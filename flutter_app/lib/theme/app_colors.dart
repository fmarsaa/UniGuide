import 'package:flutter/material.dart';

/// Semantic colors that adapt to light/dark mode. Call these instead of
/// hardcoding hex literals in screen widgets.
class AppColors {
  static bool isDark(BuildContext context) => Theme.of(context).brightness == Brightness.dark;

  static Color scaffoldBackground(BuildContext context) =>
      isDark(context) ? const Color(0xFF0F172A) : const Color(0xFFF1F5F9);
  static Color cardBackground(BuildContext context) =>
      isDark(context) ? const Color(0xFF1E293B) : Colors.white;
  static Color cardBorder(BuildContext context) =>
      isDark(context) ? const Color(0xFF334155) : const Color(0xFFE2E8F0);
  static Color textPrimary(BuildContext context) =>
      isDark(context) ? Colors.white : const Color(0xFF0F172A);
  static Color textSecondary(BuildContext context) =>
      isDark(context) ? const Color(0xFF94A3B8) : const Color(0xFF64748B);

  // A slightly lighter chip/pill background sitting on top of a card -
  // e.g. the cutoff-points pill in the admin catalog list.
  static Color chipBackground(BuildContext context) =>
      isDark(context) ? const Color(0xFF334155) : const Color(0xFFF1F5F9);

  // Brand accent - same in both modes, it already has enough contrast.
  static const Color accentTeal = Color(0xFF0EA5A4);
}
