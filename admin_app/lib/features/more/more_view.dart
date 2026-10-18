import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/constants/named_routs.dart";
import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/theme_controller.dart";
import "package:davos_admin/features/auth/controller/session_controller.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/pressable.dart";

class _Entry {
  const _Entry(this.title, this.subtitle, this.icon, this.color, this.route, this.permission);

  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
  final String route;
  final String permission;
}

const _groups = <(String, List<_Entry>)>[
  (
    "عملیات",
    [
      _Entry("مشتریان", "جستجو، مسدود و آزادسازی", Icons.people_alt_rounded, AppColors.info, NamedRouts.customers, "customers"),
      _Entry("پرداخت‌ها", "تراکنش‌های درگاه و شماره مرجع", Icons.credit_card_rounded, AppColors.success, NamedRouts.payments, "payments"),
    ],
  ),
  (
    "ارتباط و هوش مصنوعی",
    [
      _Entry("پنل پیامک", "اعتبار، ارسال و گزارش تحویل", Icons.sms_rounded, AppColors.warning, NamedRouts.sms, "sms"),
      _Entry("دستیار هوشمند", "پرسش‌ها، پاسخ‌ها و دانسته‌ها", Icons.smart_toy_rounded, Color(0xFFA78BFA), NamedRouts.assistant, "assistant"),
    ],
  ),
  (
    "سیستم",
    [
      _Entry("تنظیمات و قیمت‌ها", "سانس‌ها، ظرفیت و محدودیت رزرو", Icons.tune_rounded, AppColors.accent, NamedRouts.settings, "settings"),
      _Entry("وضعیت سرویس‌ها", "پایگاه‌داده، ردیس، پیامک و درگاه", Icons.monitor_heart_rounded, AppColors.danger, NamedRouts.system, "system"),
      _Entry("کاربران پنل", "افزودن کارمند و سطح دسترسی", Icons.admin_panel_settings_rounded, Color(0xFF2DD4BF), NamedRouts.users, "owner"),
    ],
  ),
];

/// The last tab: everything that is not part of the daily rhythm, grouped, and the person's own account.
class MoreView extends StatelessWidget {
  const MoreView({super.key});

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final session = Get.find<SessionController>();
    final theme = Get.find<ThemeController>();
    return SafeArea(
      bottom: false,
      child: Obx(() {
        final me = session.me.value;
        return ListView(
          padding: const EdgeInsets.fromLTRB(20, 14, 20, 130),
          children: [
            const Text("بیشتر", style: TextStyle(fontSize: 26, fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            AppCard(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    width: 56,
                    height: 56,
                    decoration: const BoxDecoration(gradient: AppColors.amber, shape: BoxShape.circle),
                    child: Center(child: Text((me?.shownName ?? "؟").characters.first, style: const TextStyle(color: AppColors.ink, fontSize: 24, fontWeight: FontWeight.w700))),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(me?.shownName ?? "", style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 17)),
                        const SizedBox(height: 2),
                        Text("${me?.roleLabel ?? ""} • ${me?.username ?? ""}", style: TextStyle(color: p.mid, fontSize: 13)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            for (final group in _groups)
              if (group.$2.any((e) => session.can(e.permission))) ...[
                Padding(padding: const EdgeInsets.fromLTRB(4, 26, 4, 10), child: Text(group.$1, style: TextStyle(color: p.mid, fontWeight: FontWeight.w700, fontSize: 13))),
                _Group(children: [for (final e in group.$2.where((e) => session.can(e.permission))) _Row(entry: e)]),
              ],
            Padding(padding: const EdgeInsets.fromLTRB(4, 26, 4, 10), child: Text("حساب من", style: TextStyle(color: p.mid, fontWeight: FontWeight.w700, fontSize: 13))),
            _Group(
              children: [
                _Tile(icon: Icons.lock_reset_rounded, color: AppColors.info, title: "تغییر رمز عبور", onTap: () => Get.toNamed(NamedRouts.changePassword)),
                Obx(() => _Tile(icon: Icons.brightness_6_rounded, color: AppColors.warning, title: "ظاهر برنامه", trailing: theme.label, onTap: theme.cycle)),
                _Tile(
                  icon: Icons.logout_rounded,
                  color: AppColors.danger,
                  title: "خروج از حساب",
                  onTap: () async {
                    if (await confirm(context, title: "خروج", message: "از حساب کاربری خارج می‌شوید؟", confirmLabel: "خروج", danger: true)) {
                      await session.signOut();
                    }
                  },
                ),
              ],
            ),
            const SizedBox(height: 24),
            Center(child: Text("داووس کارتینگ • نسخهٔ ۱٫۰", style: TextStyle(color: p.low, fontSize: 12))),
          ],
        );
      }),
    );
  }
}

class _Group extends StatelessWidget {
  const _Group({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return Container(
      decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(22), border: Border.all(color: p.line), boxShadow: p.shadow),
      child: Column(
        children: [
          for (var i = 0; i < children.length; i++) ...[
            children[i],
            if (i != children.length - 1) Padding(padding: const EdgeInsetsDirectional.only(start: 66), child: Divider(color: p.line)),
          ],
        ],
      ),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row({required this.entry});

  final _Entry entry;

  @override
  Widget build(BuildContext context) => _Tile(icon: entry.icon, color: entry.color, title: entry.title, subtitle: entry.subtitle, onTap: () => Get.toNamed(entry.route));
}

class _Tile extends StatelessWidget {
  const _Tile({required this.icon, required this.color, required this.title, required this.onTap, this.subtitle, this.trailing});

  final IconData icon;
  final Color color;
  final String title;
  final String? subtitle;
  final String? trailing;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return Pressable(
      onTap: onTap,
      scale: 0.99,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(color: color.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(13)),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5)),
                  if (subtitle != null) Text(subtitle!, style: TextStyle(color: p.mid, fontSize: 12, height: 1.5)),
                ],
              ),
            ),
            if (trailing != null) Padding(padding: const EdgeInsetsDirectional.only(end: 6), child: Text(trailing!, style: TextStyle(color: p.mid, fontSize: 12.5))),
            Icon(Icons.chevron_left_rounded, color: p.low),
          ],
        ),
      ),
    );
  }
}
