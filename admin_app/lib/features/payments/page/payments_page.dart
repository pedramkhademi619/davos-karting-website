import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/payments/controller/payments_controller.dart";
import "package:davos_admin/features/payments/model/admin_payment.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/pager_bar.dart";
import "package:davos_admin/shared/widgets/search_box.dart";
import "package:davos_admin/shared/widgets/state_view.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

class PaymentsPage extends GetView<PaymentsController> {
  const PaymentsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("پرداخت‌ها")),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 6),
            child: SearchBox(controller: controller.search, onSearch: controller.submitSearch, hint: "کد پیگیری یا شناسه"),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Obx(
              () => PillSelector<String>(
                options: {"": "همه", "paid": "پرداخت شده", "failed": "ناموفق", "unknown": "نامشخص", "refund_pending": "در انتظار استرداد", "created": "ایجاد شده"},
                value: controller.status.value,
                onChanged: controller.setStatus,
              ),
            ),
          ),
          Expanded(
            child: Obx(() {
              final state = StateView.from(
                loading: controller.loading.value,
                isEmpty: controller.items.isEmpty,
                error: controller.error.value,
                emptyMessage: "پرداختی پیدا نشد.",
                onRetry: controller.reload,
              );
              if (state != null) return state;
              return RefreshIndicator(
                onRefresh: controller.reload,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
                  children: [
                    AppCard(
                      child: InfoRow("مجموع پرداخت‌های موفق", tomanText(controller.paidTotalToman.value), bold: true),
                    ),
                    const SizedBox(height: 8),
                    for (final payment in controller.items) Padding(padding: const EdgeInsets.only(bottom: 8), child: _PaymentTile(payment)),
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

class _PaymentTile extends StatelessWidget {
  const _PaymentTile(this.payment);

  final AdminPayment payment;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Text(tomanText(payment.amountToman), style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15))),
              StatusChip(payment.statusLabel, tone: paymentTone(payment.status)),
            ],
          ),
          const SizedBox(height: 6),
          InfoRow("کد پیگیری", fa(payment.orderRef)),
          if (payment.referenceId != null) InfoRow("شماره مرجع بانک", fa(payment.referenceId)),
          InfoRow("درگاه", payment.gateway),
          InfoRow("زمان", jalaliDateTime(payment.createdAt)),
          if (payment.settledAt != null) InfoRow("تسویه", jalaliDateTime(payment.settledAt)),
          if ((payment.failureReason ?? "").isNotEmpty) InfoRow("دلیل خطا", payment.failureReason!),
        ],
      ),
    );
  }
}
