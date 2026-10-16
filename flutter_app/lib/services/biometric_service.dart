import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:local_auth/local_auth.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Fingerprint / face unlock for the phone app.
///
/// This is an app lock layered on top of the normal sign-in, not a replacement
/// for it: the student still signs in with their email and password. After that
/// they can choose to have UniGuide ask for their fingerprint or face (whichever
/// the phone has enrolled) when the app opens or comes back from the background.
/// Choosing "use password instead" signs them out, so the lock can never be a
/// way around the real sign-in. Nothing biometric ever leaves the phone - the
/// operating system only tells the app "yes" or "no".
class BiometricService {
  BiometricService._();

  static final LocalAuthentication _auth = LocalAuthentication();
  static const String _enabledPrefix = 'biometric_unlock_enabled_';
  static const String _askedPrefix = 'biometric_unlock_asked_';

  /// True only on a phone that has a fingerprint or face enrolled. Never on the
  /// web portal, which has no biometric lock.
  static Future<bool> isAvailable() async {
    if (kIsWeb) return false;
    try {
      if (!await _auth.canCheckBiometrics) return false;
      final enrolled = await _auth.getAvailableBiometrics();
      return enrolled.isNotEmpty;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> isEnabled(String uid) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getBool('$_enabledPrefix$uid') ?? false;
    } catch (_) {
      return false;
    }
  }

  static Future<void> setEnabled(String uid, bool enabled) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('$_enabledPrefix$uid', enabled);
  }

  /// Whether we have already offered biometric unlock to this student, so the
  /// offer is made once and not on every launch.
  static Future<bool> wasOffered(String uid) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getBool('$_askedPrefix$uid') ?? false;
    } catch (_) {
      return true; // if storage is unavailable, do not nag
    }
  }

  static Future<void> markOffered(String uid) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('$_askedPrefix$uid', true);
    } catch (_) {}
  }

  /// Shows the phone's own fingerprint/face prompt. Returns true only if the
  /// person was recognised; cancelling, a failed scan or any error is false.
  static Future<bool> authenticate({String reason = 'Unlock UniGuide'}) async {
    try {
      return await _auth.authenticate(
        localizedReason: reason,
        biometricOnly: true,
        persistAcrossBackgrounding: true,
      );
    } on LocalAuthException {
      return false;
    } catch (_) {
      return false;
    }
  }
}
