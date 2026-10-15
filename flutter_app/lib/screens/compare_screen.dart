import 'package:flutter/material.dart';
import '../models/programme.dart';
import '../theme/app_colors.dart';

/// Side-by-side comparison of two or three saved programmes. Every value comes
/// straight from the programme records - nothing is calculated or estimated here.
class CompareScreen extends StatelessWidget {
  final List<Programme> programmes;

  const CompareScreen({Key? key, required this.programmes}) : super(key: key);

  static const double _labelWidth = 118;
  static const double _columnWidth = 176;

  @override
  Widget build(BuildContext context) {
    final rows = <_Row>[
      _Row('Code', (p) => p.code),
      _Row('Faculty', (p) => p.faculty),
      _Row('Duration', (p) => '${p.durationYears} years'),
      _Row('Minimum mean grade', (p) => p.minMeanGrade),
      _Row('Cutoff points (latest)', (p) => p.cutoffRangeLabel),
      _Row('Minimum subject grades', (p) {
        if (p.minimumSubjectRequirements.isEmpty) return 'None listed';
        return p.minimumSubjectRequirements.entries.map((e) => '${e.key}: ${e.value}').join('\n');
      }),
      _Row('Cluster subjects', (p) => p.clusterSubjects.join(', ')),
      _Row('Universities and cutoffs', (p) {
        if (p.offeringUniversities.isEmpty) return 'None listed';
        return p.offeringUniversities
            .map((u) => u.latestCutoff > 0 ? '${u.universityName} (${u.latestCutoff.toStringAsFixed(1)})' : u.universityName)
            .join('\n');
      }),
      _Row('Example careers', (p) => p.careerOpportunities.take(3).join(', ')),
    ];

    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground(context),
      appBar: AppBar(
        title: const Text('Compare programmes', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF14213D),
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(width: _labelWidth),
                  for (final p in programmes)
                    SizedBox(
                      width: _columnWidth,
                      child: Padding(
                        padding: const EdgeInsets.only(right: 10, bottom: 10),
                        child: Text(
                          p.title,
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.textPrimary(context)),
                        ),
                      ),
                    ),
                ],
              ),
              for (final row in rows)
                Container(
                  decoration: BoxDecoration(border: Border(top: BorderSide(color: AppColors.cardBorder(context)))),
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SizedBox(
                        width: _labelWidth,
                        child: Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: Text(
                            row.label,
                            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.textSecondary(context)),
                          ),
                        ),
                      ),
                      for (final p in programmes)
                        SizedBox(
                          width: _columnWidth,
                          child: Padding(
                            padding: const EdgeInsets.only(right: 10),
                            child: Text(
                              row.value(p),
                              style: TextStyle(fontSize: 12, height: 1.4, color: AppColors.textPrimary(context)),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Row {
  final String label;
  final String Function(Programme) value;
  const _Row(this.label, this.value);
}
