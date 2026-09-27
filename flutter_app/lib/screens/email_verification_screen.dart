import 'dart:async';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

/// Shown when a signed-in user hasn't verified their email yet. Blocks
/// access to the rest of the app until verification completes (the backend
/// also enforces this independently - see require_auth in main.py - so this
/// screen is about UX, not the only line of defense).
class EmailVerificationScreen extends StatefulWidget {
  final User user;
  final VoidCallback onVerified;
  final VoidCallback onSignOut;

  const EmailVerificationScreen({
    Key? key,
    required this.user,
    required this.onVerified,
    required this.onSignOut,
  }) : super(key: key);

  @override
  State<EmailVerificationScreen> createState() => _EmailVerificationScreenState();
}

class _EmailVerificationScreenState extends State<EmailVerificationScreen> {
  Timer? _pollTimer;
  bool _isChecking = false;
  bool _isResending = false;
  String? _message;

  @override
  void initState() {
    super.initState();
    // Auto-check every 4 seconds so the user doesn't have to tap "I've
    // verified" themselves if they click the email link on another device.
    _pollTimer = Timer.periodic(const Duration(seconds: 4), (_) => _checkVerified(silent: true));
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _checkVerified({bool silent = false}) async {
    if (_isChecking) return;
    setState(() => _isChecking = true);
    try {
      await widget.user.reload();
      final refreshed = FirebaseAuth.instance.currentUser;
      if (refreshed != null && refreshed.emailVerified) {
        _pollTimer?.cancel();
        // reload() only updates the local profile flag - the cached ID token
        // sent to the backend still carries the old email_verified: false
        // claim until forced. Without this, every backend call 403s until
        // the token naturally expires (~1hr).
        await refreshed.getIdToken(true);
        widget.onVerified();
        return;
      }
      if (!silent) {
        setState(() => _message = 'Not verified yet - check your inbox (and spam folder) and click the link.');
      }
    } catch (_) {
      if (!silent) {
        setState(() => _message = 'Could not check verification status. Try again.');
      }
    } finally {
      if (mounted) setState(() => _isChecking = false);
    }
  }

  Future<void> _resendEmail() async {
    setState(() {
      _isResending = true;
      _message = null;
    });
    try {
      await widget.user.sendEmailVerification();
      setState(() => _message = 'Verification email sent to ${widget.user.email}.');
    } on FirebaseAuthException catch (e) {
      setState(() => _message = e.code == 'too-many-requests'
          ? 'Too many requests - please wait a bit before resending.'
          : (e.message ?? 'Could not resend the email.'));
    } catch (_) {
      setState(() => _message = 'Could not resend the email.');
    } finally {
      if (mounted) setState(() => _isResending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF14213D),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 28.0, vertical: 24.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 76,
                  height: 76,
                  decoration: BoxDecoration(
                    color: const Color(0xFF0EA5A4).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(22),
                    border: Border.all(color: const Color(0xFF0EA5A4).withOpacity(0.4), width: 1.5),
                  ),
                  child: const Icon(Icons.mark_email_unread_outlined, size: 38, color: Color(0xFF2DD4BF)),
                ),
                const SizedBox(height: 20),
                const Text(
                  'Verify Your Email',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 10),
                Text(
                  'We sent a verification link to\n${widget.user.email}\n\nOpen it, then come back here.',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13, height: 1.5),
                ),
                const SizedBox(height: 24),
                if (_message != null) ...[
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0EA5A4).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: const Color(0xFF0EA5A4).withOpacity(0.3)),
                    ),
                    child: Text(_message!, style: const TextStyle(color: Color(0xFF2DD4BF), fontSize: 12), textAlign: TextAlign.center),
                  ),
                  const SizedBox(height: 16),
                ],
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton.icon(
                    onPressed: _isChecking ? null : () => _checkVerified(),
                    icon: _isChecking
                        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : const Icon(Icons.refresh, size: 18),
                    label: const Text("I've verified - Continue"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0EA5A4),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                TextButton(
                  onPressed: _isResending ? null : _resendEmail,
                  child: Text(
                    _isResending ? 'Sending...' : 'Resend verification email',
                    style: const TextStyle(color: Color(0xFF94A3B8)),
                  ),
                ),
                TextButton(
                  onPressed: widget.onSignOut,
                  child: const Text('Sign out', style: TextStyle(color: Colors.white54)),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
