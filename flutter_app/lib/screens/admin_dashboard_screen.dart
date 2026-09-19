import 'package:flutter/material.dart';
import '../models/programme.dart';
import '../data/programme_repository.dart';

class AdminDashboardScreen extends StatefulWidget {
  final List<Programme>? programmes;
  final Function(String programmeId, double newCutoff) onUpdateCutoff;
  final VoidCallback? onLogout;

  const AdminDashboardScreen({
    Key? key,
    this.programmes,
    required this.onUpdateCutoff,
    this.onLogout,
  }) : super(key: key);

  @override
  State<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends State<AdminDashboardScreen> {
  late List<Programme> _displayedProgrammes;

  final List<Map<String, String>> auditLogs = [
    {
      'timestamp': 'Today, 08:30 AM',
      'action': 'Model Inference Cycle Executed',
      'actor': 'Decision Support Engine',
      'details': 'Evaluated student KCSE cluster weighted profile via Random Forest (latency: 38ms)',
    },
    {
      'timestamp': 'Yesterday, 04:15 PM',
      'action': 'Cluster Cutoff Updated',
      'actor': 'Dean of Admissions',
      'details': 'Updated KUCCPS placement cutoff for Medicine & Health Sciences to 43.5 pts',
    },
    {
      'timestamp': '16 Sep 2026, 11:20 AM',
      'action': 'Degree Curriculum Validated',
      'actor': 'Academic Registrar',
      'details': 'CUE accreditation verified across 11 undergraduate faculties',
    },
  ];

  @override
  void initState() {
    super.initState();
    _displayedProgrammes = widget.programmes != null && widget.programmes!.isNotEmpty
        ? List.from(widget.programmes!)
        : List.from(ProgrammeRepository.allProgrammes);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF1F5F9),
      appBar: AppBar(
        title: const Text(
          'Administrator Management Portal',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        backgroundColor: const Color(0xFF1E293B),
        foregroundColor: Colors.white,
        actions: [
          if (widget.onLogout != null)
            IconButton(
              icon: const Icon(Icons.logout, size: 20),
              tooltip: 'Sign Out',
              onPressed: widget.onLogout,
            ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Admin Control Banner
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
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
                          Icon(Icons.admin_panel_settings, color: Color(0xFF38BDF8), size: 20),
                          SizedBox(width: 8),
                          Text(
                            'Administrative Governance & Audit',
                            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                          ),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: const Color(0xFF38BDF8).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.4)),
                        ),
                        child: const Text(
                          'Authenticated',
                          style: TextStyle(color: Color(0xFF38BDF8), fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Configure programme cutoffs, audit machine learning decision logs, and manage KUCCPS placement criteria.',
                    style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12, height: 1.4),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Performance & Model Metrics
            Row(
              children: [
                _buildMetricCard('Random Forest F1', '92.4%', Icons.analytics, const Color(0xFF0EA5A4)),
                const SizedBox(width: 10),
                _buildMetricCard('Degree Catalog', '${_displayedProgrammes.length}', Icons.school, const Color(0xFF6366F1)),
                const SizedBox(width: 10),
                _buildMetricCard('Mean Match', '88.6%', Icons.check_circle, const Color(0xFFF59E0B)),
              ],
            ),
            const SizedBox(height: 22),

            // Section 1: Manage Programme Cutoffs
            const Text(
              'University Programme Catalog & KUCCPS Cutoffs',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
            ),
            const SizedBox(height: 4),
            Text(
              'Adjusting cutoff thresholds immediately recalibrates applicant eligibility margins in real time.',
              style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
            ),
            const SizedBox(height: 12),

            ..._displayedProgrammes.map((prog) {
              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            prog.title,
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF0F172A)),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '${prog.code} • ${prog.faculty}',
                            style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 10),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF1F5F9),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            '${prog.averageCutoff.toStringAsFixed(1)} pts',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF1E293B)),
                          ),
                        ),
                        const SizedBox(width: 6),
                        IconButton(
                          icon: const Icon(Icons.edit, size: 18, color: Color(0xFF0EA5A4)),
                          tooltip: 'Edit Cutoff',
                          onPressed: () => _showEditCutoffDialog(context, prog),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            }).toList(),
            const SizedBox(height: 22),

            // Section 2: Audit Trails & Activity Logs
            const Text(
              'System Audit Trails & Model Inference Logs',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
            ),
            const SizedBox(height: 4),
            Text(
              'Tracks decision support inferences and administrative requirement adjustments.',
              style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
            ),
            const SizedBox(height: 12),

            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Column(
                children: auditLogs.map((log) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12.0),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Padding(
                          padding: EdgeInsets.only(top: 2.0),
                          child: Icon(Icons.history, size: 16, color: Color(0xFF64748B)),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    log['action']!,
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Color(0xFF0F172A)),
                                  ),
                                  Text(
                                    log['timestamp']!,
                                    style: TextStyle(fontSize: 10, color: Colors.grey.shade500),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 2),
                              Text(
                                'Authorized Actor: ${log['actor']!}',
                                style: const TextStyle(fontSize: 11, color: Color(0xFF0EA5A4), fontWeight: FontWeight.w600),
                              ),
                              Text(
                                log['details']!,
                                style: TextStyle(fontSize: 11, color: Colors.grey.shade600, height: 1.3),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard(String title, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 18, color: color),
            const SizedBox(height: 6),
            Text(
              value,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
            ),
            Text(
              title,
              style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
            ),
          ],
        ),
      ),
    );
  }

  void _showEditCutoffDialog(BuildContext context, Programme prog) {
    final controller = TextEditingController(text: prog.averageCutoff.toString());
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Edit Cutoff: ${prog.code}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(prog.title, style: TextStyle(fontSize: 12, color: Colors.grey.shade700)),
            const SizedBox(height: 14),
            TextField(
              controller: controller,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'KUCCPS Average Cutoff (Points)',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0EA5A4),
              foregroundColor: Colors.white,
            ),
            onPressed: () {
              final newPts = double.tryParse(controller.text);
              if (newPts != null) {
                widget.onUpdateCutoff(prog.id, newPts);
                setState(() {
                  final idx = _displayedProgrammes.indexWhere((p) => p.id == prog.id);
                  if (idx != -1) {
                    _displayedProgrammes[idx] = Programme(
                      id: prog.id,
                      code: prog.code,
                      title: prog.title,
                      faculty: prog.faculty,
                      minMeanGrade: prog.minMeanGrade,
                      averageCutoff: newPts,
                      clusterGroup: prog.clusterGroup,
                      clusterSubjects: prog.clusterSubjects,
                      minimumSubjectRequirements: prog.minimumSubjectRequirements,
                      description: prog.description,
                      careerOpportunities: prog.careerOpportunities,
                      requiredSkills: prog.requiredSkills,
                      professionalCertifications: prog.professionalCertifications,
                      offeringUniversities: prog.offeringUniversities,
                      durationYears: prog.durationYears,
                    );
                  }
                });
                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Updated ${prog.code} cutoff to $newPts points')),
                );
              }
            },
            child: const Text('Save Changes'),
          ),
        ],
      ),
    );
  }
}
