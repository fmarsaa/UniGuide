import 'dart:math';

import 'package:flutter/material.dart';
import '../models/profile_option_groups.dart';
import '../theme/app_colors.dart';

/// Chip picker for a long option list: collapsible headings, a search box and
/// a "your picks" row. Presentation only - the option strings are what the
/// trained model knows, so this never renames or filters what is stored.
///
/// The screen is for undecided students, so by default the order of headings
/// and of options inside each heading is shuffled once per student (and kept
/// stable while they fill the screen in) - no option gets a permanent
/// first-position advantage. A group whose name is empty is shown without a
/// heading, always open.
class GroupedOptionPicker extends StatefulWidget {
  final Map<String, List<String>> groups;
  final List<String> selected;
  final ValueChanged<String> onToggle;
  final String searchHint;
  final bool shuffle;

  const GroupedOptionPicker({
    Key? key,
    required this.groups,
    required this.selected,
    required this.onToggle,
    required this.searchHint,
    this.shuffle = true,
  }) : super(key: key);

  @override
  State<GroupedOptionPicker> createState() => _GroupedOptionPickerState();
}

class _GroupedOptionPickerState extends State<GroupedOptionPicker> {
  final TextEditingController _search = TextEditingController();
  final Set<String> _open = <String>{};
  late final Map<String, List<String>> _groups;
  String _query = '';

  @override
  void initState() {
    super.initState();
    _groups = widget.shuffle ? _shuffled(widget.groups) : widget.groups;
    // Re-opening the screen with a saved profile: show the groups that already
    // hold a pick instead of making the student hunt for them.
    for (final entry in _groups.entries) {
      if (entry.value.any(widget.selected.contains)) _open.add(entry.key);
    }
  }

  static Map<String, List<String>> _shuffled(Map<String, List<String>> groups) {
    final rng = Random();
    final movable = groups.entries.where((e) => !kPinnedLastGroups.contains(e.key)).toList()..shuffle(rng);
    final pinned = groups.entries.where((e) => kPinnedLastGroups.contains(e.key));
    return {
      for (final e in [...movable, ...pinned]) e.key: (List<String>.of(e.value)..shuffle(rng)),
    };
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final q = _query.trim().toLowerCase();
    final groupWidgets = <Widget>[];
    for (final entry in _groups.entries) {
      final items = q.isEmpty ? entry.value : entry.value.where((o) => o.toLowerCase().contains(q)).toList();
      if (items.isEmpty) continue;
      groupWidgets.add(_buildGroup(context, entry.key, entry.value, items, forceOpen: q.isNotEmpty));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: _search,
          onChanged: (v) => setState(() => _query = v),
          style: TextStyle(fontSize: 13, color: AppColors.textPrimary(context)),
          decoration: InputDecoration(
            hintText: widget.searchHint,
            hintStyle: TextStyle(fontSize: 13, color: AppColors.textSecondary(context)),
            prefixIcon: const Icon(Icons.search, size: 20),
            suffixIcon: _query.isEmpty
                ? null
                : IconButton(
                    icon: const Icon(Icons.close, size: 18),
                    onPressed: () {
                      _search.clear();
                      setState(() => _query = '');
                    },
                  ),
            isDense: true,
            filled: true,
            fillColor: AppColors.cardBackground(context),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: AppColors.cardBorder(context)),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: AppColors.cardBorder(context)),
            ),
          ),
        ),
        if (widget.selected.isNotEmpty) ...[
          const SizedBox(height: 14),
          Text(
            'Your picks (${widget.selected.length})',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.textSecondary(context)),
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              for (final s in widget.selected)
                InputChip(
                  label: Text(s, style: const TextStyle(fontSize: 11, color: Colors.white)),
                  backgroundColor: AppColors.accentTeal,
                  deleteIconColor: Colors.white,
                  side: BorderSide.none,
                  visualDensity: VisualDensity.compact,
                  onDeleted: () => widget.onToggle(s),
                ),
            ],
          ),
        ],
        const SizedBox(height: 12),
        if (groupWidgets.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Text(
              'Nothing matches "$_query".',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)),
            ),
          )
        else
          ...groupWidgets,
      ],
    );
  }

  Widget _buildGroup(BuildContext context, String name, List<String> all, List<String> items, {required bool forceOpen}) {
    final isOpen = forceOpen || name.isEmpty || _open.contains(name);
    final pickedHere = all.where(widget.selected.contains).length;

    if (name.isEmpty) {
      return Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [for (final o in items) _chip(context, o)],
      );
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: AppColors.cardBackground(context),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: pickedHere > 0 ? AppColors.accentTeal : AppColors.cardBorder(context)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: forceOpen
                ? null
                : () => setState(() {
                      if (!_open.add(name)) _open.remove(name);
                    }),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      name,
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.textPrimary(context)),
                    ),
                  ),
                  if (pickedHere > 0)
                    Container(
                      margin: const EdgeInsets.only(right: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppColors.accentTeal,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        '$pickedHere',
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                    ),
                  Text(
                    '${all.length}',
                    style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)),
                  ),
                  const SizedBox(width: 4),
                  Icon(
                    isOpen ? Icons.expand_less : Icons.expand_more,
                    size: 20,
                    color: AppColors.textSecondary(context),
                  ),
                ],
              ),
            ),
          ),
          if (isOpen)
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [for (final o in items) _chip(context, o)],
              ),
            ),
        ],
      ),
    );
  }

  Widget _chip(BuildContext context, String option) => OptionChip(
        label: option,
        selected: widget.selected.contains(option),
        onTap: () => widget.onToggle(option),
      );
}

/// Plain, ungrouped chip list - for short lists like personal strengths.
class FlatOptionChips extends StatelessWidget {
  final List<String> options;
  final List<String> selected;
  final ValueChanged<String> onToggle;

  const FlatOptionChips({Key? key, required this.options, required this.selected, required this.onToggle})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final o in options) OptionChip(label: o, selected: selected.contains(o), onTap: () => onToggle(o)),
      ],
    );
  }
}

/// One selectable chip, styled identically wherever options are picked.
class OptionChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const OptionChip({Key? key, required this.label, required this.selected, required this.onTap}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return FilterChip(
      label: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
          color: selected ? Colors.white : AppColors.textPrimary(context),
        ),
      ),
      selected: selected,
      selectedColor: AppColors.accentTeal,
      backgroundColor: AppColors.cardBackground(context),
      checkmarkColor: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(color: selected ? AppColors.accentTeal : AppColors.cardBorder(context)),
      ),
      onSelected: (_) => onTap(),
    );
  }
}
