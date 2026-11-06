import 'package:flutter/material.dart';

import '../services/api_service.dart';

/// Lets the user type the UniGuide server address, check it answers, and save it on
/// the phone. Leaving the field empty and saving restores the address the app was
/// built with.
class ServerAddressDialog extends StatefulWidget {
  const ServerAddressDialog({Key? key}) : super(key: key);

  static Future<void> show(BuildContext context) {
    return showDialog(
        context: context, builder: (_) => const ServerAddressDialog());
  }

  @override
  State<ServerAddressDialog> createState() => _ServerAddressDialogState();
}

class _ServerAddressDialogState extends State<ServerAddressDialog> {
  late final TextEditingController _controller =
      TextEditingController(text: ApiService.baseUrl);
  bool _testing = false;
  String? _result;
  bool _reachable = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _test() async {
    setState(() {
      _testing = true;
      _result = null;
    });
    final ok = await ApiService.testConnection(_controller.text);
    if (!mounted) return;
    setState(() {
      _testing = false;
      _reachable = ok;
      _result = ok
          ? 'OK - the server answered.'
          : 'Not reachable. Check the address and the Wi-Fi connection.';
    });
  }

  Future<void> _save() async {
    await ApiService.saveBaseUrl(_controller.text);
    if (!mounted) return;
    Navigator.of(context).pop();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Server address set to ${ApiService.baseUrl}')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Server address'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            controller: _controller,
            keyboardType: TextInputType.url,
            autocorrect: false,
            decoration: const InputDecoration(
              labelText: 'Address',
              hintText: 'http://192.168.43.10:8000',
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Built-in address: ${ApiService.defaultBaseUrl}. Save an empty field to go back to it.',
            style: const TextStyle(fontSize: 12),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _testing ? null : _test,
            icon: _testing
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.wifi_tethering),
            label: const Text('Test connection'),
          ),
          if (_result != null) ...[
            const SizedBox(height: 8),
            Text(
              _result!,
              style: TextStyle(
                  color:
                      _reachable ? Colors.green.shade700 : Colors.red.shade700),
            ),
          ],
        ],
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel')),
        ElevatedButton(onPressed: _save, child: const Text('Save')),
      ],
    );
  }
}
