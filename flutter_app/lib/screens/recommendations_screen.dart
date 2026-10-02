import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/recommendation.dart';
import '../models/programme.dart';
import '../theme/app_colors.dart';
import '../widgets/shap_bars.dart';

class RecommendationsScreen extends StatelessWidget {
  final List<RecommendationItem> recommendations;
  final Function(Programme programme) onSelectProgramme;
  final Function(RecommendationItem recommendation) onOpenFeedback;
  final VoidCallback onAdjustProfile;
  final String? studentPrimaryInterest;

  const RecommendationsScreen({
    Key? key,
    required this.recommendations,
    required this.onSelectProgramme,
    required this.onOpenFeedback,
    required this.onAdjustProfile,
    this.studentPrimaryInterest,
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

            // TVET/diploma pathway notice - shown only when NONE of the 3
            // results are genuine eligible matches (every real KUCCPS
            // degree programme's minimum subject requirements were failed).
            // Deliberately does not name a specific diploma/certificate
            // institution or programme - we have no verified TVET catalogue
            // (see the degree catalogue's own verification effort), so
            // making up a specific suggestion here would repeat exactly the
            // "guesswork data" problem already fixed for degrees. Instead
            // this points the student to KUCCPS's own real placement
            // portal and reflects their own stated interest back at them.
            if (recommendations.isNotEmpty && recommendations.every((r) => !r.meetsMinimumRequirements))
              _buildTvetPathwayNotice(context),

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
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
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
                    const SizedBox(width: 2),
                    InkWell(
                      borderRadius: BorderRadius.circular(20),
                      onTap: () => _showConfidenceExplanation(context),
                      child: Padding(
                        padding: const EdgeInsets.all(4.0),
                        child: Icon(Icons.info_outline, size: 15, color: Colors.grey.shade500),
                      ),
                    ),
                  ],
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

                // A student whose KCSE subject grades fail this programme's
                // real KUCCPS minimum requirements outright still gets a
                // result (so the list is never empty), but it must be
                // flagged unmistakably as NOT a genuine match rather than
                // shown with the same reassuring blue pill as the others.
                if (!item.meetsMinimumRequirements) ...[
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.red.shade200),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.error_outline, size: 16, color: Colors.red.shade700),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            'Does not meet minimum subject requirements — shown as a fallback suggestion, not a qualifying match.',
                            style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.red.shade900),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 10),
                ],

                // KUCCPS Cutoff Status Pill
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: item.meetsMinimumRequirements ? Colors.blue.shade50 : Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: item.meetsMinimumRequirements ? Colors.blue.shade200 : Colors.grey.shade300),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Icon(
                            item.meetsMinimumRequirements ? Icons.verified : Icons.block,
                            size: 16,
                            color: item.meetsMinimumRequirements ? Colors.blue.shade700 : Colors.grey.shade700,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            item.eligibilityStatus,
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: item.meetsMinimumRequirements ? Colors.blue.shade900 : Colors.grey.shade800,
                            ),
                          ),
                        ],
                      ),
                      Text(
                        'Cutoff: ${item.programme.averageCutoff} pts',
                        style: TextStyle(
                          fontSize: 11,
                          color: item.meetsMinimumRequirements ? Colors.blue.shade800 : Colors.grey.shade700,
                        ),
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

  Widget _buildTvetPathwayNotice(BuildContext context) {
    final interestNote = studentPrimaryInterest != null && studentPrimaryInterest!.isNotEmpty
        ? ' Since you told us you\'re interested in "$studentPrimaryInterest", that\'s a good starting point for what to search for.'
        : '';
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.amber.shade50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.amber.shade300),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.school_outlined, color: Colors.amber.shade800, size: 20),
              const SizedBox(width: 8),
              Text(
                "You don't currently qualify for any of our degree programmes",
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.amber.shade900),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Based on the grades you entered, none of these 3 suggestions are '
            'programmes you meet the real KUCCPS minimum subject requirements '
            'for - they\'re shown only as the closest available options, not a '
            'genuine match (look for the red warning on each card below).'
            '$interestNote\n\n'
            'Certificate and diploma-level courses have lower entry requirements '
            'and are also placed through KUCCPS. We don\'t yet have a verified '
            'catalogue of those to recommend specific ones honestly, so please '
            'check KUCCPS\'s own portal directly.',
            style: TextStyle(fontSize: 12, height: 1.4, color: Colors.amber.shade900),
          ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            onPressed: () => launchUrl(Uri.parse('https://www.kuccps.net'), mode: LaunchMode.externalApplication),
            icon: const Icon(Icons.open_in_new, size: 15),
            label: const Text('Visit KUCCPS', style: TextStyle(fontSize: 12)),
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.amber.shade900,
              side: BorderSide(color: Colors.amber.shade400),
            ),
          ),
        ],
      ),
    );
  }

  void _showConfidenceExplanation(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('What does "Match %" mean?'),
        content: const Text(
          'This percentage shows how strongly your academic profile, interests, '
          'skills and aspirations match patterns the model learned from thousands '
          'of similar student profiles - it is a measure of fit, not a guarantee.\n\n'
          'It does NOT predict your chance of being admitted. Real admission also '
          'depends on that year\'s national cutoff competition, which changes every '
          'intake based on how many students apply and qualify. Always check the '
          "programme's KUCCPS cutoff points shown below alongside this score.",
          style: TextStyle(fontSize: 13, height: 1.4),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }
}
