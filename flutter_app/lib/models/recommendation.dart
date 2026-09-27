import 'programme.dart';

class ShapFeatureImpact {
  final String featureName;
  final String category; // 'Academic', 'Interests', 'Skills', 'Strengths', 'Aspirations'
  final double shapValue; // e.g. +0.32 or -0.08
  final String description;

  ShapFeatureImpact({
    required this.featureName,
    required this.category,
    required this.shapValue,
    required this.description,
  });

  factory ShapFeatureImpact.fromJson(Map<String, dynamic> json) {
    return ShapFeatureImpact(
      featureName: json['featureName'] ?? '',
      category: json['category'] ?? 'Academic',
      shapValue: (json['shapValue'] as num?)?.toDouble() ?? 0.0,
      description: json['description'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
    'featureName': featureName,
    'category': category,
    'shapValue': shapValue,
    'description': description,
  };
}

class RecommendationItem {
  final int rank; // 1, 2, or 3
  final Programme programme;
  final double confidenceScore; // 0.0 to 1.0 (e.g. 0.942 = 94.2%)
  final double studentClusterScore;
  final double cutoffDiff; // studentScore - programme.averageCutoff
  final String eligibilityStatus; // 'Likely Admission', 'Competitive', etc.
  // False means the student's KCSE subject grades fail this programme's real
  // KUCCPS minimum requirements outright - the backend still returns it (as
  // a fallback so the list isn't empty) but it is NOT a genuine match, and
  // the UI must say so rather than presenting it like the others.
  final bool meetsMinimumRequirements;
  final List<ShapFeatureImpact> shapExplanations;
  final String primaryReason;

  RecommendationItem({
    required this.rank,
    required this.programme,
    required this.confidenceScore,
    required this.studentClusterScore,
    required this.cutoffDiff,
    required this.eligibilityStatus,
    required this.meetsMinimumRequirements,
    required this.shapExplanations,
    required this.primaryReason,
  });

  factory RecommendationItem.fromJson(Map<String, dynamic> json) {
    return RecommendationItem(
      rank: json['rank'] ?? 1,
      programme: Programme.fromJson(json['programme'] ?? {}),
      confidenceScore: (json['confidenceScore'] as num?)?.toDouble() ?? 0.0,
      studentClusterScore: (json['studentClusterScore'] as num?)?.toDouble() ?? 0.0,
      cutoffDiff: (json['cutoffDiff'] as num?)?.toDouble() ?? 0.0,
      eligibilityStatus: json['eligibilityStatus'] ?? 'Likely Admission',
      meetsMinimumRequirements: json['meetsMinimumRequirements'] ?? true,
      shapExplanations: (json['shapExplanations'] as List? ?? [])
          .map((s) => ShapFeatureImpact.fromJson(s))
          .toList(),
      primaryReason: json['primaryReason'] ?? '',
    );
  }
}
