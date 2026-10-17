import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/system/controller/system_controller.dart";
import "package:davos_admin/features/system/model/system_status.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/state_view.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

/// Overall sentence and how loudly to show it: 0 = fine, 1 = needs attention, 2 = something is down.
const _overall = {
  "ok": ("همه سرویس‌ها سالم‌اند.", 0),
  "degraded": ("همه‌چیز کار می‌کند ولی بعضی موارد نیاز به توجه دارند.", 1),
  "down": ("حداقل یک سرویس از کار افتاده است.", 2),
};

const _groups = ["زیرساخت", "سرویس‌های بیرونی", "برنامه"];

class SystemPage extends GetView<SystemController> {
  const SystemPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("وضعیت سرویس‌ها")),
      body: Obx(() {
        final status = controller.status.value;
        final state = StateView.from(
          loading: controller.loading.value,
          isEmpty: status == null,
          error: controller.error.value,
          emptyMessage: "اطلاعاتی نیست.",
          onRetry: controller.reload,
        );
        if (state != null) return state;
        final data = status!;
        final summary = _overall[data.overall];
        final extraGroups = data.services.map((s) => s.group).where((g) => !_groups.contains(g)).toSet();
        return RefreshIndicator(
          onRefresh: controller.reload,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (controller.error.value != null) MessageBar(controller.error.value!, error: true),
              MessageBar(summary?.$1 ?? levelLabels[data.overall] ?? data.overall, error: summary?.$2 == 2, warning: summary?.$2 == 1),
              Text("آخرین بررسی: ${jalaliDateTime(data.checkedAt)}", style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
              for (final group in [..._groups, ...extraGroups])
                ..._group(context, group, data.services.where((s) => s.group == group).toList()),
            ],
          ),
        );
      }),
    );
  }

  List<Widget> _group(BuildContext context, String group, List<ServiceStatus> services) {
    if (services.isEmpty) return const [];
    return [
      SectionTitle(group),
      for (final service in services)
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(child: Text(service.label, style: const TextStyle(fontWeight: FontWeight.w800))),
                    StatusChip(levelLabels[service.level] ?? service.level, tone: levelTone(service.level)),
                  ],
                ),
                const SizedBox(height: 4),
                Text(service.summary, style: const TextStyle(height: 1.7)),
                if (service.latencyMs != null)
                  Text("تاخیر: ${fa(service.latencyMs)} میلی‌ثانیه", style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
                for (final part in service.parts)
                  Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.circle, size: 9, color: StatusChip.colors(levelTone(part.level), Brightness.dark).$2),
                        const SizedBox(width: 8),
                        Expanded(child: Text("${part.label}${part.detail.isEmpty ? "" : " — ${part.detail}"}", style: const TextStyle(fontSize: 13, height: 1.6))),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ),
    ];
  }
}
