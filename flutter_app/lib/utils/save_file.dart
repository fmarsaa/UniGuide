// Saves a text file for the user: a direct download in the web portal, the phone's
// share sheet on Android. Picked at build time so neither platform compiles the
// other's code.
export 'save_file_stub.dart'
    if (dart.library.js_interop) 'save_file_web.dart'
    if (dart.library.io) 'save_file_io.dart';
