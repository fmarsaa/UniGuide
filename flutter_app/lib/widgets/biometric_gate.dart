import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import '../services/biometric_service.dart';
import '../theme/app_colors.dart';

/// Wraps the signed-in part of the app. If the student turned on biometric unlock,
/// it shows a lock screen and asks for their fingerprint or face before showing
/// [child] - when the app opens, and again when it returns from the background
/// after [_relockAfter]. If they have not been offered it yet, it offers it once.
class BiometricGate extends StatefulWidget {
  final User user;
  final Widget child;

  const BiometricGate({Key? key, required this.user, required this.child})
      : super(key: key);

  @override
  State<BiometricGate> createState() => _BiometricGateState();
}

class _BiometricGateState extends State<BiometricGate>
    with WidgetsBindingObserver {
  static const Duration _relockAfter = Duration(seconds: 30);

  bool _checking = true;
  bool _locked = false;
  bool _prompting = false;
  DateTime? _leftAt;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _start();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  Future<void> _start() async {
    final available = await BiometricService.isAvailable();
    final enabled =
        available && await BiometricService.isEnabled(widget.user.uid);
    if (!mounted) return;
    setState(() {
      _checking = false;
      _locked = enabled;
    });
    if (enabled) {
      _unlock();
    } else if (available) {
      _offerOnce();
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused) {
      _leftAt = DateTime.now();
    } else if (state == AppLifecycleState.resumed) {
      final left = _leftAt;
      _leftAt = null;
      if (left != null &&
          DateTime.now().difference(left) > _relockAfter &&
          !_locked &&
          !_prompting) {
        _relockIfEnabled();
      }
    }
  }

  Future<void> _relockIfEnabled() async {
    if (!await BiometricService.isEnabled(widget.user.uid) ||
        !await BiometricService.isAvailable()) return;
    if (!mounted) return;
    setState(() => _locked = true);
    _unlock();
  }

  Future<void> _unlock() async {
    if (_prompting) return;
    _prompting = true;
    final ok = await BiometricService.authenticate(reason: 'Unlock UniGuide');
    _prompting = false;
    if (!mounted) return;
    if (ok) setState(() => _locked = false);
  }

  Future<void> _offerOnce() async {
    if (await BiometricService.wasOffered(widget.user.uid)) return;
    await BiometricService.markOffered(widget.user.uid);
    if (!mounted) return;
    final wantsIt = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Unlock with your fingerprint or face?'),
        content: const Text(
          'You can use your phone\'s fingerprint or face unlock to open UniGuide instead of typing your password each time. '
          'You can switch this off any time from the fingerprint icon at the top.',
          style: TextStyle(fontSize: 13, height: 1.4),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Not now')),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.accentTeal,
                foregroundColor: Colors.white),
            child: const Text('Turn on'),
          ),
        ],
      ),
    );
    if (wantsIt == true) {
      // Confirm it works before switching it on, so nobody gets locked into a lock they cannot open.
      final ok = await BiometricService.authenticate(
          reason: 'Confirm to turn on biometric unlock');
      if (ok) await BiometricService.setEnabled(widget.user.uid, true);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(ok
              ? 'Biometric unlock is on'
              : 'Biometric unlock was not turned on'),
        ));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_checking) {
      return Scaffold(
        backgroundColor: AppColors.scaffoldBackground(context),
        body: const Center(
          child: CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(AppColors.accentTeal)),
        ),
      );
    }
    if (!_locked) return widget.child;

    return Scaffold(
      backgroundColor: const Color(0xFF14213D),
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 380),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.lock_outline,
                      size: 54, color: AppColors.accentTeal),
                  const SizedBox(height: 16),
                  const Text(
                    'UniGuide is locked',
                    style: TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Use your fingerprint or face to continue.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    onPressed: _unlock,
                    icon: const Icon(Icons.fingerprint),
                    label: const Text('Unlock'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.accentTeal,
                      foregroundColor: Colors.white,
                      minimumSize: const Size(200, 48),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextButton(
                    // Signing out is the only other way in, so the lock can never be bypassed.
                    onPressed: () => FirebaseAuth.instance.signOut(),
                    child: const Text('Sign in with password instead',
                        style: TextStyle(color: Colors.white70)),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Fingerprint icon for the top bar: switches biometric unlock on or off.
/// Hidden on the web and on phones with no fingerprint or face enrolled.
class BiometricToggleButton extends StatefulWidget {
  const BiometricToggleButton({Key? key}) : super(key: key);

  @override
  State<BiometricToggleButton> createState() => _BiometricToggleButtonState();
}

class _BiometricToggleButtonState extends State<BiometricToggleButton> {
  bool _available = false;
  bool _enabled = false;

  String? get _uid => FirebaseAuth.instance.currentUser?.uid;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final uid = _uid;
    if (uid == null) return;
    final available = await BiometricService.isAvailable();
    final enabled = available && await BiometricService.isEnabled(uid);
    if (mounted)
      setState(() {
        _available = available;
        _enabled = enabled;
      });
  }

  Future<void> _toggle() async {
    final uid = _uid;
    if (uid == null) return;
    final messenger = ScaffoldMessenger.of(context);
    if (_enabled) {
      await BiometricService.setEnabled(uid, false);
      if (mounted) setState(() => _enabled = false);
      messenger.showSnackBar(
          const SnackBar(content: Text('Biometric unlock is off')));
      return;
    }
    final ok = await BiometricService.authenticate(
        reason: 'Confirm to turn on biometric unlock');
    if (ok) await BiometricService.setEnabled(uid, true);
    if (mounted) setState(() => _enabled = ok);
    messenger.showSnackBar(SnackBar(
        content: Text(ok
            ? 'Biometric unlock is on'
            : 'Biometric unlock was not turned on')));
  }

  @override
  Widget build(BuildContext context) {
    if (!_available) return const SizedBox.shrink();
    return IconButton(
      icon: Icon(Icons.fingerprint,
          size: 22, color: _enabled ? AppColors.accentTeal : null),
      tooltip:
          _enabled ? 'Turn off biometric unlock' : 'Turn on biometric unlock',
      onPressed: _toggle,
    );
  }
}
