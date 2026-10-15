import 'dart:async';
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

  List<Map<String, dynamic>> _freshnessHistory = [];
  bool _isLoadingFreshnessHistory = true;

  final TextEditingController _catalogSearchController = TextEditingController();
  String _catalogSearchQuery = '';

  final TextEditingController _auditSearchController = TextEditingController();
  String _auditSearchQuery = '';

  List<Map<String, dynamic>> _admins = [];
  bool _isLoadingAdmins = true;
  String? _adminsError;
  final TextEditingController _addAdminController = TextEditingController();
  bool _isAddingAdmin = false;

  Map<String, dynamic> _trainingStatus = {'running': false};
  bool _isTriggeringRetrain = false;
  String? _retrainMessage;
  List<Map<String, dynamic>> _modelBackups = [];
  bool _isLoadingBackups = true;
  Timer? _trainingPollTimer;

  Map<String, dynamic>? _popularity;
  bool _isLoadingPopularity = true;

  @override
  void initState() {
    super.initState();
    _displayedProgrammes = widget.programmes != null && widget.programmes!.isNotEmpty
        ? List.from(widget.programmes!)
        : List.from(ProgrammeRepository.allProgrammes);
    _loadAdminProgrammes();
    _loadAuditLogs();
    _loadStudentFeedback();
    _loadModelMetrics();
    _loadFreshnessFlags();
    _loadFreshnessHistory();
    _loadAdmins();
    _loadTrainingStatus();
    _loadModelBackups();
    _loadPopularity();
  }

  @override
  void dispose() {
    _trainingPollTimer?.cancel();
    _catalogSearchController.dispose();
    _auditSearchController.dispose();
    _addAdminController.dispose();
    super.dispose();
  }

  /// Admin Catalog tab needs ALL programmes including deactivated ones
  /// (unlike the student-facing list passed in via widget.programmes,
  /// which already excludes inactive ones) - falls back to whatever was
  /// passed in if this fails, so the tab still shows something.
  Future<void> _loadAdminProgrammes() async {
    try {
      final all = await ApiService.fetchAllProgrammesForAdmin();
      if (mounted) setState(() => _displayedProgrammes = all);
    } on ApiException {
      // Keep the fallback list already set in initState.
    }
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
      await _loadFreshnessHistory();
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

  Future<void> _loadFreshnessHistory() async {
    setState(() => _isLoadingFreshnessHistory = true);
    try {
      final history = await ApiService.fetchCatalogueFreshnessHistory();
      if (mounted) setState(() {
        _freshnessHistory = history;
        _isLoadingFreshnessHistory = false;
      });
    } on ApiException {
      if (mounted) setState(() => _isLoadingFreshnessHistory = false);
    }
  }

  Future<void> _deactivateProgramme(Programme prog) async {
    try {
      await ApiService.deactivateProgramme(prog.id);
      await _loadAdminProgrammes();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Deactivated ${prog.code}')));
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not deactivate: ${e.message}'), backgroundColor: Colors.redAccent),
        );
      }
    }
  }

  Future<void> _reactivateProgramme(Programme prog) async {
    try {
      await ApiService.reactivateProgramme(prog.id);
      await _loadAdminProgrammes();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Reactivated ${prog.code}')));
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not reactivate: ${e.message}'), backgroundColor: Colors.redAccent),
        );
      }
    }
  }

  void _confirmDeactivate(Programme prog) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Deactivate programme?'),
        content: Text(
          '${prog.code} will be hidden from students and recommendations until you reactivate it. This is reversible.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
            onPressed: () {
              Navigator.pop(ctx);
              _deactivateProgramme(prog);
            },
            child: const Text('Deactivate'),
          ),
        ],
      ),
    );
  }

  Future<void> _loadAdmins() async {
    setState(() {
      _isLoadingAdmins = true;
      _adminsError = null;
    });
    try {
      final admins = await ApiService.fetchAdmins();
      if (mounted) setState(() {
        _admins = admins;
        _isLoadingAdmins = false;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() {
        _adminsError = e.message;
        _isLoadingAdmins = false;
      });
    }
  }

  Future<void> _addAdmin() async {
    final email = _addAdminController.text.trim();
    if (email.isEmpty) return;
    setState(() => _isAddingAdmin = true);
    try {
      await ApiService.addAdmin(email);
      _addAdminController.clear();
      await _loadAdmins();
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: Colors.redAccent),
        );
      }
    } finally {
      if (mounted) setState(() => _isAddingAdmin = false);
    }
  }

  Future<void> _removeAdmin(String uid, String email) async {
    try {
      await ApiService.removeAdmin(uid);
      await _loadAdmins();
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not remove: ${e.message}'), backgroundColor: Colors.redAccent),
        );
      }
    }
  }

  Future<void> _loadTrainingStatus() async {
    try {
      final status = await ApiService.fetchModelTrainingStatus();
      if (!mounted) return;
      final wasRunning = _trainingStatus['running'] == true;
      setState(() => _trainingStatus = status);
      if (status['running'] == true) {
        _trainingPollTimer ??= Timer.periodic(const Duration(seconds: 5), (_) => _loadTrainingStatus());
      } else {
        _trainingPollTimer?.cancel();
        _trainingPollTimer = null;
        if (wasRunning) {
          // A poll just caught the transition from running -> finished -
          // refresh everything a completed retrain could have changed.
          _loadModelMetrics();
          _loadModelBackups();
          _loadAuditLogs();
        }
      }
    } on ApiException {
      // Non-critical - the status banner just won't update this cycle.
    }
  }

  Future<void> _triggerRetrain() async {
    setState(() {
      _isTriggeringRetrain = true;
      _retrainMessage = null;
    });
    try {
      await ApiService.triggerModelRetrain();
      setState(() => _retrainMessage = 'Retrain started - this takes a few minutes.');
      await _loadTrainingStatus();
    } on ApiException catch (e) {
      setState(() => _retrainMessage = 'Could not start retrain: ${e.message}');
    } finally {
      if (mounted) setState(() => _isTriggeringRetrain = false);
    }
  }

  void _confirmRetrain() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Retrain the model?'),
        content: const Text(
          'This regenerates the training data and refits the model from scratch - it typically takes a '
          'few minutes and runs as a separate process so the app keeps working normally while it runs. The new '
          'model is hot-loaded automatically when it finishes.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              _triggerRetrain();
            },
            child: const Text('Start Retrain'),
          ),
        ],
      ),
    );
  }

  Future<void> _loadModelBackups() async {
    setState(() => _isLoadingBackups = true);
    try {
      final backups = await ApiService.fetchModelBackups();
      if (mounted) setState(() {
        _modelBackups = backups;
        _isLoadingBackups = false;
      });
    } on ApiException {
      if (mounted) setState(() => _isLoadingBackups = false);
    }
  }

  void _confirmRestore(Map<String, dynamic> backup) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Restore this model version?'),
        content: Text(
          'The current model will be backed up first, then replaced with the version from ${backup['timestamp']}. '
          'This is reversible - restoring again later can bring today\'s model back.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await ApiService.restoreModelBackup(backup['timestamp'] as String);
                await _loadModelMetrics();
                await _loadModelBackups();
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Model restored')));
                }
              } on ApiException catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Could not restore: ${e.message}'), backgroundColor: Colors.redAccent),
                  );
                }
              }
            },
            child: const Text('Restore'),
          ),
        ],
      ),
    );
  }

  Future<void> _loadPopularity() async {
    setState(() => _isLoadingPopularity = true);
    try {
      final popularity = await ApiService.fetchProgrammePopularity();
      if (mounted) setState(() {
        _popularity = popularity;
        _isLoadingPopularity = false;
      });
    } on ApiException {
      if (mounted) setState(() => _isLoadingPopularity = false);
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
      _buildAdminsTab(),
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
          NavigationDestination(
            icon: Icon(Icons.manage_accounts_outlined),
            selectedIcon: Icon(Icons.manage_accounts, color: Color(0xFF0EA5A4)),
            label: 'Admins',
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
                    Expanded(
                      child: Row(
                        children: const [
                          Icon(Icons.admin_panel_settings, color: Color(0xFF38BDF8), size: 20),
                          SizedBox(width: 8),
                          Flexible(
                            child: Text(
                              'Administrative Governance & Audit',
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
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
                'Model Accuracy',
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
          const SizedBox(height: 8),
          _buildFreshnessHistorySummary(context),
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
          const SizedBox(height: 10),
          TextField(
            controller: _auditSearchController,
            decoration: InputDecoration(
              hintText: 'Search by actor, action, or details...',
              prefixIcon: const Icon(Icons.search, size: 18),
              isDense: true,
              contentPadding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
            ),
            style: const TextStyle(fontSize: 13),
            onChanged: (v) => setState(() => _auditSearchQuery = v.trim().toLowerCase()),
          ),
          const SizedBox(height: 10),

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
          const SizedBox(height: 10),
          TextField(
            controller: _catalogSearchController,
            decoration: InputDecoration(
              hintText: 'Search by title, code, or faculty...',
              prefixIcon: const Icon(Icons.search, size: 18),
              isDense: true,
              contentPadding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
            ),
            style: const TextStyle(fontSize: 13),
            onChanged: (v) => setState(() => _catalogSearchQuery = v.trim().toLowerCase()),
          ),
          const SizedBox(height: 12),

          ..._filteredCatalogProgrammes.map((prog) {
            final isFlagged = _freshnessFlags.any((f) => f['programmeId'] == prog.id);
            final isInactive = !prog.isActive;
            return Opacity(
              opacity: isInactive ? 0.55 : 1.0,
              child: Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.cardBackground(context),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: isInactive ? Colors.grey.shade400 : AppColors.cardBorder(context)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Flexible(
                                child: Text(
                                  prog.title,
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.textPrimary(context)),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              if (isFlagged) ...[
                                const SizedBox(width: 4),
                                Tooltip(
                                  message: 'Flagged by catalogue freshness check - see Console tab',
                                  child: Icon(Icons.warning_amber_rounded, size: 14, color: Colors.amber.shade700),
                                ),
                              ],
                              if (isInactive) ...[
                                const SizedBox(width: 4),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                  decoration: BoxDecoration(
                                    color: Colors.grey.shade300,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: const Text('INACTIVE', style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold)),
                                ),
                              ],
                            ],
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
                            prog.cutoffRangeLabel,
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.textPrimary(context)),
                          ),
                        ),
                        if (!isInactive) ...[
                          const SizedBox(width: 6),
                          IconButton(
                            icon: const Icon(Icons.edit, size: 18, color: Color(0xFF0EA5A4)),
                            tooltip: 'Edit Programme',
                            onPressed: () => _showEditProgrammeDialog(context, prog),
                          ),
                          IconButton(
                            icon: const Icon(Icons.visibility_off_outlined, size: 18, color: Colors.redAccent),
                            tooltip: 'Deactivate Programme',
                            onPressed: () => _confirmDeactivate(prog),
                          ),
                        ] else
                          TextButton(
                            onPressed: () => _reactivateProgramme(prog),
                            child: const Text('Reactivate', style: TextStyle(fontSize: 12)),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          }).toList(),
          const SizedBox(height: 12),
        ],
      ),
    );
  }

  List<Programme> get _filteredCatalogProgrammes {
    if (_catalogSearchQuery.isEmpty) return _displayedProgrammes;
    return _displayedProgrammes.where((p) {
      final haystack = '${p.title} ${p.code} ${p.faculty}'.toLowerCase();
      return haystack.contains(_catalogSearchQuery);
    }).toList();
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
          _buildRatingSummary(context),
          const SizedBox(height: 16),

          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.cardBackground(context),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.cardBorder(context)),
            ),
            child: _buildFeedbackBody(),
          ),
          const SizedBox(height: 22),

          Text(
            'Programme Popularity',
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context)),
          ),
          const SizedBox(height: 4),
          Text(
            'Across every recommendation ever generated, among the 53 trained programmes.',
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
          ),
          const SizedBox(height: 12),
          _buildPopularitySection(context),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildRatingSummary(BuildContext context) {
    if (_studentFeedback.isEmpty) return const SizedBox.shrink();
    final ratings = _studentFeedback.map((f) => (f['rating'] as num?)?.toInt() ?? 0).where((r) => r > 0).toList();
    if (ratings.isEmpty) return const SizedBox.shrink();
    final average = ratings.reduce((a, b) => a + b) / ratings.length;
    final distribution = {for (var star = 1; star <= 5; star++) star: ratings.where((r) => r == star).length};

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.cardBackground(context),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.cardBorder(context)),
      ),
      child: Row(
        children: [
          Column(
            children: [
              Text(average.toStringAsFixed(1), style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Color(0xFFF59E0B))),
              Text('of ${ratings.length}', style: TextStyle(fontSize: 10, color: AppColors.textSecondary(context))),
            ],
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              children: [5, 4, 3, 2, 1].map((star) {
                final count = distribution[star] ?? 0;
                final fraction = ratings.isEmpty ? 0.0 : count / ratings.length;
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 1.5),
                  child: Row(
                    children: [
                      Text('$star★', style: TextStyle(fontSize: 10, color: AppColors.textSecondary(context))),
                      const SizedBox(width: 6),
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: fraction,
                            minHeight: 6,
                            backgroundColor: AppColors.chipBackground(context),
                            valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFFF59E0B)),
                          ),
                        ),
                      ),
                      const SizedBox(width: 6),
                      SizedBox(width: 18, child: Text('$count', style: TextStyle(fontSize: 10, color: AppColors.textSecondary(context)))),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPopularitySection(BuildContext context) {
    if (_isLoadingPopularity) {
      return const Center(child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0EA5A4))));
    }
    if (_popularity == null) {
      return Text('Could not load popularity data.', style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)));
    }
    final most = (_popularity!['mostRecommended'] as List? ?? []).cast<Map<String, dynamic>>();
    final least = (_popularity!['leastRecommended'] as List? ?? []).cast<Map<String, dynamic>>();

    Widget buildList(String title, List<Map<String, dynamic>> items, Color color) {
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
              Text(title, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color)),
              const SizedBox(height: 8),
              ...items.map((item) => Padding(
                    padding: const EdgeInsets.only(bottom: 6.0),
                    child: Text(
                      '${item['title']} (${item['count']})',
                      style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  )),
            ],
          ),
        ),
      );
    }

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        buildList('Most Recommended', most, const Color(0xFF0EA5A4)),
        const SizedBox(width: 10),
        buildList('Least Recommended', least, Colors.redAccent),
      ],
    );
  }

  Widget _buildAdminsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Model Management',
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context)),
          ),
          const SizedBox(height: 4),
          Text(
            'Retrain the model from scratch, or roll back to a previous version.',
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
          ),
          const SizedBox(height: 12),
          _buildModelManagementSection(context),
          const SizedBox(height: 22),

          Text(
            'Administrators',
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context)),
          ),
          const SizedBox(height: 4),
          Text(
            'Grant or revoke admin access for an existing account by email.',
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
          ),
          const SizedBox(height: 12),
          _buildAdminsSection(context),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildModelManagementSection(BuildContext context) {
    final isRunning = _trainingStatus['running'] == true;
    return Container(
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
              Expanded(
                child: Text(
                  _modelAccuracy != null
                      ? 'Current model: ${(_modelAccuracy! * 100).toStringAsFixed(1)}% accuracy'
                      : 'Current model: —',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary(context)),
                ),
              ),
              ElevatedButton.icon(
                onPressed: (isRunning || _isTriggeringRetrain) ? null : _confirmRetrain,
                icon: isRunning
                    ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.model_training, size: 16),
                label: Text(isRunning ? 'Training...' : 'Retrain Model'),
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0EA5A4), foregroundColor: Colors.white),
              ),
            ],
          ),
          if (isRunning) ...[
            const SizedBox(height: 8),
            Text(
              'Retraining is running as a separate process - this app keeps working normally and will hot-load the new model automatically when it finishes (usually a few minutes).',
              style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)),
            ),
          ],
          if (_retrainMessage != null) ...[
            const SizedBox(height: 8),
            Text(_retrainMessage!, style: const TextStyle(fontSize: 11, color: Color(0xFF0EA5A4))),
          ],
          if (_trainingStatus['lastError'] != null) ...[
            const SizedBox(height: 8),
            Text('Last retrain failed: ${_trainingStatus['lastError']}', style: const TextStyle(fontSize: 11, color: Colors.redAccent)),
          ],
          const SizedBox(height: 14),
          Text('Previous Versions', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context))),
          const SizedBox(height: 6),
          if (_isLoadingBackups)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
            )
          else if (_modelBackups.isEmpty)
            Text('No previous versions yet - they appear here after your first retrain.',
                style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)))
          else
            ..._modelBackups.map((backup) {
              final acc = (backup['accuracy'] as num?)?.toDouble();
              return Padding(
                padding: const EdgeInsets.only(bottom: 6.0),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        '${backup['timestamp']}${acc != null ? ' - ${(acc * 100).toStringAsFixed(1)}%' : ''}',
                        style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)),
                      ),
                    ),
                    TextButton(
                      onPressed: isRunning ? null : () => _confirmRestore(backup),
                      child: const Text('Restore', style: TextStyle(fontSize: 11)),
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }

  Widget _buildAdminsSection(BuildContext context) {
    return Container(
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
              Expanded(
                child: TextField(
                  controller: _addAdminController,
                  decoration: const InputDecoration(
                    hintText: 'Email of an existing account to grant admin access',
                    isDense: true,
                    border: OutlineInputBorder(),
                  ),
                  style: const TextStyle(fontSize: 13),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                onPressed: _isAddingAdmin ? null : _addAdmin,
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0EA5A4), foregroundColor: Colors.white),
                child: _isAddingAdmin
                    ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Text('Add'),
              ),
            ],
          ),
          const SizedBox(height: 14),
          if (_isLoadingAdmins)
            const Center(child: CircularProgressIndicator(strokeWidth: 2))
          else if (_adminsError != null)
            Row(
              children: [
                Expanded(child: Text('Could not load admins: $_adminsError', style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)))),
                TextButton(onPressed: _loadAdmins, child: const Text('Retry')),
              ],
            )
          else if (_admins.isEmpty)
            Text(
              'No additional admins yet - access via ADMIN_EMAILS (server config) always works and isn\'t shown here.',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
            )
          else
            ..._admins.map((admin) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 8.0),
                child: Row(
                  children: [
                    const Icon(Icons.person_outline, size: 16, color: Color(0xFF64748B)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text((admin['email'] ?? 'Unknown').toString(), style: TextStyle(fontSize: 12, color: AppColors.textPrimary(context))),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline, size: 18, color: Colors.redAccent),
                      tooltip: 'Revoke admin access',
                      onPressed: () => _removeAdmin(admin['uid'] as String, (admin['email'] ?? '').toString()),
                    ),
                  ],
                ),
              );
            }),
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

  /// Shows when the freshness check last actually ran (manual or the
  /// weekly scheduled job) and lets the admin expand a short history -
  /// without this, there's no way to tell the automation is really running
  /// over time versus having only ever registered once at server startup.
  Widget _buildFreshnessHistorySummary(BuildContext context) {
    if (_isLoadingFreshnessHistory) {
      return const SizedBox.shrink();
    }
    if (_freshnessHistory.isEmpty) {
      return Text(
        'No freshness checks have run yet.',
        style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)),
      );
    }
    final latest = _freshnessHistory.first;
    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        title: Text(
          'Last checked: ${latest['runAt'] ?? '—'} by ${latest['actor'] ?? 'unknown'} - '
          '${latest['totalFlagsFound'] ?? 0} issue(s) found',
          style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)),
        ),
        children: _freshnessHistory.skip(1).map((run) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 6.0),
            child: Text(
              '${run['runAt'] ?? '—'} by ${run['actor'] ?? 'unknown'} - '
              'checked ${run['checkedProgrammes'] ?? 0}, ${run['totalFlagsFound'] ?? 0} issue(s), '
              '${run['newlyFlagged'] ?? 0} new',
              style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)),
            ),
          );
        }).toList(),
      ),
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
    final filtered = _auditSearchQuery.isEmpty
        ? _auditLogs
        : _auditLogs.where((log) {
            final haystack = '${log['action'] ?? ''} ${log['actor'] ?? ''} ${log['details'] ?? ''}'.toLowerCase();
            return haystack.contains(_auditSearchQuery);
          }).toList();
    if (filtered.isEmpty) {
      return Text(
        'No audit log entries match "$_auditSearchQuery".',
        style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
      );
    }
    return Column(
      children: filtered.map((log) {
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
    // One (latest, previous) pair per university: students are compared with
    // each university's own cutoff, so that is what an admin edits.
    final uniControllers = <String, List<TextEditingController>>{
      for (final u in prog.offeringUniversities)
        u.kuccpsCode: [
          TextEditingController(text: u.latestCutoff.toString()),
          TextEditingController(text: u.previousCutoff.toString()),
        ],
    };
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
              const Text('Cutoff points by university', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
              const SizedBox(height: 2),
              Text(
                "Students are compared with each university's own cutoff.",
                style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
              ),
              const SizedBox(height: 10),
              for (final u in prog.offeringUniversities) ...[
                Text('${u.universityName} (${u.kuccpsCode})', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                const SizedBox(height: 6),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: uniControllers[u.kuccpsCode]![0],
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: const InputDecoration(labelText: 'Latest', border: OutlineInputBorder(), isDense: true),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: uniControllers[u.kuccpsCode]![1],
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: const InputDecoration(labelText: 'Previous', border: OutlineInputBorder(), isDense: true),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
              ],
              const SizedBox(height: 2),
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
                    final newOfferings = <UniversityOffering>[];
                    var allValid = true;
                    for (final u in prog.offeringUniversities) {
                      final latest = double.tryParse(uniControllers[u.kuccpsCode]![0].text.trim());
                      final previous = double.tryParse(uniControllers[u.kuccpsCode]![1].text.trim());
                      if (latest == null || previous == null || latest <= 0 || latest > 48 || previous <= 0 || previous > 48) {
                        allValid = false;
                        break;
                      }
                      newOfferings.add(UniversityOffering(
                        universityName: u.universityName,
                        universityType: u.universityType,
                        location: u.location,
                        latestCutoff: latest,
                        previousCutoff: previous,
                        kuccpsCode: u.kuccpsCode,
                      ));
                    }
                    if (!allValid) {
                      ScaffoldMessenger.of(ctx).showSnackBar(
                        const SnackBar(content: Text('Enter cutoffs between 0 and 48 for every university.'), backgroundColor: Colors.redAccent),
                      );
                      return;
                    }
                    final newMinGrade = minGradeController.text.trim();
                    final newDescription = descriptionController.text.trim();
                    setDialogState(() => isSaving = true);
                    try {
                      for (int i = 0; i < newOfferings.length; i++) {
                        final old = prog.offeringUniversities[i];
                        final updated = newOfferings[i];
                        if (old.latestCutoff != updated.latestCutoff || old.previousCutoff != updated.previousCutoff) {
                          await ApiService.updateUniversityCutoff(
                              prog.id, updated.kuccpsCode, updated.latestCutoff, updated.previousCutoff);
                        }
                      }
                      if (newMinGrade.isNotEmpty || newDescription.isNotEmpty) {
                        await widget.onUpdateProgramme(
                          prog.id,
                          minMeanGrade: newMinGrade.isNotEmpty ? newMinGrade : null,
                          description: newDescription.isNotEmpty ? newDescription : null,
                        );
                      }
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
                            averageCutoff: prog.averageCutoff,
                            clusterGroup: prog.clusterGroup,
                            clusterSubjects: prog.clusterSubjects,
                            minimumSubjectRequirements: prog.minimumSubjectRequirements,
                            description: newDescription.isNotEmpty ? newDescription : prog.description,
                            careerOpportunities: prog.careerOpportunities,
                            requiredSkills: prog.requiredSkills,
                            professionalCertifications: prog.professionalCertifications,
                            offeringUniversities: newOfferings,
                            durationYears: prog.durationYears,
                            status: prog.status,
                          );
                        }
                      });
                      Navigator.pop(ctx);
                      // No separate blocking "are you sure" dialog for this -
                      // the edit dialog itself (with its own visible Cancel)
                      // already requires an explicit confirm tap. Undo here
                      // is the more useful safety net: it re-submits exactly
                      // the pre-edit values via the same update path.
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('Updated ${prog.code}'),
                          action: SnackBarAction(
                            label: 'Undo',
                            onPressed: () async {
                              try {
                                for (final old in prog.offeringUniversities) {
                                  await ApiService.updateUniversityCutoff(
                                      prog.id, old.kuccpsCode, old.latestCutoff, old.previousCutoff);
                                }
                                await widget.onUpdateProgramme(
                                  prog.id,
                                  minMeanGrade: prog.minMeanGrade,
                                  description: prog.description,
                                );
                                if (!mounted) return;
                                setState(() {
                                  final idx = _displayedProgrammes.indexWhere((p) => p.id == prog.id);
                                  if (idx != -1) _displayedProgrammes[idx] = prog;
                                });
                                _loadAuditLogs();
                              } on ApiException catch (e) {
                                if (!mounted) return;
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text('Could not undo: ${e.message}'), backgroundColor: Colors.redAccent),
                                );
                              }
                            },
                          ),
                        ),
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
