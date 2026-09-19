import 'package:flutter/material.dart';
import '../models/recommendation.dart';

class ShapExplanationCard extends StatelessWidget {
  final List<ShapFeatureImpact> shapFeatures;
  final String primaryReason;

  const ShapExplanationCard({
    Key? key,
    required this.shapFeatures,
    required this.primaryReason,
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
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.auto_graph, size: 18, color: Colors.indigo.shade700),
              const SizedBox(width: 8),
              const Text(
                'SHAP Feature Importance (Explainability)',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                  color: Color(0xFF14213D),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            primaryReason,
            style: TextStyle(fontSize: 12, color: Colors.grey.shade700, height: 1.4),
          ),
          const Divider(height: 20),
          const Text(
            'Attribution to Random Forest Classification Decision:',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.grey),
          ),
          const SizedBox(height: 10),
          ...shapFeatures.map((feat) {
            final isPositive = feat.shapValue >= 0;
            final double normalizedWidth = (feat.shapValue.abs() / 0.4).clamp(0.1, 1.0);
            final color = _getCategoryColor(feat.category);

            return Padding(
              padding: const EdgeInsets.only(bottom: 10.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
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
                          Text(
                            feat.featureName,
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                      Text(
                        '${isPositive ? '+' : ''}${feat.shapValue.toStringAsFixed(2)}',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: isPositive ? Colors.blue : Colors.red.shade700,
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
                      backgroundColor: Colors.grey.shade200,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        isPositive ? const Color(0xFF0EA5A4) : Colors.red.shade400,
                      ),
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    feat.description,
                    style: TextStyle(fontSize: 10.5, color: Colors.grey.shade600),
                  ),
                ],
              ),
            );
          }).toList(),
        ],
      ),
    );
  }
}
