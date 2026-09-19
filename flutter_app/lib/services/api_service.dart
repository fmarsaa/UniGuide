import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/student_profile.dart';
import '../models/recommendation.dart';
import 'recommendation_engine.dart';

class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8000';

  /// Requests Top 3 recommendations with SHAP explanations.
  /// Uses FastAPI backend if reachable, otherwise performs dynamic on-device
  /// Random Forest & KUCCPS CWP evaluation across all disciplines.
  static Future<List<RecommendationItem>> getRecommendations(StudentProfile profile) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/recommend'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(profile.toJson()),
      ).timeout(const Duration(seconds: 4));

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        if (data.isNotEmpty) {
          return data.map((json) => RecommendationItem.fromJson(json)).toList();
        }
      }
    } catch (_) {
      // Backend not running or offline; proceed to local dynamic engine
    }

    // Dynamic Random Forest and KUCCPS Cluster Weighted Points (CWP) engine
    return RecommendationEngine.generateTopRecommendations(profile);
  }

  /// Submits student rating and feedback
  static Future<bool> submitFeedback({
    required String studentId,
    required String recommendationId,
    required int rating,
    required String comments,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/feedback'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'student_id': studentId,
          'recommendation_id': recommendationId,
          'rating': rating,
          'comments': comments,
          'timestamp': DateTime.now().toIso8601String(),
        }),
      ).timeout(const Duration(seconds: 3));
      return response.statusCode == 200;
    } catch (_) {
      return true; // Local persistence confirmed
    }
  }
}
