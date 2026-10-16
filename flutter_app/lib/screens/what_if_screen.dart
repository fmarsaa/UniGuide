import 'package:flutter/material.dart';
import '../models/kcse_grade.dart';
import '../models/recommendation.dart';
import '../models/student_profile.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';

/// "What if?": change one or more KCSE grades and see how the top three
/// programmes, and the entry check for each, would change. It asks the server for
/// a real recommendation but in preview mode, so nothing is saved and the
/// student's own results stay exactly as they were.
class WhatIfScreen extends StatefulWidget {
  final StudentProfile profile;
  final List<RecommendationItem> current;

  const WhatIfScreen({Key? key, required this.profile, required this.current})
      : super(key: key);

  @override
  State<WhatIfScreen> createState() => _WhatIfScreenState();
}

class _WhatIfScreenState extends State<WhatIfScreen> {
  late final Map<String, String> _grades;
  List<RecommendationItem>? _result;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _grades = Map<String, String>.from(widget.profile.grades);
  }

  bool _isChanged(String subject) =>
      _grades[subject] != widget.profile.grades[subject];
  bool get _anyChange => _grades.keys.any(_isChanged);

  /// Same rule as the profile screen: the average of the grade points, rounded.
  String _meanGradeOf(Map<String, String> grades) {
    if (grades.isEmpty) return widget.profile.kcseMeanGrade;
    final total = grades.values
        .fold<int>(0, (sum, g) => sum + KCSEGrade.fromString(g).points);
    final points = (total / grades.length).round().clamp(1, 12);
    return KCSEGrade.values.firstWhere((g) => g.points == points).label;
  }

  void _reset() => setState(() {
        _grades
          ..clear()
          ..addAll(widget.profile.grades);
        _result = null;
        _error = null;
      });

  Future<void> _run() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    final p = widget.profile;
    final modified = StudentProfile(
      uid: p.uid,
      fullName: p.fullName,
      indexNumber: p.indexNumber,
      kcseMeanGrade: _meanGradeOf(_grades),
      grades: Map<String, String>.from(_grades),
      interests: p.interests,
      skills: p.skills,
      strengths: p.strengths,
      aspirations: p.aspirations,
    );
    try {
      final results =
          await ApiService.getRecommendations(modified, preview: true);
      if (!mounted) return;
      setState(() {
        _result = results;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final subjects = _grades.keys.toList()..sort();
    final oldMean = widget.profile.kcseMeanGrade;
    final newMean = _meanGradeOf(_grades);

    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground(context),
      appBar: AppBar(
        title: const Text('What if?',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF14213D),
        foregroundColor: Colors.white,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'Change a grade to see how your results would change. This is only a preview - nothing is saved and your real results stay as they are.',
            style: TextStyle(
                fontSize: 12.5,
                height: 1.4,
                color: AppColors.textSecondary(context)),
          ),
          const SizedBox(height: 14),
          Container(
            decoration: BoxDecoration(
              color: AppColors.cardBackground(context),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.cardBorder(context)),
            ),
            child: Column(
              children: [
                for (int i = 0; i < subjects.length; i++) ...[
                  if (i > 0)
                    Divider(height: 1, color: AppColors.cardBorder(context)),
                  _subjectRow(subjects[i]),
                ],
              ],
            ),
          ),
          const SizedBox(height: 10),
          if (_anyChange)
            Text(
              'Mean grade: $oldMean  ->  $newMean',
              style: TextStyle(
                  fontSize: 12.5,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary(context)),
            ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: (_anyChange && !_loading) ? _run : null,
                  icon: _loading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white))
                      : const Icon(Icons.science_outlined, size: 18),
                  label: Text(_loading ? 'Checking...' : 'See what changes'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.accentTeal,
                    foregroundColor: Colors.white,
                    disabledBackgroundColor: AppColors.chipBackground(context),
                    minimumSize: const Size.fromHeight(46),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              TextButton(
                  onPressed: _anyChange ? _reset : null,
                  child: const Text('Reset')),
            ],
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!,
                style: TextStyle(fontSize: 12, color: Colors.red.shade400)),
          ],
          if (_result != null) ..._resultSection(context),
        ],
      ),
    );
  }

  Widget _subjectRow(String subject) {
    final changed = _isChanged(subject);
    return Container(
      color: changed ? AppColors.accentTeal.withOpacity(0.10) : null,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Row(
        children: [
          Expanded(
            child: Text(
              subject,
              style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary(context)),
            ),
          ),
          if (changed)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Text('was ${widget.profile.grades[subject]}',
                  style: TextStyle(
                      fontSize: 11, color: AppColors.textSecondary(context))),
            ),
          DropdownButton<String>(
            value: _grades[subject],
            underline: const SizedBox.shrink(),
            items: [
              for (final g in KCSEGrade.values)
                DropdownMenuItem(value: g.label, child: Text(g.label))
            ],
            onChanged: (value) => setState(() {
              if (value != null) _grades[subject] = value;
              _result = null;
            }),
          ),
        ],
      ),
    );
  }

  List<Widget> _resultSection(BuildContext context) {
    final results = _result!;
    final currentIds = widget.current.map((r) => r.programme.id).toList();
    final newIds = results.map((r) => r.programme.id).toList();
    final dropped =
        widget.current.where((r) => !newIds.contains(r.programme.id)).toList();
    final unchanged = results.length == currentIds.length &&
        List.generate(results.length, (i) => i)
            .every((i) => newIds[i] == currentIds[i]);

    return [
      const SizedBox(height: 22),
      Text(
        'With these grades',
        style: TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary(context)),
      ),
      const SizedBox(height: 4),
      Text(
        unchanged
            ? 'Your top three programmes would stay the same - but check the entry check on each one below.'
            : 'Your top three would change. Here is what you would see:',
        style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
      ),
      const SizedBox(height: 10),
      for (int i = 0; i < results.length; i++)
        _resultCard(context, results[i], i, currentIds),
      if (dropped.isNotEmpty) ...[
        const SizedBox(height: 4),
        Text(
          'No longer in your top three: ${dropped.map((r) => r.programme.title).join(', ')}',
          style: TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary(context),
              height: 1.4),
        ),
      ],
      const SizedBox(height: 24),
    ];
  }

  Widget _resultCard(BuildContext context, RecommendationItem item, int index,
      List<String> currentIds) {
    final before = currentIds.indexOf(item.programme.id);
    String tag;
    Color tagColor;
    if (before == -1) {
      tag = 'New in your top 3';
      tagColor = const Color(0xFF059669);
    } else if (before > index) {
      tag = 'Moved up';
      tagColor = const Color(0xFF059669);
    } else if (before < index) {
      tag = 'Moved down';
      tagColor = const Color(0xFFD97706);
    } else {
      tag = 'Same place';
      tagColor = AppColors.textSecondary(context);
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.cardBackground(context),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.cardBorder(context)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('#${item.rank}',
                  style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: AppColors.accentTeal)),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  item.programme.title,
                  style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 13.5,
                      color: AppColors.textPrimary(context)),
                ),
              ),
              const SizedBox(width: 8),
              Text(tag,
                  style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: tagColor)),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            item.eligibilityStatus,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: item.meetsMinimumRequirements
                  ? Colors.blue.shade400
                  : AppColors.textSecondary(context),
            ),
          ),
          const SizedBox(height: 2),
          Text(
            'Cutoff: ${item.programme.cutoffRangeLabel}',
            style: TextStyle(
                fontSize: 11.5, color: AppColors.textSecondary(context)),
          ),
        ],
      ),
    );
  }
}
