import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";
import "package:davos_admin/shared/widgets/app_button.dart";

/// "۱ تا ۳۰ از ۱۲۰" with next/previous buttons for any [PagedController].
class PagerBar extends StatelessWidget {
  const PagerBar({super.key, required this.controller});

  final PagedController<dynamic> controller;

  @override
  Widget build(BuildContext context) => Obx(() {
    final total = controller.total.value;
    if (total <= controller.pageSize) return const SizedBox.shrink();
    final from = controller.offset.value + 1;
    final to = (controller.offset.value + controller.items.length).clamp(from, total);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 14),
      child: Row(
        children: [
          AppButton(label: "بعدی", onPressed: controller.hasNext ? controller.next : null, outlined: true, expand: false, small: true, icon: Icons.chevron_right_rounded),
          Expanded(child: Text("${fa(from)} تا ${fa(to)} از ${fa(total)}", textAlign: TextAlign.center, style: TextStyle(color: context.pit.mid, fontSize: 13))),
          AppButton(label: "قبلی", onPressed: controller.hasPrevious ? controller.previous : null, outlined: true, expand: false, small: true, icon: Icons.chevron_left_rounded),
        ],
      ),
    );
  });
}
