import 'package:flutter/material.dart';
import '../models/programme.dart';
import '../data/programme_repository.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';
import '../theme/theme_controller.dart';
import 'package:provider/provider.dart';

typedef ProgrammeUpdater = Future<void> Function(
  String programmeId, {
  double? averageCutoff,
  String? minMeanGrade,
  String? description,
});

class AdminDashboardScreen extends StatefulWidget {
  final List<Programme>? programmes;
  final ProgrammeUpdater onUpdateProgramme;
  final VoidCallback? onLogout;

  const AdminDashboardScreen({
    Key? key,
    this.programmes,
    required this.onUpdateProgramme,
    this.onLogout,
  }) : super(key: key);

  @override
  State<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends State<AdminDashboardScreen> {
  late List<Programme> _displayedProgrammes;

  int _currentAdminTabIndex = 0;

  List<Map<String, dynamic>> _auditLogs = [];
  bool _isLoadingLogs = true;
  String? _auditLogError;

  List<Map<String, dynamic>> _studentFeedback = [];
  bool _isLoadingFeedback = true;
  String? _feedbackError;

  double? _modelAccuracy;
  double? _modelWeightedF1;

  List<Map<String, dynamic>> _freshnessFlags = [];
  bool _isLoadingFreshness = true;
  bool _isRunningFreshnessCheck = false;
  String? _freshnessError;
  String? _freshnessCheckMessage;

  @override
  void initState() {
    super.initState();
    _displayedProgrammes = widget.programmes != null && widget.programmes!.isNotEmpty
        ? List.from(widget.programmes!)
        : List.from(ProgrammeRepository.allProgrammes);
    _loadAuditLogs();
    _loadStudentFeedback();
    _loadModelMetrics();
    _loadFreshnessFlags();
  }

  Future<void> _loadFreshnessFlags() async {
    setState(() {
      _isLoadingFreshness = true;
      _freshnessError = null;
    });
    try {
      final flags = await ApiService.fetchCatalogueFreshnessFlags();
      setState(() {
        _freshnessFlags = flags;
        _isLoadingFreshness = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _freshnessError = e.message;
        _isLoadingFreshness = false;
      });
    }
  }

  Future<void> _runFreshnessCheck() async {
    setState(() {
      _isRunningFreshnessCheck = true;
      _freshnessCheckMessage = null;
    });
    try {
      final result = await ApiService.runCatalogueFreshnessCheck();
      setState(() {
        _freshnessCheckMessage =
            'Checked ${result['checked_programmes']} programmes against KUCCPS - ${result['newly_flagged']} new issue(s) found.';
        _isRunningFreshnessCheck = false;
      });
      await _loadFreshnessFlags();
    } on ApiException catch (e) {
      setState(() {
        _freshnessCheckMessage = 'Check failed: ${e.message}';
        _isRunningFreshnessCheck = false;
      });
    }
  }

  Future<void> _dismissFreshnessFlag(String flagId) async {
    try {
      await ApiService.dismissCatalogueFreshnessFlag(flagId);
      setState(() => _freshnessFlags.removeWhere((f) => f['id'] == flagId));
    } on ApiException catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not dismiss: ${e.message}'), backgroundColor: Colors.redAccent),
      );
    }
  }

  Future<void> _loadModelMetrics() async {
    try {
      final health = await ApiService.fetchHealth();
      final metrics = health['model_metrics'] as Map<String, dynamic>?;
      if (metrics != null && mounted) {
        setState(() {
          _modelAccuracy = (metrics['accuracy'] as num?)?.toDouble();
          _modelWeightedF1 = (metrics['weighted_f1'] as num?)?.toDouble();
        });
      }
    } on ApiException {
      // Non-critical: metric cards just fall back to "—".
    }
  }

  Future<void> _loadAuditLogs() async {
    setState(() {
      _isLoadingLogs = true;
      _auditLogError = null;
    });
    try {
      final logs = await ApiService.fetchAuditLogs();
      setState(() {
        _auditLogs = logs;
        _isLoadingLogs = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _auditLogError = e.message;
        _isLoadingLogs = false;
      });
    }
  }

  Future<void> _loadStudentFeedback() async {
    setState(() {
      _isLoadingFeedback = true;
      _feedbackError = null;
    });
    try {
      final feedback = await ApiService.fetchStudentFeedback();
      setState(() {
        _studentFeedback = feedback;
        _isLoadingFeedback = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _feedbackError = e.message;
        _isLoadingFeedback = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeController = context.watch<ThemeController>();
    final isDark = themeController.mode == ThemeMode.dark ||
        (themeController.mode == ThemeMode.system &&
            MediaQuery.platformBrightnessOf(context) == Brightness.dark);

    final List<Widget> adminPages = [
      _buildConsoleTab(),
      _buildCatalogTab(),
      _buildFeedbackTab(),
    ];

    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground(context),
      appBar: AppBar(
        title: const Text(
          'Administrator Management Portal',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        backgroundColor: const Color(0xFF1E293B),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: Icon(isDark ? Icons.light_mode_outlined : Icons.dark_mode_outlined, size: 20),
            tooltip: isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode',
            onPressed: () => context.read<ThemeController>().toggle(),
          ),
          if (widget.onLogout != null)
            IconButton(
              icon: const Icon(Icons.logout, size: 20),
              tooltip: 'Sign Out',
              onPressed: widget.onLogout,
            ),
        ],
      ),
      body: adminPages[_currentAdminTabIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentAdminTabIndex,
        onDestinationSelected: (index) {
          setState(() => _currentAdminTabIndex = index);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard, color: Color(0xFF0EA5A4)),
            label: 'Console',
          ),
          NavigationDestination(
            icon: Icon(Icons.menu_book_outlined),
            selectedIcon: Icon(Icons.menu_book, color: Color(0xFF0EA5A4)),
            label: 'Catalog & Cutoffs',
          ),
          NavigationDestination(
            icon: Icon(Icons.reviews_outlined),
            selectedIcon: Icon(Icons.reviews, color: Color(0xFF0EA5A4)),
            label: 'Feedback',
          ),
        ],
      ),
    );
  }

  Widget _buildConsoleTab() {
    return SingleChildScrollView(
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
                  'Manage programme cutoffs, admission requirements, and descriptions, and review the audit trail of changes.',
                  style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12, height: 1.4),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Performance & Model Metrics (from the last training run's model_metrics.json)
          Row(
            children: [
              _buildMetricCard(
                'Random Forest Accuracy',
                _modelAccuracy != null ? '${(_modelAccuracy! * 100).toStringAsFixed(1)}%' : '—',
                Icons.analytics,
                const Color(0xFF0EA5A4),
              ),
              const SizedBox(width: 10),
              _buildMetricCard('Degree Catalog', '${_displayedProgrammes.length}', Icons.school, const Color(0xFF6366F1)),
              const SizedBox(width: 10),
              _buildMetricCard(
                'Weighted F1-Score',
                _modelWeightedF1 != null ? '${(_modelWeightedF1! * 100).toStringAsFixed(1)}%' : '—',
                Icons.check_circle,
                const Color(0xFFF59E0B),
              ),
            ],
          ),
          const SizedBox(height: 22),

          // Catalogue Freshness - re-checks the catalog against KUCCPS's own
          // published data and flags anything that may have changed, rather
          // than relying purely on an admin noticing on their own.
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  'Catalogue Freshness',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context)),
                ),
              ),
              ElevatedButton.icon(
                onPressed: _isRunningFreshnessCheck ? null : _runFreshnessCheck,
                icon: _isRunningFreshnessCheck
                    ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.sync, size: 16),
                label: Text(_isRunningFreshnessCheck ? 'Checking...' : 'Check Now'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF38BDF8),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Re-checks the catalog against KUCCPS\'s own published cutoff data. Never edits anything automatically - only flags a university-programme pair for your review when it may have changed.',
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
          ),
          const SizedBox(height: 12),
          if (_freshnessCheckMessage != null) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFF38BDF8).withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.3)),
              ),
              child: Text(_freshnessCheckMessage!, style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 12)),
            ),
            const SizedBox(height: 10),
          ],
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.cardBackground(context),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.cardBorder(context)),
            ),
            child: _buildFreshnessFlagsBody(),
          ),
          const SizedBox(height: 22),

          // Audit Trails & Activity Logs
          Text(
            'System Audit Trails & Model Inference Logs',
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context)),
          ),
          const SizedBox(height: 4),
          Text(
            'Tracks decision support inferences and administrative requirement adjustments.',
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
          ),
          const SizedBox(height: 12),

          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.cardBackground(context),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.cardBorder(context)),
            ),
            child: _buildAuditLogBody(),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildCatalogTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'University Programme Catalog & KUCCPS Cutoffs',
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context)),
          ),
          const SizedBox(height: 4),
          Text(
            'Tap the edit icon to update a programme\'s cutoff, minimum grade, or description. Changes are saved immediately and logged in the audit trail.',
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
          ),
          const SizedBox(height: 12),

          ..._displayedProgrammes.map((prog) {
            return Container(
              margin: const EdgeInsets.only(bottom: 10),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.cardBackground(context),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.cardBorder(context)),
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
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.textPrimary(context)),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${prog.code} • ${prog.faculty}',
                          style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)),
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
                          color: AppColors.chipBackground(context),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          '${prog.averageCutoff.toStringAsFixed(1)} pts',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.textPrimary(context)),
                        ),
                      ),
                      const SizedBox(width: 6),
                      IconButton(
                        icon: const Icon(Icons.edit, size: 18, color: Color(0xFF0EA5A4)),
                        tooltip: 'Edit Programme',
                        onPressed: () => _showEditProgrammeDialog(context, prog),
                      ),
                    ],
                  ),
                ],
              ),
            );
          }).toList(),
          const SizedBox(height: 12),
        ],
      ),
    );
  }

  Widget _buildFeedbackTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Student Feedback & Ratings',
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context)),
          ),
          const SizedBox(height: 4),
          Text(
            'Real ratings and comments students submitted after receiving a recommendation.',
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
          ),
          const SizedBox(height: 12),

          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.cardBackground(context),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.cardBorder(context)),
            ),
            child: _buildFeedbackBody(),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildFreshnessFlagsBody() {
    if (_isLoadingFreshness) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 12),
        child: Center(child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF38BDF8)))),
      );
    }
    if (_freshnessError != null) {
      return Row(
        children: [
          Expanded(
            child: Text(
              'Could not load freshness flags: $_freshnessError',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
            ),
          ),
          TextButton(onPressed: _loadFreshnessFlags, child: const Text('Retry')),
        ],
      );
    }
    if (_freshnessFlags.isEmpty) {
      return Row(
        children: [
          const Icon(Icons.check_circle_outline, size: 16, color: Color(0xFF0EA5A4)),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'No open flags. Run "Check Now" to compare the catalog against KUCCPS\'s latest published data.',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
            ),
          ),
        ],
      );
    }
    return Column(
      children: _freshnessFlags.map((flag) {
        return Padding(
          padding: const EdgeInsets.only(bottom: 12.0),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Padding(
                padding: EdgeInsets.only(top: 2.0),
                child: Icon(Icons.warning_amber_rounded, size: 16, color: Color(0xFFF59E0B)),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${flag['programmeTitle'] ?? 'Unknown programme'} - ${flag['universityName'] ?? 'Unknown university'}',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppColors.textPrimary(context)),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      (flag['details'] ?? '').toString(),
                      style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context), height: 1.3),
                    ),
                  ],
                ),
              ),
              TextButton(
                onPressed: () => _dismissFreshnessFlag(flag['id'] as String),
                child: const Text('Dismiss', style: TextStyle(fontSize: 11)),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildAuditLogBody() {
    if (_isLoadingLogs) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 12),
        child: Center(child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0EA5A4)))),
      );
    }
    if (_auditLogError != null) {
      return Row(
        children: [
          Expanded(
            child: Text(
              'Could not load audit logs: $_auditLogError',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
            ),
          ),
          TextButton(onPressed: _loadAuditLogs, child: const Text('Retry')),
        ],
      );
    }
    if (_auditLogs.isEmpty) {
      return Text(
        'No administrative actions have been recorded yet.',
        style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
      );
    }
    return Column(
      children: _auditLogs.map((log) {
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
                          (log['action'] ?? 'Action').toString(),
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppColors.textPrimary(context)),
                        ),
                        Text(
                          (log['timestamp'] ?? '').toString(),
                          style: TextStyle(fontSize: 10, color: AppColors.textSecondary(context)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Authorized Actor: ${log['actor'] ?? 'Unknown'}',
                      style: const TextStyle(fontSize: 11, color: Color(0xFF0EA5A4), fontWeight: FontWeight.w600),
                    ),
                    Text(
                      (log['details'] ?? '').toString(),
                      style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context), height: 1.3),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildFeedbackBody() {
    if (_isLoadingFeedback) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 12),
        child: Center(child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0EA5A4)))),
      );
    }
    if (_feedbackError != null) {
      return Row(
        children: [
          Expanded(
            child: Text(
              'Could not load feedback: $_feedbackError',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
            ),
          ),
          TextButton(onPressed: _loadStudentFeedback, child: const Text('Retry')),
        ],
      );
    }
    if (_studentFeedback.isEmpty) {
      return Text(
        'No student feedback has been submitted yet.',
        style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
      );
    }
    return Column(
      children: _studentFeedback.map((fb) {
        final rating = (fb['rating'] as num?)?.toInt() ?? 0;
        final comments = (fb['comments'] ?? '').toString();
        final studentEmail = (fb['studentEmail'] ?? 'Unknown student').toString();
        final submittedAt = (fb['submittedAt'] ?? '').toString();
        return Padding(
          padding: const EdgeInsets.only(bottom: 14.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: List.generate(5, (i) => Icon(
                          i < rating ? Icons.star : Icons.star_border,
                          size: 14,
                          color: const Color(0xFFF59E0B),
                        )),
                  ),
                  Text(
                    submittedAt.length >= 10 ? submittedAt.substring(0, 10) : submittedAt,
                    style: TextStyle(fontSize: 10, color: AppColors.textSecondary(context)),
                  ),
                ],
              ),
              const SizedBox(height: 2),
              Text(
                studentEmail,
                style: const TextStyle(fontSize: 11, color: Color(0xFF0EA5A4), fontWeight: FontWeight.w600),
              ),
              if (comments.isNotEmpty) ...[
                const SizedBox(height: 2),
                Text(
                  comments,
                  style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context), height: 1.3),
                ),
              ],
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildMetricCard(String title, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.cardBackground(context),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.cardBorder(context)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 18, color: color),
            const SizedBox(height: 6),
            Text(
              value,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context)),
            ),
            Text(
              title,
              style: TextStyle(fontSize: 10, color: AppColors.textSecondary(context)),
            ),
          ],
        ),
      ),
    );
  }

  void _showEditProgrammeDialog(BuildContext context, Programme prog) {
    final cutoffController = TextEditingController(text: prog.averageCutoff.toString());
    final minGradeController = TextEditingController(text: prog.minMeanGrade);
    final descriptionController = TextEditingController(text: prog.description);
    bool isSaving = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(builder: (ctx, setDialogState) => AlertDialog(
        title: Text('Edit Programme: ${prog.code}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(prog.title, style: TextStyle(fontSize: 12, color: Colors.grey.shade700)),
              const SizedBox(height: 14),
              TextField(
                controller: cutoffController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'KUCCPS Average Cutoff (Points)',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: minGradeController,
                decoration: const InputDecoration(
                  labelText: 'Minimum KCSE Mean Grade',
                  hintText: 'e.g. C+',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: descriptionController,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: 'Programme Description',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: isSaving ? null : () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0EA5A4),
              foregroundColor: Colors.white,
            ),
            onPressed: isSaving
                ? null
                : () async {
                    final newPts = double.tryParse(cutoffController.text);
                    if (newPts == null) return;
                    final newMinGrade = minGradeController.text.trim();
                    final newDescription = descriptionController.text.trim();
                    setDialogState(() => isSaving = true);
                    try {
                      await widget.onUpdateProgramme(
                        prog.id,
                        averageCutoff: newPts,
                        minMeanGrade: newMinGrade.isNotEmpty ? newMinGrade : null,
                        description: newDescription.isNotEmpty ? newDescription : null,
                      );
                      if (!mounted) return;
                      setState(() {
                        final idx = _displayedProgrammes.indexWhere((p) => p.id == prog.id);
                        if (idx != -1) {
                          _displayedProgrammes[idx] = Programme(
                            id: prog.id,
                            code: prog.code,
                            title: prog.title,
                            faculty: prog.faculty,
                            minMeanGrade: newMinGrade.isNotEmpty ? newMinGrade : prog.minMeanGrade,
                            averageCutoff: newPts,
                            clusterGroup: prog.clusterGroup,
                            clusterSubjects: prog.clusterSubjects,
                            minimumSubjectRequirements: prog.minimumSubjectRequirements,
                            description: newDescription.isNotEmpty ? newDescription : prog.description,
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
                        SnackBar(content: Text('Updated ${prog.code}')),
                      );
                      _loadAuditLogs();
                    } on ApiException catch (e) {
                      setDialogState(() => isSaving = false);
                      ScaffoldMessenger.of(ctx).showSnackBar(
                        SnackBar(content: Text('Could not save: ${e.message}'), backgroundColor: Colors.redAccent),
                      );
                    }
                  },
            child: isSaving
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Text('Save Changes'),
          ),
        ],
      )),
    );
  }
}
