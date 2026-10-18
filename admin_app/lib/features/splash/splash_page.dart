import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/constants/named_routs.dart";
import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/features/auth/controller/session_controller.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

/// First screen: finds out whether a stored session is still valid and sends the user to the home screen or the sign-in.
class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _decide());
  }

  Future<void> _decide() async {
    final signedIn = await Get.find<SessionController>().restore();
    Get.offAllNamed(signedIn ? NamedRouts.home : NamedRouts.login);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.ink,
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              "داووس کارتینگ",
              style: TextStyle(color: AppColors.accent, fontSize: 28, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 6),
            const Text("پنل مدیریت", style: TextStyle(color: Colors.white70)),
            const SizedBox(height: 28),
            SizedBox(height: 40, child: StateView.loading()),
          ],
        ),
      ),
    );
  }
}
