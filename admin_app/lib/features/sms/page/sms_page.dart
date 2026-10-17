import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/sms/controller/sms_controller.dart";
import "package:davos_admin/features/sms/model/sms_models.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/pager_bar.dart";
import "package:davos_admin/shared/widgets/pill_tab_bar.dart";
import "package:davos_admin/shared/widgets/state_view.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

class SmsPage extends GetView<SmsController> {
  const SmsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text("پنل پیامک"),
          bottom: const PillTabBar(tabs: ["ارسال پیام", "گزارش ارسال‌ها"]),
        ),
        body: TabBarView(children: [_SendTab(controller), _LogTab(controller)]),
      ),
    );
  }
}

class _AccountCard extends StatelessWidget {
  const _AccountCard(this.controller);

  final SmsController controller;

  @override
  Widget build(BuildContext context) => Obx(() {
    final account = controller.account.value;
    if (account == null) return const SizedBox.shrink();
    return AppCard(
      child: Column(
        children: [
          InfoRow("سرویس‌دهنده", account.providerLabel),
          InfoRow("اتصال", account.connected ? "برقرار" : "برقرار نیست", valueColor: account.connected ? AppColors.success : AppColors.danger),
          if (account.remainingCreditToman != null) InfoRow("اعتبار باقی‌مانده", tomanText(account.remainingCreditToman!), bold: true),
          if (account.expiresAt != null) InfoRow("انقضا", jalaliText(account.expiresAt)),
        ],
      ),
    );
  });
}

class _SendTab extends StatelessWidget {
  const _SendTab(this.controller);

  final SmsController controller;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _AccountCard(controller),
        const SectionTitle("ارسال پیام"),
        Obx(
          () => PillSelector<String>(
            options: const {"numbers": "شماره‌های دستی", "subscribers": "مشترکان خبرنامه", "day": "مشتریان یک روز"},
            value: controller.audience.value,
            onChanged: (v) {
              controller.audience.value = v;
              controller.cancelConfirm();
            },
          ),
        ),
        const SizedBox(height: 12),
        Obx(() {
          switch (controller.audience.value) {
            case "numbers":
              return LabeledField(
                label: "شماره‌ها (با فاصله، ویرگول یا خط جدید جدا کنید)",
                controller: controller.numbers,
                lines: 3,
                ltr: true,
                hint: "09121234567",
              );
            case "day":
              return DateField(
                label: "روز",
                value: controller.day.value ?? todayIso(),
                onChanged: (v) => controller.day.value = v,
              );
            default:
              return const Padding(
                padding: EdgeInsets.only(bottom: 12),
                child: Text("پیام برای همهٔ کسانی که در خبرنامه عضو شده‌اند ارسال می‌شود.", style: TextStyle(height: 1.7)),
              );
          }
        }),
        LabeledField(label: "متن پیام", controller: controller.text, lines: 4, maxLength: 500),
        Obx(() {
          final message = controller.sendMessage.value;
          return message == null ? const SizedBox.shrink() : MessageBar(message, error: controller.sendFailed.value);
        }),
        Obx(() {
          if (controller.confirming.value) {
            return Column(
              children: [
                MessageBar("این پیام برای ${controller.audienceLabel} ارسال می‌شود. مطمئن هستید؟"),
                Row(
                  children: [
                    Expanded(child: AppButton(label: "بله، ارسال شود", onPressed: controller.send, busy: controller.sending.value)),
                    const SizedBox(width: 10),
                    Expanded(child: AppButton(label: "انصراف", onPressed: controller.cancelConfirm, outlined: true)),
                  ],
                ),
              ],
            );
          }
          return AppButton(label: "ارسال", icon: Icons.send_rounded, onPressed: controller.send);
        }),
      ],
    );
  }
}

class _LogTab extends StatelessWidget {
  const _LogTab(this.controller);

  final SmsController controller;

  @override
  Widget build(BuildContext context) => Obx(() {
    final state = StateView.from(
      loading: controller.loading.value,
      isEmpty: controller.items.isEmpty,
      error: controller.error.value,
      emptyMessage: "هنوز پیامکی ارسال نشده است.",
      onRetry: controller.reload,
    );
    if (state != null) return state;
    return RefreshIndicator(
      onRefresh: controller.reload,
      child: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          for (final log in controller.items)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(child: Text(fa(log.recipient), textDirection: TextDirection.ltr, style: const TextStyle(fontWeight: FontWeight.w700))),
                        StatusChip(
                          smsStatusLabels[log.status] ?? log.status,
                          tone: switch (log.status) {
                            "delivered" => Tone.success,
                            "failed" || "blocked" => Tone.danger,
                            "sent" || "queued" => Tone.info,
                            _ => Tone.neutral,
                          },
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(log.body, style: const TextStyle(height: 1.7)),
                    const SizedBox(height: 6),
                    Text(
                      "${smsKindLabels[log.kind] ?? log.kind} • ${jalaliDateTime(log.createdAt)}${log.sentBy.isEmpty ? "" : " • ${log.sentBy}"}",
                      style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor),
                    ),
                    if (log.error.isNotEmpty) Text(log.error, style: const TextStyle(color: AppColors.danger, fontSize: 12)),
                  ],
                ),
              ),
            ),
          PagerBar(controller: controller),
        ],
      ),
    );
  });
}
