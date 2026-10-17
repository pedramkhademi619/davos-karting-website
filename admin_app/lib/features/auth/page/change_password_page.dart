import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";

class ChangePasswordPage extends StatefulWidget {
  const ChangePasswordPage({super.key});

  @override
  State<ChangePasswordPage> createState() => _ChangePasswordPageState();
}

class _ChangePasswordPageState extends State<ChangePasswordPage> {
  final _current = TextEditingController();
  final _next = TextEditingController();
  final _repeat = TextEditingController();
  bool _busy = false;
  String? _message;
  bool _isError = false;

  @override
  void dispose() {
    _current.dispose();
    _next.dispose();
    _repeat.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_next.text != _repeat.text) {
      setState(() {
        _message = "رمز جدید و تکرار آن یکسان نیستند.";
        _isError = true;
      });
      return;
    }
    setState(() {
      _busy = true;
      _message = null;
    });
    try {
      await ApiService().changePassword(_current.text, _next.text);
      _current.clear();
      _next.clear();
      _repeat.clear();
      setState(() {
        _message = "رمز عبور تغییر کرد.";
        _isError = false;
      });
    } catch (e) {
      setState(() {
        _message = errorMessage(e);
        _isError = true;
      });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("تغییر رمز عبور"), leading: const BackButton()),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_message != null) MessageBar(_message!, error: _isError),
          LabeledField(label: "رمز عبور فعلی", controller: _current, password: true),
          LabeledField(label: "رمز عبور جدید", controller: _next, password: true),
          LabeledField(label: "تکرار رمز جدید", controller: _repeat, password: true),
          const SizedBox(height: 8),
          AppButton(label: "ذخیره", onPressed: _save, busy: _busy),
          TextButton(onPressed: Get.back, child: const Text("بازگشت")),
        ],
      ),
    );
  }
}
