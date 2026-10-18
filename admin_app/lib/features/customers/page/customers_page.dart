import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/auth/controller/session_controller.dart";
import "package:davos_admin/features/customers/controller/customers_controller.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/pager_bar.dart";
import "package:davos_admin/shared/widgets/search_box.dart";
import "package:davos_admin/shared/widgets/state_view.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

class CustomersPage extends GetView<CustomersController> {
  const CustomersPage({super.key});

  @override
  Widget build(BuildContext context) {
    final isOwner = Get.find<SessionController>().isOwner;
    return Scaffold(
      appBar: AppBar(title: const Text("مشتریان")),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: SearchBox(controller: controller.search, onSearch: controller.submitSearch, hint: "نام یا شماره موبایل"),
          ),
          Expanded(
            child: Obx(() {
              final state = StateView.from(
                loading: controller.loading.value,
                isEmpty: controller.items.isEmpty,
                error: controller.error.value,
                emptyMessage: "مشتری‌ای پیدا نشد.",
                onRetry: controller.reload,
              );
              if (state != null) return state;
              return RefreshIndicator(
                onRefresh: controller.reload,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(12, 0, 12, 24),
                  children: [
                    for (final customer in controller.items)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: AppCard(
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(customer.fullName.isEmpty ? "بدون نام" : customer.fullName, style: const TextStyle(fontWeight: FontWeight.w700)),
                                    const SizedBox(height: 2),
                                    Text(fa(customer.mobile), textDirection: TextDirection.ltr),
                                    const SizedBox(height: 4),
                                    Text(
                                      "عضویت: ${jalaliText(customer.createdAt)}${customer.marketingOptIn ? " • خبرنامه" : ""}",
                                      style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor),
                                    ),
                                  ],
                                ),
                              ),
                              Column(
                                children: [
                                  StatusChip(customer.blocked ? "مسدود" : "فعال", tone: customer.blocked ? Tone.danger : Tone.success),
                                  if (isOwner)
                                    TextButton(
                                      onPressed: () async {
                                        final yes = await confirm(
                                          context,
                                          title: customer.blocked ? "آزادسازی مشتری" : "مسدود کردن مشتری",
                                          message: customer.blocked
                                              ? "این مشتری دوباره می‌تواند وارد شود و رزرو کند."
                                              : "این مشتری دیگر نمی‌تواند وارد شود یا رزرو کند.",
                                          danger: !customer.blocked,
                                        );
                                        if (yes) await controller.toggleBlock(customer);
                                      },
                                      child: Text(customer.blocked ? "آزاد کردن" : "مسدود کردن"),
                                    ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    PagerBar(controller: controller),
                  ],
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}
