import 'dart:math';
import '../models/kcse_grade.dart';

class KuccpsCalculator {
  /// Converts letter grade to KUCCPS points (1 to 12)
  static int gradeToPoints(String grade) {
    return KCSEGrade.fromString(grade).points;
  }

  /// Calculates KUCCPS Cluster Weighted Points (CWP)
  /// CWP = sqrt((r / m) * (t / 48)) * 48
  /// r: Student's cluster raw points across 4 required subjects (max 48)
  /// m: Maximum possible cluster raw points (default 48)
  /// aggregatePoints: Student's best 7 subjects sum (max 84)
  static double calculateClusterScore({
    required int rawClusterPoints,
    required int aggregatePoints,
    int maxClusterPoints = 48,
  }) {
    if (rawClusterPoints <= 0 || aggregatePoints <= 0) return 0.0;

    final double t = (aggregatePoints / 84.0) * 48.0;
    final double r = rawClusterPoints.toDouble();
    final double m = maxClusterPoints.toDouble();

    final double cwp = sqrt((r / m) * (t / 48.0)) * 48.0;
    return double.parse(cwp.toStringAsFixed(3));
  }

  /// Evaluates qualification status relative to institutional cutoff
  static String getEligibilityLabel(double studentScore, double cutoff) {
    final diff = studentScore - cutoff;
    if (diff >= 0.0) {
      return 'Likely Admission';
    } else if (diff >= -1.5) {
      return 'Competitive / Borderline';
    } else {
      return 'Reach / High Risk';
    }
  }
}
