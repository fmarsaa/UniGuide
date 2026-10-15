import 'package:flutter/foundation.dart';
import '../models/programme.dart';
import 'api_service.dart';

/// The student's saved ("shortlisted") programmes. Lives at app level so the
/// bookmark button on a recommendation card, the programme page and the
/// catalogue all show the same saved state. Saves go to the backend, so a
/// shortlist follows the student's account across sessions.
class ShortlistController extends ChangeNotifier {
  List<Programme> _items = [];
  bool _loading = false;
  String? _error;

  List<Programme> get items => List.unmodifiable(_items);
  bool get isLoading => _loading;
  String? get error => _error;

  bool isSaved(String programmeId) => _items.any((p) => p.id == programmeId);

  Future<void> load() async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      _items = await ApiService.fetchShortlist();
    } on ApiException catch (e) {
      _error = e.message;
    }
    _loading = false;
    notifyListeners();
  }

  /// Saves or removes [programme]. Updates the screen immediately and rolls
  /// back if the server refuses. Returns an error message, or null on success.
  Future<String?> toggle(Programme programme) async {
    final wasSaved = isSaved(programme.id);
    _items = wasSaved
        ? _items.where((p) => p.id != programme.id).toList()
        : [..._items, programme];
    notifyListeners();
    try {
      if (wasSaved) {
        await ApiService.removeFromShortlist(programme.id);
      } else {
        await ApiService.addToShortlist(programme.id);
      }
      return null;
    } on ApiException catch (e) {
      _items = wasSaved
          ? [..._items, programme]
          : _items.where((p) => p.id != programme.id).toList();
      notifyListeners();
      return e.message;
    }
  }
}
