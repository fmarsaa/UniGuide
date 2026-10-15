import 'package:flutter/material.dart';
import '../models/kcse_grade.dart';
import '../models/student_profile.dart';
import '../models/profile_option_groups.dart';
import '../theme/app_colors.dart';
import '../widgets/grouped_option_picker.dart';

class ProfileSetupScreen extends StatefulWidget {
  final StudentProfile initialProfile;
  final Function(StudentProfile updatedProfile) onGenerateRecommendations;

  const ProfileSetupScreen({
    Key? key,
    required this.initialProfile,
    required this.onGenerateRecommendations,
  }) : super(key: key);

  @override
  State<ProfileSetupScreen> createState() => _ProfileSetupScreenState();
}

class _ProfileSetupScreenState extends State<ProfileSetupScreen> {
  // The subjects every candidate must give a grade for - kept in sync with
  // backend/kuccps.py COMPULSORY_SUBJECTS. Biology is optional (a student
  // may not have sat it), so it is in the optional list below.
  static const List<String> _compulsorySubjects = ['Mathematics', 'English', 'Kiswahili', 'Chemistry'];

  // Full KNEC optional subject list - kept in sync with backend/kuccps.py
  // FULL_OPTIONAL_SUBJECTS. Real candidates sit 7-9 subjects total: these 4
  // compulsory plus 3-5 chosen from this list, which varies school to school.
  static const List<String> _fullOptionalSubjects = [
    'Biology',
    'Physics',
    'History & Government',
    'Geography',
    'Christian Religious Education (CRE)',
    'Islamic Religious Education (IRE)',
    'Business Studies',
    'Agriculture',
    'Computer Studies',
    'French',
    'German',
    'Home Science',
    'Art & Design',
    'Music',
    'Building Construction',
    'Woodwork',
    'Metalwork',
    'Electricity',
    'Power Mechanics',
    'Aviation Technology',
  ];

  final List<String> _allGrades = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'E'];

  int _totalSubjectCount = 7; // 7, 8, or 9 - chosen by the student first.
  late Map<String, String?> _compulsoryGrades;
  late List<String?> _optionalSubjectChoice;
  late List<String?> _optionalGrade;

  late List<String> _selectedInterests;
  late List<String> _selectedSkills;
  late List<String> _selectedStrengths;
  late List<String> _selectedAspirations;

  int _step = 0;
  bool _showValidationErrors = false;

  // Kept in exact sync with backend/synthetic_data_generator.py's
  // INTERESTS_POOL/SKILLS_POOL/STRENGTHS_POOL/ASPIRATIONS_POOL - the trained
  // Random Forest only knows these exact option strings as features.
  final List<String> _availableInterests = [
    'Healthcare & Clinical Medicine',
    'Patient Care & Nursing',
    'Pharmaceutical Sciences',
    'Software Development & Coding',
    'Artificial Intelligence & Machine Learning',
    'Data Analytics & Statistics',
    'Cybersecurity & Network Defense',
    'Civil Infrastructure & Structural Engineering',
    'Electrical & Electronic Systems',
    'Robotics, Mechatronics & Automation',
    'Corporate Law & Constitutional Advocacy',
    'Financial Markets & Investment Banking',
    'Actuarial Modeling & Risk Analysis',
    'Agribusiness & Food Sustainability',
    'Dental & Oral Health Care',
    'Veterinary & Animal Health Care',
    'Food Science & Nutrition',
    'Mechanical Systems & Manufacturing',
    'Architecture & Building Design',
    'Mathematical Research & Data Science',
    'Economic Policy & Market Analysis',
    'Journalism & Media Production',
    'Business Systems & Enterprise Technology',
    // 53-class catalogue expansion additions - kept in exact sync with
    // backend/synthetic_data_generator.py's INTERESTS_POOL.
    'Public Health & Epidemiology',
    'Clinical Laboratory & Diagnostic Sciences',
    'Physical Rehabilitation & Therapy',
    'Environmental Conservation & Sustainability',
    'Chemical & Materials Sciences',
    'Physics & Applied Sciences Research',
    'Food Production & Agro-Processing',
    'Social Research & Community Development',
    'Counseling & Mental Health Support',
    'Teaching & Curriculum Development',
    'Tourism & Destination Management',
    'Hospitality & Guest Services',
    'Human Resource & Organizational Development',
    'International Trade & Global Business',
    'Procurement & Supply Chain Management',
    'Urban Planning & Land Use',
    'Geospatial Mapping & Remote Sensing',
    'Political & Governance Studies',
    'Criminal Justice & Security Studies',
    'General Business Administration & Strategy',
  ];

  final List<String> _availableSkills = [
    'Clinical Diagnostics & Health Care',
    'Python & Software Programming',
    'Mathematical & Quantitative Analysis',
    'Scientific Laboratory Research',
    'Problem Solving & Analytical Logic',
    'Critical Thinking & Persuasive Debate',
    'CAD Modeling & Spatial Engineering',
    'Financial Modeling & Accounting',
    'Attention to Detail',
    'Team Collaboration & Leadership',
    'Agricultural & Environmental Science',
    'News Writing & Media Research',
    'Cost Estimation & Construction Economics',
    // 53-class catalogue expansion additions - kept in exact sync with
    // backend/synthetic_data_generator.py's SKILLS_POOL.
    'Chemical Analysis & Process Optimization',
    'Microbial Culturing & Laboratory Research',
    'Statistical Modeling & Programming (R/Python)',
    'Pedagogy & Classroom Management',
    'Epidemiological Surveillance & Health Education',
    'Social Research Methods & Community Engagement',
    'Case Management & Counseling Ethics',
    'Active Listening & Psychological Assessment',
    'Destination Marketing & Itinerary Planning',
    'Guest Relations & Hospitality Service Standards',
    'Recruitment & Employee Relations',
    'Cross-Cultural Trade & Market Entry Strategy',
    'Supply Chain Analysis & Contract Negotiation',
    'Land Use Planning & GIS Mapping',
    'GIS Software & Remote Sensing',
    'Property Valuation & Market Analysis',
    'Forest Resource Assessment & Conservation Planning',
    'Environmental Monitoring & Impact Assessment',
    'Medical Device Design & Signal Processing',
    'Patient Assessment & Rehabilitation Technique',
    'Political Analysis & Policy Research',
    'Criminal Justice Analysis & Investigation',
  ];

  final List<String> _availableStrengths = [
    'Perseverance & Discipline',
    'Logical & Analytical Reasoning',
    'Attention to Precision',
    'Empathy & Human Care',
    'Creative Problem Solving',
    'Leadership & Strategic Direction',
    'Team Collaboration',
  ];

  final List<String> _availableAspirations = [
    'Medical Doctor (Physician/Surgeon)',
    'Pharmacist',
    'Registered Nursing Specialist',
    'Software Engineer / AI Architect',
    'Civil Infrastructure Engineer',
    'Electrical Power Engineer',
    'Advocate of the High Court / Corporate Lawyer',
    'Actuary / Risk Strategist',
    'Financial Analyst / Investment Banker',
    'Cybersecurity Architect',
    'Dentist',
    'Veterinary Doctor',
    'Nutritionist / Dietitian',
    'Mechanical Engineer',
    'Architect',
    'Quantity Surveyor',
    'Mathematician / Data Analyst',
    'Economist / Policy Analyst',
    'Journalist / Media Professional',
    'Agricultural Officer / Agronomist',
    'Business Systems Analyst / IT Project Manager',
    // Experiment 1 (profile redesign) additions: deliberately broad,
    // cluster-level aspirations - kept in exact sync with
    // backend/synthetic_data_generator.py's ASPIRATIONS_POOL additions.
    'Healthcare Professional (General)',
    'Technology Professional (General)',
    'Engineering Professional (General)',
    'Finance & Business Professional (General)',
    'Built Environment Professional (General)',
    'Quantitative Analyst / Researcher (General)',
    'Public Policy & Communications Professional (General)',
    'Agricultural & Environmental Professional (General)',
    // 53-class catalogue expansion additions - kept in exact sync with
    // backend/synthetic_data_generator.py's ASPIRATIONS_POOL.
    'Industrial Chemist / Process Chemist',
    'Microbiologist',
    'Food Scientist / Food Technologist',
    'Statistician / Data Analyst',
    'Science Teacher / Educator',
    'Arts Teacher / Educator',
    'Public Health Officer',
    'Sociologist / Social Researcher',
    'Social Worker',
    'Counseling Psychologist',
    'Business Manager / Administrator',
    'Tourism Officer / Destination Manager',
    'Hotel & Hospitality Manager',
    'Real Estate / Property Manager',
    'Chemical Process Engineer',
    'Human Resource Manager',
    'International Trade Manager',
    'Urban & Regional Planner',
    'Geospatial Analyst / Land Surveyor',
    'Medical Laboratory Technologist',
    'Physiotherapist',
    'Community Health Officer',
    'Data Scientist',
    'Biochemist',
    'Physicist / Research Scientist',
    'Chemist / Analytical Scientist',
    'Procurement & Supply Chain Manager',
    'Environmental Scientist / Conservationist',
    'Forester / Conservation Officer',
    'Biomedical Engineer',
    'Political Analyst / Public Administrator',
    'Criminologist / Security Analyst',
    'Educator / Teaching Professional (General)',
    'Social & Community Services Professional (General)',
    'Applied & Physical Sciences Researcher (General)',
    'Tourism & Hospitality Professional (General)',
  ];

  @override
  void initState() {
    super.initState();

    // No fake defaults: every dropdown starts unselected for a brand new
    // profile. A profile being re-edited (returning student) pre-fills from
    // whatever was actually saved before - that's real data, not a guess.
    _compulsoryGrades = {
      for (final subject in _compulsorySubjects) subject: widget.initialProfile.grades[subject],
    };

    final existingOptional = widget.initialProfile.grades.keys
        .where((k) => !_compulsorySubjects.contains(k))
        .toList();
    _totalSubjectCount = (_compulsorySubjects.length + existingOptional.length).clamp(7, 9);
    final optionalSlots = _totalSubjectCount - _compulsorySubjects.length;
    _optionalSubjectChoice = List<String?>.generate(
      optionalSlots,
      (i) => i < existingOptional.length ? existingOptional[i] : null,
    );
    _optionalGrade = List<String?>.generate(
      optionalSlots,
      (i) => i < existingOptional.length ? widget.initialProfile.grades[existingOptional[i]] : null,
    );

    _selectedInterests = List<String>.from(widget.initialProfile.interests);
    _selectedSkills = List<String>.from(widget.initialProfile.skills);
    _selectedStrengths = List<String>.from(widget.initialProfile.strengths);
    _selectedAspirations = List<String>.from(widget.initialProfile.aspirations);
  }

  void _setTotalSubjectCount(int count) {
    setState(() {
      final newOptionalSlots = count - _compulsorySubjects.length;
      if (newOptionalSlots > _optionalSubjectChoice.length) {
        final extra = newOptionalSlots - _optionalSubjectChoice.length;
        _optionalSubjectChoice.addAll(List<String?>.filled(extra, null));
        _optionalGrade.addAll(List<String?>.filled(extra, null));
      } else if (newOptionalSlots < _optionalSubjectChoice.length) {
        _optionalSubjectChoice = _optionalSubjectChoice.sublist(0, newOptionalSlots);
        _optionalGrade = _optionalGrade.sublist(0, newOptionalSlots);
      }
      _totalSubjectCount = count;
    });
  }

  List<String> _choicesForSlot(int slotIndex) {
    final chosenElsewhere = <String>{
      for (int i = 0; i < _optionalSubjectChoice.length; i++)
        if (i != slotIndex && _optionalSubjectChoice[i] != null) _optionalSubjectChoice[i]!,
    };
    return _fullOptionalSubjects.where((s) => !chosenElsewhere.contains(s)).toList();
  }

  int _gradePoints(String grade) => KCSEGrade.fromString(grade).points;

  String _pointsToGrade(int points) {
    final clamped = points.clamp(1, 12);
    return KCSEGrade.values.firstWhere((g) => g.points == clamped, orElse: () => KCSEGrade.cPlus).label;
  }

  String? get _computedMeanGrade {
    final grades = [
      ..._compulsoryGrades.values.whereType<String>(),
      ..._optionalGrade.whereType<String>(),
    ];
    if (grades.isEmpty) return null;
    final totalPoints = grades.fold<int>(0, (sum, g) => sum + _gradePoints(g));
    return _pointsToGrade((totalPoints / grades.length).round());
  }

  bool get _subjectsComplete {
    if (_compulsoryGrades.values.any((g) => g == null)) return false;
    for (int i = 0; i < _optionalSubjectChoice.length; i++) {
      if (_optionalSubjectChoice[i] == null || _optionalGrade[i] == null) return false;
    }
    return true;
  }

  bool get _isComplete =>
      _subjectsComplete &&
      _selectedInterests.isNotEmpty &&
      _selectedSkills.isNotEmpty &&
      _selectedStrengths.isNotEmpty;

  void _toggleItem(List<String> list, String item) {
    setState(() {
      if (list.contains(item)) {
        list.remove(item);
      } else {
        list.add(item);
      }
    });
  }

  void _saveAndGenerate() {
    if (!_isComplete) {
      setState(() => _showValidationErrors = true);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please complete every step first.')),
      );
      return;
    }

    final grades = <String, String>{
      for (final entry in _compulsoryGrades.entries) entry.key: entry.value!,
    };
    for (int i = 0; i < _optionalSubjectChoice.length; i++) {
      grades[_optionalSubjectChoice[i]!] = _optionalGrade[i]!;
    }

    final updated = StudentProfile(
      id: widget.initialProfile.id,
      fullName: widget.initialProfile.fullName,
      indexNumber: widget.initialProfile.indexNumber,
      kcseMeanGrade: _computedMeanGrade ?? 'C+',
      grades: grades,
      interests: _selectedInterests,
      skills: _selectedSkills,
      strengths: _selectedStrengths,
      aspirations: _selectedAspirations,
    );

    widget.onGenerateRecommendations(updated);
  }

  // --- Step flow ----------------------------------------------------------
  // One job per screen instead of one 150-chip scroll. Progress and the
  // per-step requirement mirror exactly what _isComplete checks at the end.
  static const List<String> _stepTitles = ['Grades', 'Interests', 'Skills', 'Aspirations'];

  bool _stepComplete(int step) {
    switch (step) {
      case 0:
        return _subjectsComplete;
      case 1:
        return _selectedInterests.isNotEmpty;
      case 2:
        return _selectedSkills.isNotEmpty && _selectedStrengths.isNotEmpty;
      default:
        return true; // optional - an undecided student can simply continue
    }
  }

  String _stepHint(int step) {
    switch (step) {
      case 0:
        return 'Choose a grade for every subject to continue.';
      case 1:
        return 'Pick at least one interest to continue.';
      case 2:
        return _selectedSkills.isEmpty && _selectedStrengths.isEmpty
            ? 'Pick at least one skill and one strength to continue.'
            : _selectedSkills.isEmpty
                ? 'Pick at least one skill to continue.'
                : 'Pick at least one strength to continue.';
      default:
        return '';
    }
  }

  // A step can be jumped to only if every step before it is already done.
  bool _canGoTo(int target) {
    for (int i = 0; i < target; i++) {
      if (!_stepComplete(i)) return false;
    }
    return true;
  }

  void _goTo(int step) => setState(() => _step = step);

  @override
  Widget build(BuildContext context) {
    final isLast = _step == _stepTitles.length - 1;

    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground(context),
      appBar: AppBar(
        title: const Text(
          'Your Profile',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        backgroundColor: const Color(0xFF14213D),
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Column(
        children: [
          _buildStepHeader(context),
          Expanded(
            child: SingleChildScrollView(
              key: ValueKey(_step),
              padding: const EdgeInsets.all(16.0),
              child: _buildStepBody(context),
            ),
          ),
        ],
      ),
      bottomNavigationBar: _buildBottomBar(context, isLast),
    );
  }

  Widget _buildStepHeader(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 10),
      decoration: BoxDecoration(
        color: AppColors.cardBackground(context),
        border: Border(bottom: BorderSide(color: AppColors.cardBorder(context))),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Step ${_step + 1} of ${_stepTitles.length}',
            style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context), fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              for (int i = 0; i < _stepTitles.length; i++)
                Expanded(
                  child: InkWell(
                    onTap: _canGoTo(i) ? () => _goTo(i) : null,
                    child: Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(3),
                            child: LinearProgressIndicator(
                              value: i < _step || (i == _step && _stepComplete(i)) ? 1.0 : (i == _step ? 0.35 : 0.0),
                              minHeight: 5,
                              backgroundColor: AppColors.cardBorder(context),
                              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.accentTeal),
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            _stepTitles[i],
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: i == _step ? FontWeight.w700 : FontWeight.w500,
                              color: i == _step ? AppColors.textPrimary(context) : AppColors.textSecondary(context),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBottomBar(BuildContext context, bool isLast) {
    final complete = _stepComplete(_step);
    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 12),
        decoration: BoxDecoration(
          color: AppColors.cardBackground(context),
          border: Border(top: BorderSide(color: AppColors.cardBorder(context))),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (!complete)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  _stepHint(_step),
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
                ),
              ),
            Row(
              children: [
                if (_step > 0) ...[
                  OutlinedButton(
                    onPressed: () => _goTo(_step - 1),
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size(88, 48),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: const Text('Back'),
                  ),
                  const SizedBox(width: 12),
                ],
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: complete ? (isLast ? _saveAndGenerate : () => _goTo(_step + 1)) : null,
                    icon: Icon(isLast ? Icons.auto_awesome : Icons.arrow_forward, size: 18),
                    iconAlignment: IconAlignment.end,
                    label: Text(
                      isLast ? 'Generate Recommendations' : 'Next',
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                    ),
                    style: ElevatedButton.styleFrom(
                      minimumSize: const Size.fromHeight(48),
                      backgroundColor: AppColors.accentTeal,
                      foregroundColor: Colors.white,
                      disabledBackgroundColor: AppColors.chipBackground(context),
                      disabledForegroundColor: AppColors.textSecondary(context),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStepBody(BuildContext context) {
    switch (_step) {
      case 0:
        return _buildGradesStep(context);
      case 1:
        return _buildPickerStep(
          title: 'What are you interested in?',
          subtitle: 'Pick the areas you enjoy most. Open a heading, or search for a topic. Choose from any heading - you are not limited to one.',
          child: GroupedOptionPicker(
            groups: withOtherGroup(kInterestGroups, _availableInterests),
            selected: _selectedInterests,
            onToggle: (o) => _toggleItem(_selectedInterests, o),
            searchHint: 'Search interests',
          ),
        );
      case 2:
        return _buildPickerStep(
          title: 'What are you good at?',
          subtitle: 'Choose the practical and thinking skills you have shown, then your strengths as a person.',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              GroupedOptionPicker(
                groups: withOtherGroup(kSkillGroups, _availableSkills),
                selected: _selectedSkills,
                onToggle: (o) => _toggleItem(_selectedSkills, o),
                searchHint: 'Search skills',
              ),
              const SizedBox(height: 20),
              _buildSectionHeader(
                title: 'Personal strengths',
                subtitle: 'Soft skills and attributes that describe you.',
              ),
              const SizedBox(height: 10),
              FlatOptionChips(
                options: _availableStrengths,
                selected: _selectedStrengths,
                onToggle: (o) => _toggleItem(_selectedStrengths, o),
              ),
            ],
          ),
        );
      default:
        return _buildPickerStep(
          title: 'Do you have a career in mind?',
          subtitle: 'This is optional. If you have one, pick your top choice. If not, choose "Not sure yet" - we will recommend from your grades, interests and skills.',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ChoiceChip(
                label: const Text('Not sure yet', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                selected: _selectedAspirations.isEmpty,
                selectedColor: AppColors.accentTeal,
                labelStyle: TextStyle(color: _selectedAspirations.isEmpty ? Colors.white : AppColors.textPrimary(context)),
                backgroundColor: AppColors.cardBackground(context),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                  side: BorderSide(color: _selectedAspirations.isEmpty ? AppColors.accentTeal : AppColors.cardBorder(context)),
                ),
                onSelected: (_) => setState(() => _selectedAspirations.clear()),
              ),
              const SizedBox(height: 14),
              GroupedOptionPicker(
                groups: {'': _availableAspirations},
                selected: _selectedAspirations,
                // One top choice only: the model uses a single career, so a
                // new pick replaces the previous one.
                onToggle: (o) => setState(() {
                  final wasSelected = _selectedAspirations.contains(o);
                  _selectedAspirations.clear();
                  if (!wasSelected) _selectedAspirations.add(o);
                }),
                searchHint: 'Search careers',
              ),
            ],
          ),
        );
    }
  }

  Widget _buildPickerStep({required String title, required String subtitle, required Widget child}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionHeader(title: title, subtitle: subtitle),
        const SizedBox(height: 14),
        child,
      ],
    );
  }

  Widget _buildGradesStep(BuildContext context) {
    final meanGrade = _computedMeanGrade;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Student Info Banner Card
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.cardBackground(context),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.cardBorder(context)),
          ),
          child: Row(
            children: [
              CircleAvatar(
                radius: 22,
                backgroundColor: AppColors.accentTeal.withOpacity(0.15),
                child: const Icon(Icons.school, color: AppColors.accentTeal, size: 24),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.initialProfile.fullName.isNotEmpty ? widget.initialProfile.fullName : 'Candidate Profile',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppColors.textPrimary(context)),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      widget.initialProfile.indexNumber.isNotEmpty
                          ? 'Index No: ${widget.initialProfile.indexNumber}'
                          : 'Form-Four Leaver',
                      style: TextStyle(color: AppColors.textSecondary(context), fontSize: 12),
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text('Mean Grade', style: TextStyle(fontSize: 10, color: AppColors.textSecondary(context))),
                  const SizedBox(height: 2),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF14213D),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      meanGrade ?? '—',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 6),
        Text(
          'Mean Grade is calculated automatically from the subject grades you enter below.',
          style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)),
        ),
        const SizedBox(height: 20),

        _buildSectionHeader(
          title: 'How many subjects did you sit?',
          subtitle: 'KCSE candidates typically sit 7-9 subjects: 4 compulsory plus 3-5 optional, depending on your school.',
        ),
        const SizedBox(height: 10),
        Row(
          children: [7, 8, 9].map((count) {
            final isSelected = _totalSubjectCount == count;
            return Padding(
              padding: const EdgeInsets.only(right: 8.0),
              child: ChoiceChip(
                label: Text('$count subjects', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                selected: isSelected,
                selectedColor: AppColors.accentTeal,
                labelStyle: TextStyle(color: isSelected ? Colors.white : AppColors.textPrimary(context)),
                backgroundColor: AppColors.cardBackground(context),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                  side: BorderSide(color: isSelected ? AppColors.accentTeal : AppColors.cardBorder(context)),
                ),
                onSelected: (_) => _setTotalSubjectCount(count),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 20),

        _buildSectionHeader(
          title: 'Compulsory subjects',
          subtitle:
              'Every candidate must enter these 4. Enter your actual grades - these determine your KUCCPS Cluster Weighted Points (CWP).',
        ),
        const SizedBox(height: 10),
        _gradesCard(
          context,
          [for (final subject in _compulsorySubjects) _buildCompulsorySubjectRow(subject)],
        ),
        const SizedBox(height: 24),

        _buildSectionHeader(
          title: 'Optional subjects (${_optionalSubjectChoice.length})',
          subtitle: 'Select the subjects you actually took and their grades.',
        ),
        const SizedBox(height: 10),
        _gradesCard(
          context,
          [for (int i = 0; i < _optionalSubjectChoice.length; i++) _buildOptionalSubjectRow(i)],
        ),
        if (_showValidationErrors && !_subjectsComplete) ...[
          const SizedBox(height: 8),
          Text(
            'Please select a grade for every compulsory subject and a subject + grade for every optional slot.',
            style: TextStyle(fontSize: 11, color: Colors.red.shade700),
          ),
        ],
      ],
    );
  }

  Widget _gradesCard(BuildContext context, List<Widget> rows) {
    return Card(
      elevation: 0,
      color: AppColors.cardBackground(context),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: AppColors.cardBorder(context)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
        child: Column(
          children: [
            for (int i = 0; i < rows.length; i++) ...[
              if (i > 0) const Divider(height: 16),
              rows[i],
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader({required String title, required String subtitle}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context)),
        ),
        const SizedBox(height: 2),
        Text(
          subtitle,
          style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context), height: 1.3),
        ),
      ],
    );
  }

  Widget _buildCompulsorySubjectRow(String subject) {
    final currentGrade = _compulsoryGrades[subject];
    final showError = _showValidationErrors && currentGrade == null;
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: Text(
            subject,
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.textPrimary(context)),
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
          decoration: BoxDecoration(
            color: AppColors.chipBackground(context),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: showError ? Colors.red.shade300 : Colors.grey.shade300),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: currentGrade,
              hint: const Text('Select', style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8))),
              isDense: true,
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context)),
              items: _allGrades.map((g) => DropdownMenuItem<String>(value: g, child: Text(g))).toList(),
              onChanged: (val) => setState(() => _compulsoryGrades[subject] = val),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildOptionalSubjectRow(int slotIndex) {
    final chosenSubject = _optionalSubjectChoice[slotIndex];
    final chosenGrade = _optionalGrade[slotIndex];
    final showError = _showValidationErrors && (chosenSubject == null || chosenGrade == null);
    final choices = _choicesForSlot(slotIndex);

    return Row(
      children: [
        Expanded(
          flex: 3,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
            decoration: BoxDecoration(
              color: AppColors.chipBackground(context),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: showError && chosenSubject == null ? Colors.red.shade300 : Colors.grey.shade300),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                isExpanded: true,
                value: chosenSubject,
                hint: Text('Optional subject ${slotIndex + 1}', style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8))),
                isDense: true,
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary(context)),
                items: choices.map((s) => DropdownMenuItem<String>(value: s, child: Text(s, overflow: TextOverflow.ellipsis))).toList(),
                onChanged: (val) => setState(() => _optionalSubjectChoice[slotIndex] = val),
              ),
            ),
          ),
        ),
        const SizedBox(width: 10),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
          decoration: BoxDecoration(
            color: AppColors.chipBackground(context),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: showError && chosenGrade == null ? Colors.red.shade300 : Colors.grey.shade300),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: chosenGrade,
              hint: const Text('Grade', style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8))),
              isDense: true,
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context)),
              items: _allGrades.map((g) => DropdownMenuItem<String>(value: g, child: Text(g))).toList(),
              onChanged: chosenSubject == null ? null : (val) => setState(() => _optionalGrade[slotIndex] = val),
            ),
          ),
        ),
      ],
    );
  }
}
