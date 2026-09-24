import 'package:flutter/material.dart';
import '../models/recommendation.dart';
import '../models/programme.dart';
import '../theme/app_colors.dart';
import '../widgets/shap_bars.dart';

class RecommendationsScreen extends StatelessWidget {
  final List<RecommendationItem> recommendations;
  final Function(Programme programme) onSelectProgramme;
  final Function(RecommendationItem recommendation) onOpenFeedback;
  final VoidCallback onAdjustProfile;

  const RecommendationsScreen({
    Key? key,
    required this.recommendations,
    required this.onSelectProgramme,
    required this.onOpenFeedback,
    required this.onAdjustProfile,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground(context),
      appBar: AppBar(
        title: const Text('Top 3 Degree Recommendations', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF14213D),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.tune),
            tooltip: 'Adjust Profile',
            onPressed: onAdjustProfile,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top Summary Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF14213D), Color(0xFF1E293B)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.15),
                    blurRadius: 8,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: const [
                          Icon(Icons.auto_awesome, color: Color(0xFF0EA5A4), size: 20),
                          SizedBox(width: 8),
                          Text(
                            'Random Forest Classifier',
                            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                          ),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0EA5A4).withOpacity(0.25),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: const Color(0xFF0EA5A4)),
                        ),
                        child: const Text(
                          'SHAP Grounded',
                          style: TextStyle(color: Color(0xFF2DD4BF), fontSize: 11, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Here are your 3 highest-probability degree programmes ranked by decision forest confidence and explained by SHAP value attributions.',
                    style: TextStyle(color: Color(0xFFCBD5E1), fontSize: 12, height: 1.4),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Top 3 Recommendation Cards
            ...recommendations.map((item) => _buildRecommendationCard(context, item)).toList(),

            const SizedBox(height: 20),
            // Adjust Profile Banner (Sequence Diagram Option B)
            Center(
              child: OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFF14213D),
                  side: const BorderSide(color: Color(0xFF14213D)),
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                icon: const Icon(Icons.tune),
                label: const Text('Adjust Profile to Request New Recommendation'),
                onPressed: onAdjustProfile,
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildRecommendationCard(BuildContext context, RecommendationItem item) {
    final rankBadgeColor = item.rank == 1
        ? const Color(0xFFD97706) // Gold
        : item.rank == 2
            ? const Color(0xFF475569) // Silver
            : const Color(0xFF92400E); // Bronze

    final confidencePercent = (item.confidenceScore * 100).toStringAsFixed(1);

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: AppColors.cardBackground(context),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: item.rank == 1 ? const Color(0xFF0EA5A4).withOpacity(0.5) : AppColors.cardBorder(context),
          width: item.rank == 1 ? 2 : 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: Rank + Confidence
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: item.rank == 1 ? const Color(0xFFF0FDFA) : AppColors.chipBackground(context),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(15)),
              border: Border(bottom: BorderSide(color: AppColors.cardBorder(context))),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      width: 26,
                      height: 26,
                      decoration: BoxDecoration(
                        color: rankBadgeColor,
                        shape: BoxShape.circle,
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        '#${item.rank}',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      item.programme.code,
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.grey),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0EA5A4),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '$confidencePercent% Match',
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11),
                  ),
                ),
              ],
            ),
          ),

          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.programme.title,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary(context),
                    height: 1.3,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  item.programme.faculty,
                  style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
                ),
                const SizedBox(height: 12),

                // KUCCPS Cutoff Status Pill
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.blue.shade200),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.verified, size: 16, color: Colors.blue.shade700),
                          const SizedBox(width: 6),
                          Text(
                            item.eligibilityStatus,
                            style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.blue.shade900),
                          ),
                        ],
                      ),
                      Text(
                        'Cutoff: ${item.programme.averageCutoff} pts',
                        style: TextStyle(fontSize: 11, color: Colors.blue.shade800),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // SHAP Explanation Component
                ShapExplanationCard(
                  shapFeatures: item.shapExplanations,
                  primaryReason: item.primaryReason,
                ),
                const SizedBox(height: 16),

                // Actions: View Details + Rating Dialog
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF14213D),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                        icon: const Icon(Icons.menu_book, size: 16, color: Colors.white),
                        label: const Text('Programme Details', style: TextStyle(fontSize: 12, color: Colors.white, fontWeight: FontWeight.w600)),
                        onPressed: () => onSelectProgramme(item.programme),
                      ),
                    ),
                    const SizedBox(width: 8),
                    IconButton(
                      icon: const Icon(Icons.star_border, color: Color(0xFFD97706)),
                      tooltip: 'Rate Recommendation Relevance',
                      onPressed: () => onOpenFeedback(item),
                      style: IconButton.styleFrom(
                        backgroundColor: Colors.amber.shade50,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                          side: BorderSide(color: Colors.amber.shade300),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
