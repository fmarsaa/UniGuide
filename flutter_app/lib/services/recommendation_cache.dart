import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/recommendation.dart';

/// Persists the student's last successful /api/recommend response locally
/// so that a later request failing purely due to connectivity (patchy
/// network is a real, common scenario in Kenya) still has something useful
/// to show instead of just an error banner. Deliberately NOT used to
/// bypass a genuine server error (4xx/5xx) - callers should only fall back
/// to the cache for connection-type failures, same distinction
/// ApiService._withRetry already draws.
class RecommendationCache {
  static const _dataKey = 'cached_recommendations_v1';
  static const _timestampKey = 'cached_recommendations_timestamp_v1';

  static Future<void> save(List<RecommendationItem> recommendations) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final encoded = jsonEncode(recommendations.map((r) => r.toJson()).toList());
      await prefs.setString(_dataKey, encoded);
      await prefs.setString(_timestampKey, DateTime.now().toIso8601String());
    } catch (_) {
      // Caching is a nice-to-have, not a feature a failed write should
      // ever surface to the student as an error.
    }
  }

  /// Returns null if nothing is cached, or if the cached data can't be
  /// parsed (e.g. after a model shape change) rather than throwing -
  /// callers should treat that exactly like "no cache available".
  static Future<(List<RecommendationItem>, DateTime)?> load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_dataKey);
      final tsRaw = prefs.getString(_timestampKey);
      if (raw == null || tsRaw == null) return null;
      final decoded = jsonDecode(raw) as List;
      final items = decoded.map((j) => RecommendationItem.fromJson(j as Map<String, dynamic>)).toList();
      return (items, DateTime.parse(tsRaw));
    } catch (_) {
      return null;
    }
  }
}
