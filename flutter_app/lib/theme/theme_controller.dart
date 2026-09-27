import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Holds the app's current [ThemeMode] and persists the user's choice
/// across launches via [SharedPreferences] (key "theme_mode" ->
/// "light"/"dark"/"system").
///
/// Call [load] once at startup - it runs asynchronously and calls
/// [notifyListeners] when the saved preference (if any) has been read, so
/// it never blocks app startup. Until then the app simply renders with the
/// default [ThemeMode.system].
class ThemeController extends ChangeNotifier {
  static const String _prefsKey = 'theme_mode';

  ThemeMode _mode = ThemeMode.system;

  ThemeMode get mode => _mode;

  Future<void> load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString(_prefsKey);
      switch (saved) {
        case 'light':
          _mode = ThemeMode.light;
          break;
        case 'dark':
          _mode = ThemeMode.dark;
          break;
        default:
          _mode = ThemeMode.system;
      }
      notifyListeners();
    } catch (_) {
      // Non-critical: keeps ThemeMode.system if preferences aren't readable.
    }
  }

  /// Flips between light and dark. If the mode is currently `system`, the
  /// platform's current brightness is resolved first so the toggle flips to
  /// the *opposite* of whatever is currently showing.
  Future<void> toggle() async {
    final ThemeMode next;
    if (_mode == ThemeMode.system) {
      final platformBrightness = WidgetsBinding.instance.platformDispatcher.platformBrightness;
      next = platformBrightness == Brightness.dark ? ThemeMode.light : ThemeMode.dark;
    } else {
      next = _mode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    }
    _mode = next;
    notifyListeners();

    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefsKey, next == ThemeMode.dark ? 'dark' : 'light');
    } catch (_) {
      // Non-critical: the toggle still works this session, it just won't
      // be remembered on the next launch.
    }
  }
}
