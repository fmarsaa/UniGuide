import 'dart:convert';

import 'package:share_plus/share_plus.dart';

/// Opens the phone's share sheet with [content] as a file, so the user can save it
/// to Drive or Files, or send it by email or WhatsApp.
Future<void> saveTextFile(String filename, String content,
    {String mimeType = 'text/csv'}) async {
  await SharePlus.instance.share(
    ShareParams(
      files: [
        XFile.fromData(utf8.encode(content), name: filename, mimeType: mimeType)
      ],
      fileNameOverrides: [filename],
    ),
  );
}
