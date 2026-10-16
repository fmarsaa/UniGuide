import 'dart:js_interop';

import 'package:web/web.dart' as web;

/// Downloads [content] straight to the browser's downloads folder.
/// A leading byte-order mark makes Excel read accented characters correctly.
Future<void> saveTextFile(String filename, String content,
    {String mimeType = 'text/csv'}) async {
  final blob = web.Blob(
    <JSAny>['﻿$content'.toJS].toJS,
    web.BlobPropertyBag(type: '$mimeType;charset=utf-8'),
  );
  final url = web.URL.createObjectURL(blob);
  final anchor = web.HTMLAnchorElement()
    ..href = url
    ..download = filename
    ..style.display = 'none';
  web.document.body!.append(anchor);
  anchor.click();
  anchor.remove();
  web.URL.revokeObjectURL(url);
}
