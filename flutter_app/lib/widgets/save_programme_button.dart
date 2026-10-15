import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/programme.dart';
import '../services/shortlist_controller.dart';
import '../theme/app_colors.dart';

/// Bookmark toggle that saves a programme to (or removes it from) the
/// student's shortlist. Used on recommendation cards, the programme page and
/// the catalogue.
class SaveProgrammeButton extends StatelessWidget {
  final Programme programme;
  final Color? unsavedColor;

  const SaveProgrammeButton({Key? key, required this.programme, this.unsavedColor}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final saved = context.select<ShortlistController, bool>((c) => c.isSaved(programme.id));
    return IconButton(
      icon: Icon(
        saved ? Icons.bookmark : Icons.bookmark_border,
        color: saved ? AppColors.accentTeal : (unsavedColor ?? AppColors.textSecondary(context)),
      ),
      tooltip: saved ? 'Remove from saved programmes' : 'Save this programme',
      onPressed: () async {
        final messenger = ScaffoldMessenger.of(context);
        final error = await context.read<ShortlistController>().toggle(programme);
        messenger.hideCurrentSnackBar();
        messenger.showSnackBar(SnackBar(
          content: Text(error ?? (saved ? 'Removed from your saved programmes' : 'Saved - find it in the Saved tab')),
          duration: const Duration(seconds: 2),
        ));
      },
    );
  }
}
