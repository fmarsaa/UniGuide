import 'package:flutter/material.dart';
import '../models/recommendation.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';

class FeedbackDialog extends StatefulWidget {
  final RecommendationItem recommendation;
  final VoidCallback onFeedbackSubmitted;

  const FeedbackDialog({
    Key? key,
    required this.recommendation,
    required this.onFeedbackSubmitted,
  }) : super(key: key);

  @override
  State<FeedbackDialog> createState() => _FeedbackDialogState();
}

class _FeedbackDialogState extends State<FeedbackDialog> {
  int _rating = 5;
  final TextEditingController _commentController = TextEditingController();
  bool _isSubmitting = false;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title: Row(
        children: const [
          Icon(Icons.rate_review, color: Color(0xFF0EA5A4), size: 22),
          SizedBox(width: 8),
          Text('Recommendation Feedback', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.recommendation.programme.title,
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.textPrimary(context)),
            ),
            const SizedBox(height: 4),
            Text(
              'Model Confidence: ${(widget.recommendation.confidenceScore * 100).toStringAsFixed(1)}%',
              style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)),
            ),
            const Divider(height: 20),
            const Text(
              'How suitable is this recommendation for your academic performance and aspirations?',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 10),

            // Star Rating Row
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(5, (index) {
                final starIndex = index + 1;
                return IconButton(
                  icon: Icon(
                    starIndex <= _rating ? Icons.star : Icons.star_border,
                    color: Colors.amber.shade700,
                    size: 32,
                  ),
                  onPressed: () => setState(() => _rating = starIndex),
                );
              }),
            ),
            Center(
              child: Text(
                _getRatingLabel(_rating),
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.amber.shade800),
              ),
            ),
            const SizedBox(height: 14),

            const Text('Comments / Suggested Improvements:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            TextField(
              controller: _commentController,
              maxLines: 3,
              decoration: InputDecoration(
                hintText: 'e.g. Matches my career goal, but cluster cutoff is slightly high...',
                hintStyle: TextStyle(fontSize: 11, color: Colors.grey.shade400),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                contentPadding: const EdgeInsets.all(10),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF0EA5A4),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
          onPressed: _isSubmitting
              ? null
              : () async {
                  setState(() => _isSubmitting = true);
                  try {
                    await ApiService.submitFeedback(
                      recommendationId: widget.recommendation.programme.id,
                      rating: _rating,
                      comments: _commentController.text,
                    );
                    if (!mounted) return;
                    Navigator.pop(context);
                    widget.onFeedbackSubmitted();
                  } on ApiException catch (e) {
                    if (!mounted) return;
                    setState(() => _isSubmitting = false);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Could not submit feedback: ${e.message}'), backgroundColor: Colors.redAccent),
                    );
                  }
                },
          child: _isSubmitting
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Text('Submit to Firestore', style: TextStyle(color: Colors.white)),
        ),
      ],
    );
  }

  String _getRatingLabel(int stars) {
    switch (stars) {
      case 5:
        return '5/5 - Highly Accurate & Relevant';
      case 4:
        return '4/5 - Relevant & Helpful';
      case 3:
        return '3/5 - Neutral / Moderate Match';
      case 2:
        return '2/5 - Low Relevance';
      case 1:
        return '1/5 - Inappropriate Match';
      default:
        return '';
    }
  }
}
