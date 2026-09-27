import 'dart:convert';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:http/http.dart' as http;
import '../models/student_profile.dart';
import '../models/recommendation.dart';
import '../models/programme.dart';

/// Thrown whenever a backend call fails. Screens must handle this explicitly
/// (retry banner, snackbar, etc.) instead of the app silently pretending the
/// request succeeded.
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class ApiService {
  // 10.0.2.2 is the Android emulator's alias for the host machine's localhost.
  // Override with --dart-define=API_BASE_URL=http://<lan-ip>:8000 for a real device.
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static Future<Map<String, String>> _authHeaders() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      throw ApiException('You must be signed in to do this.');
    }
    final token = await user.getIdToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  static ApiException _errorFor(http.Response response) {
    String detail = response.body;
    try {
      final decoded = jsonDecode(response.body);
      if (decoded is Map && decoded['detail'] != null) {
        detail = decoded['detail'].toString();
      }
    } catch (_) {
      // Body wasn't JSON; use it as-is.
    }
    return ApiException(detail, statusCode: response.statusCode);
  }

  /// Runs [attempt] with automatic retry for transient network failures
  /// (connection refused, DNS hiccup, brief server restart) - the exact
  /// failure mode behind "Could not reach the UniGuide server" when the
  /// backend was simply mid-restart for a moment. A real server response
  /// (4xx/5xx, surfaced as ApiException by _errorFor) is NOT retried -
  /// retrying a 403 or 404 can't fix it, so that fails immediately instead
  /// of making the user wait through retries for nothing.
  static Future<T> _withRetry<T>(String failureMessage, Future<T> Function() attempt, {int retries = 2}) async {
    for (int attemptNumber = 0; ; attemptNumber++) {
      try {
        return await attempt();
      } on ApiException {
        rethrow;
      } catch (e) {
        if (attemptNumber >= retries) {
          throw ApiException('$failureMessage: $e');
        }
        await Future.delayed(Duration(milliseconds: 500 * (attemptNumber + 1)));
      }
    }
  }

  /// Public health/metrics check - used by the admin dashboard to show the
  /// model's real measured accuracy instead of an invented number.
  static Future<Map<String, dynamic>> fetchHealth() {
    return _withRetry('Could not reach the UniGuide server', () async {
      final response = await http.get(Uri.parse('$baseUrl/api/health')).timeout(const Duration(seconds: 10));
      if (response.statusCode != 200) throw _errorFor(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    });
  }

  /// Calls the backend right after Firebase sign-in to resolve the caller's
  /// role (student/administrator) and any saved profile.
  static Future<Map<String, dynamic>> whoami() {
    return _withRetry('Could not reach the UniGuide server', () async {
      final headers = await _authHeaders();
      final response = await http
          .post(Uri.parse('$baseUrl/api/auth/whoami'), headers: headers)
          .timeout(const Duration(seconds: 10));
      if (response.statusCode != 200) throw _errorFor(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    });
  }

  /// Requests Top 3 Random Forest recommendations with real SHAP explanations.
  static Future<List<RecommendationItem>> getRecommendations(StudentProfile profile) {
    return _withRetry('Could not reach the UniGuide recommendation service', () async {
      final headers = await _authHeaders();
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/recommend'),
            headers: headers,
            body: jsonEncode(profile.toJson()),
          )
          .timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) throw _errorFor(response);

      final List<dynamic> data = jsonDecode(response.body);
      return data.map((json) => RecommendationItem.fromJson(json)).toList();
    });
  }

  /// Submits student rating and feedback for a recommendation.
  static Future<void> submitFeedback({
    required String recommendationId,
    required int rating,
    required String comments,
  }) {
    return _withRetry('Could not submit feedback', () async {
      final headers = await _authHeaders();
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/feedback'),
            headers: headers,
            body: jsonEncode({
              'recommendation_id': recommendationId,
              'rating': rating,
              'comments': comments,
              'timestamp': DateTime.now().toIso8601String(),
            }),
          )
          .timeout(const Duration(seconds: 10));
      if (response.statusCode != 200) throw _errorFor(response);
    });
  }

  /// Fetches the full programme catalog (student directory + admin dashboard).
  static Future<List<Programme>> fetchProgrammes() {
    return _withRetry('Could not load the programme catalog', () async {
      final response = await http
          .get(Uri.parse('$baseUrl/api/programmes'))
          .timeout(const Duration(seconds: 10));
      if (response.statusCode != 200) throw _errorFor(response);
      final List<dynamic> data = jsonDecode(response.body);
      return data.map((json) => Programme.fromJson(json)).toList();
    });
  }

  /// Admin-only: fetches the real system audit trail (cutoff edits, etc.).
  static Future<List<Map<String, dynamic>>> fetchAuditLogs() {
    return _withRetry('Could not load audit logs', () async {
      final headers = await _authHeaders();
      final response = await http
          .get(Uri.parse('$baseUrl/api/admin/audit-logs'), headers: headers)
          .timeout(const Duration(seconds: 10));
      if (response.statusCode != 200) throw _errorFor(response);
      final List<dynamic> data = jsonDecode(response.body);
      return data.cast<Map<String, dynamic>>();
    });
  }

  /// Admin-only: fetches real student feedback/ratings submitted across all
  /// students (students/{uid}/feedback subcollections), newest first.
  static Future<List<Map<String, dynamic>>> fetchStudentFeedback() {
    return _withRetry('Could not load student feedback', () async {
      final headers = await _authHeaders();
      final response = await http
          .get(Uri.parse('$baseUrl/api/admin/feedback'), headers: headers)
          .timeout(const Duration(seconds: 10));
      if (response.statusCode != 200) throw _errorFor(response);
      final List<dynamic> data = jsonDecode(response.body);
      return data.cast<Map<String, dynamic>>();
    });
  }

  /// Admin-only: persists a new KUCCPS cutoff for a programme.
  static Future<Programme> updateProgrammeCutoff(String programmeId, double newCutoff) {
    return updateProgramme(programmeId, averageCutoff: newCutoff);
  }

  /// Admin-only: persists any combination of programme fields. Only the
  /// fields you pass are changed; everything else on the programme is left
  /// untouched (see backend ProgrammeUpdatePayload).
  static Future<Programme> updateProgramme(
    String programmeId, {
    double? averageCutoff,
    String? minMeanGrade,
    String? description,
  }) {
    return _withRetry('Could not update the programme', () async {
      final headers = await _authHeaders();
      final body = <String, dynamic>{};
      if (averageCutoff != null) body['averageCutoff'] = averageCutoff;
      if (minMeanGrade != null) body['minMeanGrade'] = minMeanGrade;
      if (description != null) body['description'] = description;

      final response = await http
          .put(
            Uri.parse('$baseUrl/api/admin/programmes/$programmeId'),
            headers: headers,
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 10));
      if (response.statusCode != 200) throw _errorFor(response);
      return Programme.fromJson(jsonDecode(response.body));
    });
  }

  /// Admin-only: re-fetches KUCCPS's own cutoff document server-side and
  /// flags any offering-university entry that may no longer be real (see
  /// backend/catalogue_freshness.py). Longer timeout than other calls -
  /// this downloads and parses a PDF, not a quick Firestore read.
  static Future<Map<String, dynamic>> runCatalogueFreshnessCheck() {
    return _withRetry('Could not run the catalogue freshness check', () async {
      final headers = await _authHeaders();
      final response = await http
          .post(Uri.parse('$baseUrl/api/admin/catalogue-freshness/check'), headers: headers)
          .timeout(const Duration(seconds: 60));
      if (response.statusCode != 200) throw _errorFor(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    });
  }

  /// Admin-only: lists currently open (undismissed) catalogue freshness flags.
  static Future<List<Map<String, dynamic>>> fetchCatalogueFreshnessFlags() {
    return _withRetry('Could not load catalogue freshness flags', () async {
      final headers = await _authHeaders();
      final response = await http
          .get(Uri.parse('$baseUrl/api/admin/catalogue-freshness/flags'), headers: headers)
          .timeout(const Duration(seconds: 10));
      if (response.statusCode != 200) throw _errorFor(response);
      final List<dynamic> data = jsonDecode(response.body);
      return data.cast<Map<String, dynamic>>();
    });
  }

  /// Admin-only: dismisses a catalogue freshness flag after manual review.
  static Future<void> dismissCatalogueFreshnessFlag(String flagId) {
    return _withRetry('Could not dismiss the flag', () async {
      final headers = await _authHeaders();
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/admin/catalogue-freshness/flags/$flagId/dismiss'),
            headers: headers,
          )
          .timeout(const Duration(seconds: 10));
      if (response.statusCode != 200) throw _errorFor(response);
    });
  }
}
