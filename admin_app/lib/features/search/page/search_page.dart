import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/features/reservations/controller/reservation_actions.dart";
import "package:davos_admin/features/search/controller/ticket_search_controller.dart";
import "package:davos_admin/shared/widgets/search_box.dart";
import "package:davos_admin/shared/widgets/skeleton.dart";
import "package:davos_admin/shared/widgets/state_view.dart";
import "package:davos_admin/shared/widgets/ticket_card.dart";

class SearchPage extends GetView<TicketSearchController> {
  const SearchPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("جستجوی بلیت"), leading: const BackButton()),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 4, 20, 12),
            child: SearchBox(
              controller: controller.text,
              autofocus: true,
              hint: "شماره بلیت، موبایل، نام یا کد رزرو",
              onChanged: controller.onChanged,
              onSearch: (_) => controller.search(),
            ),
          ),
          Expanded(
            child: Obx(() {
              if (controller.error.value != null) return StateView.error(controller.error.value!, onRetry: controller.search);
              if (controller.searching.value && controller.results.isEmpty) return const SkeletonList(count: 2, itemHeight: 190);
              if (!controller.searched.value) {
                return StateView.empty("شمارهٔ بلیت یا چند رقم آخر موبایل را بنویسید؛ همان‌جا ورود مشتری را ثبت کنید.", icon: Icons.confirmation_number_outlined);
              }
              if (controller.results.isEmpty) return StateView.empty("بلیتی پیدا نشد.", icon: Icons.search_off_rounded);
              return ListView(
                padding: const EdgeInsets.fromLTRB(20, 4, 20, 40),
                children: [
                  for (final r in controller.results)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 14),
                      child: TicketCard(
                        reservation: r,
                        showDate: true,
                        onCheckIn: () async {
                          if (await ReservationActions.checkIn(r)) controller.search();
                        },
                        onCancel: () async {
                          if (await ReservationActions.cancel(context, r)) controller.search();
                        },
                      ),
                    ),
                  Text("${controller.results.length} نتیجه", textAlign: TextAlign.center, style: TextStyle(color: context.pit.low, fontSize: 12)),
                ],
              );
            }),
          ),
        ],
      ),
    );
  }
}
