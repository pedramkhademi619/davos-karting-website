import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/constants/named_routs.dart";
import "package:davos_admin/features/accounting/page/finance_view.dart";
import "package:davos_admin/features/auth/controller/session_controller.dart";
import "package:davos_admin/features/dashboard/today_view.dart";
import "package:davos_admin/features/more/more_view.dart";
import "package:davos_admin/features/reservations/page/reservations_view.dart";
import "package:davos_admin/features/shell/pit_nav_bar.dart";
import "package:davos_admin/features/shell/shell_controller.dart";

/// The app's frame: the four main tabs and the floating bar. Tabs the person has no permission for are not shown.
class ShellPage extends StatelessWidget {
  const ShellPage({super.key});

  @override
  Widget build(BuildContext context) {
    final session = Get.find<SessionController>();
    final shell = Get.find<ShellController>();
    return Obx(() {
      session.me.value;
      final tabs = <_Tab>[
        const _Tab(NavItem(label: "امروز", icon: Icons.bolt_outlined, activeIcon: Icons.bolt_rounded), TodayView()),
        if (session.can("reservations")) const _Tab(NavItem(label: "رزروها", icon: Icons.calendar_month_outlined, activeIcon: Icons.calendar_month_rounded), ReservationsView()),
        if (session.can("accounting")) const _Tab(NavItem(label: "مالی", icon: Icons.account_balance_wallet_outlined, activeIcon: Icons.account_balance_wallet_rounded), FinanceView()),
        const _Tab(NavItem(label: "بیشتر", icon: Icons.grid_view_outlined, activeIcon: Icons.grid_view_rounded), MoreView()),
      ];
      shell.lastIndex = tabs.length - 1;
      final index = shell.index.value.clamp(0, tabs.length - 1);
      return Scaffold(
        extendBody: true,
        body: IndexedStack(index: index, children: [for (final t in tabs) t.view]),
        bottomNavigationBar: PitNavBar(
          items: [for (final t in tabs) t.item],
          index: index,
          onSelect: shell.open,
          onAction: session.can("reservations") ? () => Get.toNamed(NamedRouts.newReservation) : null,
        ),
      );
    });
  }
}

class _Tab {
  const _Tab(this.item, this.view);

  final NavItem item;
  final Widget view;
}
