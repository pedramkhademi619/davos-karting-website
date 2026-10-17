import "dart:math" as math;

import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/constants/named_routs.dart";
import "package:davos_admin/core/constants/urls.dart";
import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/services/storage_service/storage_service.dart";
import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/features/auth/controller/session_controller.dart";
import "package:davos_admin/shared/widgets/app_button.dart";

/// The sign-in: always dark, with a kart circuit being driven in the background.
class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> with SingleTickerProviderStateMixin {
  final TextEditingController _username = TextEditingController(text: StorageService().readLastUsername());
  final TextEditingController _password = TextEditingController();
  late final AnimationController _lap = AnimationController(vsync: this, duration: const Duration(seconds: 7))..repeat();
  bool _busy = false;
  bool _show = false;
  String? _error;

  @override
  void dispose() {
    _lap.dispose();
    _username.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_username.text.trim().isEmpty || _password.text.isEmpty) {
      setState(() => _error = "نام کاربری و رمز عبور را وارد کنید.");
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await Get.find<SessionController>().signIn(_username.text, _password.text);
      Get.offAllNamed(NamedRouts.home);
    } catch (e) {
      if (mounted) setState(() => _error = errorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  InputDecoration _decoration(String hint, {Widget? suffix}) => InputDecoration(
    hintText: hint,
    suffixIcon: suffix,
    fillColor: Colors.white.withValues(alpha: 0.06),
    hintStyle: const TextStyle(color: Color(0xFF8C909C)),
    enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.12))),
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.12))),
  );

  @override
  Widget build(BuildContext context) {
    return Theme(
      data: Theme.of(context).copyWith(brightness: Brightness.dark),
      child: Scaffold(
        backgroundColor: const Color(0xFF0A0B0E),
        body: Stack(
          children: [
            Positioned.fill(child: AnimatedBuilder(animation: _lap, builder: (context, _) => CustomPaint(painter: _CircuitPainter(_lap.value)))),
            Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [Colors.transparent, const Color(0xFF0A0B0E).withValues(alpha: 0.85), const Color(0xFF0A0B0E)], stops: const [0.2, 0.55, 0.75]),
                ),
              ),
            ),
            SafeArea(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(26, 0, 26, 24),
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: MediaQuery.of(context).size.height - MediaQuery.of(context).padding.vertical - 24),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.end,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const SizedBox(height: 260),
                      const Text("داووس کارتینگ", style: TextStyle(color: AppColors.accent, fontSize: 38, fontWeight: FontWeight.w700, height: 1.2)),
                      const SizedBox(height: 4),
                      const Text("اتاق کنترل پیست", style: TextStyle(color: Color(0xFFA3A7B3), fontSize: 16)),
                      const SizedBox(height: 30),
                      if (_error != null)
                        Container(
                          margin: const EdgeInsets.only(bottom: 14),
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(color: AppColors.danger.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(16), border: Border.all(color: AppColors.danger.withValues(alpha: 0.4))),
                          child: Row(
                            children: [
                              const Icon(Icons.error_rounded, color: AppColors.danger, size: 20),
                              const SizedBox(width: 10),
                              Expanded(child: Text(_error!, style: const TextStyle(color: Color(0xFFF4F4F1), height: 1.6, fontSize: 13.5))),
                            ],
                          ),
                        ),
                      TextField(
                        controller: _username,
                        textDirection: TextDirection.ltr,
                        style: const TextStyle(color: Color(0xFFF4F4F1)),
                        decoration: _decoration("نام کاربری", suffix: const Icon(Icons.person_outline_rounded, color: Color(0xFF8C909C))),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _password,
                        obscureText: !_show,
                        textDirection: TextDirection.ltr,
                        style: const TextStyle(color: Color(0xFFF4F4F1)),
                        onSubmitted: (_) => _submit(),
                        decoration: _decoration(
                          "رمز عبور",
                          suffix: IconButton(
                            tooltip: _show ? "پنهان کردن رمز" : "نمایش رمز",
                            icon: Icon(_show ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: const Color(0xFF8C909C)),
                            onPressed: () => setState(() => _show = !_show),
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),
                      AppButton(label: "ورود", icon: Icons.arrow_back_rounded, onPressed: _submit, busy: _busy),
                      const SizedBox(height: 22),
                      Text(Urls.domain, textAlign: TextAlign.center, textDirection: TextDirection.ltr, style: const TextStyle(color: Color(0xFF6C7181), fontSize: 12)),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// A circuit outline with a glowing kart running laps on it.
class _CircuitPainter extends CustomPainter {
  _CircuitPainter(this.t);

  final double t;

  Path _track(Size size) {
    final w = size.width;
    final h = math.min(size.height * 0.5, 420.0);
    final path = Path()
      ..moveTo(w * 0.12, h * 0.62)
      ..cubicTo(w * 0.08, h * 0.2, w * 0.3, h * 0.05, w * 0.48, h * 0.18)
      ..cubicTo(w * 0.62, h * 0.28, w * 0.7, h * 0.08, w * 0.84, h * 0.14)
      ..cubicTo(w * 1.0, h * 0.2, w * 0.98, h * 0.52, w * 0.86, h * 0.62)
      ..cubicTo(w * 0.76, h * 0.7, w * 0.78, h * 0.9, w * 0.6, h * 0.88)
      ..cubicTo(w * 0.42, h * 0.86, w * 0.5, h * 0.62, w * 0.34, h * 0.7)
      ..cubicTo(w * 0.24, h * 0.76, w * 0.14, h * 0.8, w * 0.12, h * 0.62)
      ..close();
    return path;
  }

  @override
  void paint(Canvas canvas, Size size) {
    final path = _track(size).shift(const Offset(0, 40));
    canvas.drawPath(
      path,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 22
        ..strokeJoin = StrokeJoin.round
        ..color = Colors.white.withValues(alpha: 0.045),
    );
    canvas.drawPath(
      path,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.4
        ..color = Colors.white.withValues(alpha: 0.16),
    );
    final metric = path.computeMetrics().first;
    // A fading comet tail behind the kart.
    const tail = 26;
    for (var i = tail; i >= 0; i--) {
      final d = ((t * metric.length) - i * 7) % metric.length;
      final pos = metric.getTangentForOffset(d < 0 ? d + metric.length : d)!.position;
      final fade = 1 - i / tail;
      canvas.drawCircle(pos, 2 + 4.5 * fade, Paint()..color = AppColors.accent.withValues(alpha: 0.75 * fade * fade));
    }
    final head = metric.getTangentForOffset(t * metric.length)!.position;
    canvas.drawCircle(head, 14, Paint()..color = AppColors.accent.withValues(alpha: 0.25)..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10));
    canvas.drawCircle(head, 5.5, Paint()..color = AppColors.accent);
  }

  @override
  bool shouldRepaint(_CircuitPainter old) => old.t != t;
}
