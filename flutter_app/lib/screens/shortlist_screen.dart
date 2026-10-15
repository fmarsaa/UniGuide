import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/programme.dart';
import '../services/shortlist_controller.dart';
import '../theme/app_colors.dart';
import '../widgets/save_programme_button.dart';
import 'compare_screen.dart';
import 'programme_detail_screen.dart';

/// "Saved" tab: the programmes a student bookmarked, with a side-by-side
/// comparison of two or three of them.
class ShortlistScreen extends StatefulWidget {
  const ShortlistScreen({Key? key}) : super(key: key);

  @override
  State<ShortlistScreen> createState() => _ShortlistScreenState();
}

class _ShortlistScreenState extends State<ShortlistScreen> {
  static const int _maxCompare = 3;
  final Set<String> _selected = <String>{};

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<ShortlistController>();
    final items = controller.items;
    // Drop selections for programmes that were removed in the meantime.
    _selected.removeWhere((id) => !items.any((p) => p.id == id));

    Widget body;
    if (controller.isLoading && items.isEmpty) {
      body = const Center(child: CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(AppColors.accentTeal)));
    } else if (controller.error != null && items.isEmpty) {
      body = _message(
        context,
        icon: Icons.cloud_off,
        title: 'Could not load your saved programmes',
        detail: controller.error!,
        action: ElevatedButton.icon(
          onPressed: controller.load,
          icon: const Icon(Icons.refresh),
          label: const Text('Retry'),
        ),
      );
    } else if (items.isEmpty) {
      body = _message(
        context,
        icon: Icons.bookmark_border,
        title: 'Nothing saved yet',
        detail: 'Tap the bookmark on any programme to keep it here, then compare your favourites side by side.',
      );
    } else {
      body = ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
        children: [
          Text(
            'Select 2 or 3 programmes to compare them side by side.',
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
          ),
          const SizedBox(height: 12),
          for (final programme in items) _card(context, programme),
        ],
      );
    }

    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground(context),
      body: body,
      floatingActionButton: items.length >= 2
          ? FloatingActionButton.extended(
              onPressed: _selected.length >= 2
                  ? () {
                      final chosen = items.where((p) => _selected.contains(p.id)).toList();
                      Navigator.push(context, MaterialPageRoute(builder: (_) => CompareScreen(programmes: chosen)));
                    }
                  : null,
              backgroundColor: _selected.length >= 2 ? AppColors.accentTeal : AppColors.chipBackground(context),
              foregroundColor: _selected.length >= 2 ? Colors.white : AppColors.textSecondary(context),
              icon: const Icon(Icons.compare_arrows),
              label: Text(_selected.length >= 2 ? 'Compare ${_selected.length}' : 'Select 2 to compare'),
            )
          : null,
    );
  }

  Widget _card(BuildContext context, Programme programme) {
    final isSelected = _selected.contains(programme.id);
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.cardBackground(context),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: isSelected ? AppColors.accentTeal : AppColors.cardBorder(context), width: isSelected ? 2 : 1),
      ),
      child: Row(
        children: [
          Checkbox(
            value: isSelected,
            activeColor: AppColors.accentTeal,
            onChanged: (checked) {
              if (checked == true && _selected.length >= _maxCompare) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('You can compare up to 3 programmes at a time.')),
                );
                return;
              }
              setState(() => checked == true ? _selected.add(programme.id) : _selected.remove(programme.id));
            },
          ),
          Expanded(
            child: InkWell(
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => ProgrammeDetailScreen(programme: programme)),
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      programme.title,
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.textPrimary(context)),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${programme.code} • ${programme.durationYears} years',
                      style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Cutoff: ${programme.cutoffRangeLabel}',
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.accentTeal),
                    ),
                  ],
                ),
              ),
            ),
          ),
          SaveProgrammeButton(programme: programme),
        ],
      ),
    );
  }

  Widget _message(BuildContext context, {required IconData icon, required String title, required String detail, Widget? action}) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 48, color: AppColors.accentTeal),
            const SizedBox(height: 12),
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppColors.textPrimary(context)),
            ),
            const SizedBox(height: 6),
            Text(
              detail,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context), height: 1.4),
            ),
            if (action != null) ...[const SizedBox(height: 16), action],
          ],
        ),
      ),
    );
  }
}
