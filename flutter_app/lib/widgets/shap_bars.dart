import 'package:flutter/material.dart';
import '../models/recommendation.dart';
import '../theme/app_colors.dart';

class ShapExplanationCard extends StatelessWidget {
  final List<ShapFeatureImpact> shapFeatures;
  final String primaryReason;

  /// Plain sentences built by the backend from the factors that really pushed
  /// this result up. Shown first; the technical bars sit behind a "details" tap.
  final List<String> plainReasons;

  const ShapExplanationCard({
    Key? key,
    required this.shapFeatures,
    required this.primaryReason,
    this.plainReasons = const [],
  }) : super(key: key);

  Color _getCategoryColor(String category) {
    switch (category) {
      case 'Academic':
        return Colors.blue.shade700;
      case 'Interests':
        return Colors.purple.shade700;
      case 'Skills':
        return Colors.teal.shade700;
      case 'Strengths':
        return Colors.amber.shade800;
      case 'Aspirations':
        return Colors.indigo.shade700;
      default:
        return Colors.grey.shade700;
    }
  }

  @override
  Widget build(BuildContext context) {
    // Bars are scaled relative to the strongest feature in *this* card
    // (rather than a fixed constant) so relative importance stays legible
    // regardless of the absolute SHAP value magnitudes a given prediction
    // happens to produce.
    final double maxAbsShap = shapFeatures.isEmpty
        ? 1.0
        : shapFeatures
            .map((f) => f.shapValue.abs())
            .reduce((a, b) => a > b ? a : b)
            .clamp(0.0001, double.infinity);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.chipBackground(context),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.cardBorder(context)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.auto_graph, size: 18, color: Colors.indigo.shade700),
              const SizedBox(width: 8),
              Text(
                'Why this was recommended',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                  color: AppColors.textPrimary(context),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          if (plainReasons.isNotEmpty)
            for (final reason in plainReasons)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.only(top: 5, right: 8),
                      child: Icon(Icons.circle,
                          size: 6, color: Colors.indigo.shade400),
                    ),
                    Expanded(
                      child: Text(
                        reason,
                        style: TextStyle(
                            fontSize: 12.5,
                            height: 1.4,
                            color: AppColors.textPrimary(context)),
                      ),
                    ),
                  ],
                ),
              )
          else
            Text(
              primaryReason,
              style: TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary(context),
                  height: 1.4),
            ),
          // ExpansionTile paints on the nearest Material, so give it its own transparent
          // one - otherwise the card's coloured background hides it and Flutter flags it.
          Material(
            color: Colors.transparent,
            child: Theme(
              data:
                  Theme.of(context).copyWith(dividerColor: Colors.transparent),
              child: ExpansionTile(
                tilePadding: EdgeInsets.zero,
                childrenPadding: EdgeInsets.zero,
                dense: true,
                title: Text(
                  'See the detailed breakdown',
                  style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Colors.indigo.shade400),
                ),
                children: [
                  Text(
                    'What influenced this result:',
                    style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textSecondary(context)),
                  ),
                  const SizedBox(height: 10),
                  ...shapFeatures.map((feat) {
                    final isPositive = feat.shapValue >= 0;
                    final double normalizedWidth =
                        (feat.shapValue.abs() / maxAbsShap).clamp(0.05, 1.0);
                    final color = _getCategoryColor(feat.category);

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 10.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Expanded(
                                child: Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: color.withOpacity(0.1),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: Text(
                                        feat.category,
                                        style: TextStyle(
                                          fontSize: 9,
                                          fontWeight: FontWeight.bold,
                                          color: color,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 6),
                                    Flexible(
                                      child: Text(
                                        feat.featureName,
                                        maxLines: 2,
                                        overflow: TextOverflow.ellipsis,
                                        style: TextStyle(
                                          fontSize: 12,
                                          fontWeight: FontWeight.w600,
                                          color: AppColors.textPrimary(context),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                '${isPositive ? '+' : ''}${feat.shapValue.toStringAsFixed(2)}',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: isPositive
                                      ? Colors.blue
                                      : Colors.red.shade700,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: normalizedWidth,
                              minHeight: 6,
                              backgroundColor: AppColors.cardBorder(context),
                              valueColor: AlwaysStoppedAnimation<Color>(
                                isPositive
                                    ? const Color(0xFF0EA5A4)
                                    : Colors.red.shade400,
                              ),
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            feat.description,
                            style: TextStyle(
                                fontSize: 10.5,
                                color: AppColors.textSecondary(context)),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
