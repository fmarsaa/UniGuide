import 'package:flutter/material.dart';

import '../models/student_profile.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';

typedef CareerNoteLoader = Future<List<Map<String, dynamic>>> Function(StudentProfile profile);

/// Under the results: for a career the student named, which programmes are not shown because a subject
/// grade is short, and which grade it is. Shows nothing when no programme is being held back.
class CareerNoteCard extends StatefulWidget {
  final StudentProfile profile;
  final CareerNoteLoader? loader;

  const CareerNoteCard({Key? key, required this.profile, this.loader}) : super(key: key);

  @override
  State<CareerNoteCard> createState() => _CareerNoteCardState();
}

class _CareerNoteCardState extends State<CareerNoteCard> {
  late final Future<List<Map<String, dynamic>>> _notes =
      (widget.loader ?? ApiService.fetchCareerNote)(widget.profile);

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: _notes,
      builder: (context, snapshot) {
        final notes = snapshot.data ?? const <Map<String, dynamic>>[];
        if (notes.isEmpty) return const SizedBox.shrink();
        return Container(
          width: double.infinity,
          margin: const EdgeInsets.only(bottom: 20),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.cardBackground(context),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.cardBorder(context)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.info_outline, size: 18, color: Color(0xFFD97706)),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'About the career you picked',
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context)),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                'These programmes are not in your results because a subject grade is below what the course asks for.',
                style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context), height: 1.4),
              ),
              const SizedBox(height: 10),
              for (final note in notes) ...[
                Text(
                  note['programme'].toString(),
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary(context)),
                ),
                for (final reason in (note['reasons'] as List))
                  Padding(
                    padding: const EdgeInsets.only(left: 8, top: 2),
                    child: Text('- $reason', style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context), height: 1.4)),
                  ),
                const SizedBox(height: 8),
              ],
            ],
          ),
        );
      },
    );
  }
}
