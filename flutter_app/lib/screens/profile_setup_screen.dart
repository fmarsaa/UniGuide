import 'package:flutter/material.dart';
import '../models/student_profile.dart';

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
  late String _meanGrade;
  late Map<String, String> _grades;
  late List<String> _selectedInterests;
  late List<String> _selectedSkills;
  late List<String> _selectedStrengths;
  late List<String> _selectedAspirations;

  final List<String> _allGrades = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'E'];

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
  ];

  @override
  void initState() {
    super.initState();
    _meanGrade = widget.initialProfile.kcseMeanGrade;
    _grades = Map<String, String>.from(widget.initialProfile.grades);
    // Ensure core cluster subjects exist in the map
    _grades.putIfAbsent('Mathematics', () => 'B+');
    _grades.putIfAbsent('English', () => 'B');
    _grades.putIfAbsent('Kiswahili', () => 'B');
    _grades.putIfAbsent('Biology', () => 'B');
    _grades.putIfAbsent('Chemistry', () => 'B');
    _grades.putIfAbsent('Physics', () => 'B');

    _selectedInterests = List<String>.from(widget.initialProfile.interests);
    _selectedSkills = List<String>.from(widget.initialProfile.skills);
    _selectedStrengths = List<String>.from(widget.initialProfile.strengths);
    _selectedAspirations = List<String>.from(widget.initialProfile.aspirations);
  }

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
    final updated = StudentProfile(
      id: widget.initialProfile.id,
      fullName: widget.initialProfile.fullName,
      indexNumber: widget.initialProfile.indexNumber,
      kcseMeanGrade: _meanGrade,
      grades: _grades,
      interests: _selectedInterests,
      skills: _selectedSkills,
      strengths: _selectedStrengths,
      aspirations: _selectedAspirations,
    );

    widget.onGenerateRecommendations(updated);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text(
          'Candidate Academic & Career Profile',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        backgroundColor: const Color(0xFF14213D),
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Student Info Banner Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: Colors.grey.shade200),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.03),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 22,
                    backgroundColor: const Color(0xFF0EA5A4).withOpacity(0.15),
                    child: const Icon(Icons.school, color: Color(0xFF0EA5A4), size: 24),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.initialProfile.fullName.isNotEmpty
                              ? widget.initialProfile.fullName
                              : 'Candidate Profile',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF0F172A)),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          widget.initialProfile.indexNumber.isNotEmpty
                              ? 'Index No: ${widget.initialProfile.indexNumber}'
                              : 'Form-Four Leaver',
                          style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      const Text('Mean Grade', style: TextStyle(fontSize: 10, color: Color(0xFF64748B))),
                      const SizedBox(height: 2),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFF14213D),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            value: _meanGrade,
                            dropdownColor: const Color(0xFF1E293B),
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                            icon: const Icon(Icons.arrow_drop_down, color: Colors.white, size: 18),
                            isDense: true,
                            items: _allGrades.map((g) {
                              return DropdownMenuItem<String>(
                                value: g,
                                child: Text(g),
                              );
                            }).toList(),
                            onChanged: (val) {
                              if (val != null) setState(() => _meanGrade = val);
                            },
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Section 1: KCSE Subject Performance
            _buildSectionHeader(
              title: '1. KCSE Subject Performance',
              subtitle: 'Specify verified grades for cluster subjects. These determine your KUCCPS Cluster Weighted Points (CWP).',
            ),
            const SizedBox(height: 10),

            Card(
              elevation: 0,
              color: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
                side: BorderSide(color: Colors.grey.shade200),
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
                child: Column(
                  children: [
                    _buildSubjectDropdown('Mathematics', 'Compulsory STEM Prerequisite'),
                    const Divider(height: 16),
                    _buildSubjectDropdown('English', 'Compulsory Language Prerequisite'),
                    const Divider(height: 16),
                    _buildSubjectDropdown('Kiswahili', 'Official Language Prerequisite'),
                    const Divider(height: 16),
                    _buildSubjectDropdown('Biology', 'Medical & Life Sciences Cluster'),
                    const Divider(height: 16),
                    _buildSubjectDropdown('Chemistry', 'Physical & Health Sciences Cluster'),
                    const Divider(height: 16),
                    _buildSubjectDropdown('Physics', 'Engineering & Technology Cluster'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Section 2: Personal & Academic Interests
            _buildSectionHeader(
              title: '2. Personal & Academic Interests',
              subtitle: 'Select your preferred knowledge areas to guide Random Forest domain classification.',
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _availableInterests.map((interest) {
                final isSelected = _selectedInterests.contains(interest);
                return FilterChip(
                  label: Text(
                    interest,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                      color: isSelected ? Colors.white : const Color(0xFF1E293B),
                    ),
                  ),
                  selected: isSelected,
                  selectedColor: const Color(0xFF0EA5A4),
                  backgroundColor: Colors.white,
                  checkmarkColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                    side: BorderSide(
                      color: isSelected ? const Color(0xFF0EA5A4) : Colors.grey.shade300,
                    ),
                  ),
                  onSelected: (_) => _toggleItem(_selectedInterests, interest),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),

            // Section 3: Demonstrated Skills
            _buildSectionHeader(
              title: '3. Demonstrated Skills',
              subtitle: 'Identify your practical and cognitive strengths.',
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _availableSkills.map((skill) {
                final isSelected = _selectedSkills.contains(skill);
                return FilterChip(
                  label: Text(
                    skill,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                      color: isSelected ? Colors.white : const Color(0xFF1E293B),
                    ),
                  ),
                  selected: isSelected,
                  selectedColor: const Color(0xFF4F46E5),
                  backgroundColor: Colors.white,
                  checkmarkColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                    side: BorderSide(
                      color: isSelected ? const Color(0xFF4F46E5) : Colors.grey.shade300,
                    ),
                  ),
                  onSelected: (_) => _toggleItem(_selectedSkills, skill),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),

            // Section 4: Personal Strengths
            _buildSectionHeader(
              title: '4. Personal Strengths',
              subtitle: 'Core soft skills and behavioral attributes.',
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _availableStrengths.map((str) {
                final isSelected = _selectedStrengths.contains(str);
                return FilterChip(
                  label: Text(
                    str,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                      color: isSelected ? Colors.white : const Color(0xFF1E293B),
                    ),
                  ),
                  selected: isSelected,
                  selectedColor: const Color(0xFFD97706),
                  backgroundColor: Colors.white,
                  checkmarkColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                    side: BorderSide(
                      color: isSelected ? const Color(0xFFD97706) : Colors.grey.shade300,
                    ),
                  ),
                  onSelected: (_) => _toggleItem(_selectedStrengths, str),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),

            // Section 5: Career Aspirations
            _buildSectionHeader(
              title: '5. Career Aspirations',
              subtitle: 'Select intended professional pathways.',
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _availableAspirations.map((asp) {
                final isSelected = _selectedAspirations.contains(asp);
                return FilterChip(
                  label: Text(
                    asp,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                      color: isSelected ? Colors.white : const Color(0xFF1E293B),
                    ),
                  ),
                  selected: isSelected,
                  selectedColor: const Color(0xFF059669),
                  backgroundColor: Colors.white,
                  checkmarkColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                    side: BorderSide(
                      color: isSelected ? const Color(0xFF059669) : Colors.grey.shade300,
                    ),
                  ),
                  onSelected: (_) => _toggleItem(_selectedAspirations, asp),
                );
              }).toList(),
            ),
            const SizedBox(height: 32),

            // Submit / Re-evaluate Button
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton.icon(
                onPressed: _saveAndGenerate,
                icon: const Icon(Icons.auto_awesome, color: Colors.white, size: 20),
                label: const Text(
                  'Run Decision Engine & Generate Recommendations',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0EA5A4),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                  elevation: 2,
                ),
              ),
            ),
            const SizedBox(height: 24),
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
          style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
        ),
        const SizedBox(height: 2),
        Text(
          subtitle,
          style: TextStyle(fontSize: 12, color: Colors.grey.shade600, height: 1.3),
        ),
      ],
    );
  }

  Widget _buildSubjectDropdown(String subject, String note) {
    final currentGrade = _grades[subject] ?? 'B';
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                subject,
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Color(0xFF1E293B)),
              ),
              Text(
                note,
                style: TextStyle(fontSize: 11, color: Colors.grey.shade500),
              ),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
          decoration: BoxDecoration(
            color: const Color(0xFFF1F5F9),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.grey.shade300),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: _allGrades.contains(currentGrade) ? currentGrade : 'B',
              isDense: true,
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
              items: _allGrades.map((g) {
                return DropdownMenuItem<String>(
                  value: g,
                  child: Text(g),
                );
              }).toList(),
              onChanged: (val) {
                if (val != null) {
                  setState(() => _grades[subject] = val);
                }
              },
            ),
          ),
        ),
      ],
    );
  }
}
