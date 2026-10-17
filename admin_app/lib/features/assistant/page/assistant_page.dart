import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/assistant/controller/assistant_controller.dart";
import "package:davos_admin/features/assistant/model/assistant_models.dart";
import "package:davos_admin/features/auth/controller/session_controller.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/pager_bar.dart";
import "package:davos_admin/shared/widgets/pill_tab_bar.dart";
import "package:davos_admin/shared/widgets/state_view.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

/// The AI assistant: four tabs (overview, questions, stored answers, knowledge). Editing is for the owner only; the
/// server enforces that too.
class AssistantPage extends StatelessWidget {
  const AssistantPage({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 4,
      child: Scaffold(
        appBar: AppBar(
          title: const Text("دستیار هوشمند"),
          bottom: const PillTabBar(scrollable: true, tabs: ["خلاصه", "پرسش‌ها", "پاسخ‌های ذخیره‌شده", "دانسته‌ها"]),
        ),
        body: const TabBarView(children: [_OverviewTab(), _ReviewTab(), _CacheTab(), _KnowledgeTab()]),
      ),
    );
  }
}

class _OverviewTab extends GetView<AssistantOverviewController> {
  const _OverviewTab();

  @override
  Widget build(BuildContext context) => Obx(() {
    final o = controller.overview.value;
    final state = StateView.from(
      loading: controller.loading.value,
      isEmpty: o == null,
      error: controller.error.value,
      emptyMessage: "اطلاعاتی نیست.",
      onRetry: controller.reload,
    );
    if (state != null) return state;
    final data = o!;
    final outcomes = data.byOutcome.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
    return RefreshIndicator(
      onRefresh: controller.reload,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          PillSelector<int>(
            options: const {1: "امروز", 7: "۷ روز", 30: "۳۰ روز", 90: "۹۰ روز"},
            value: controller.days.value,
            onChanged: controller.setDays,
          ),
          const SizedBox(height: 12),
          StatGrid(
            tiles: [
              StatTile(label: "تعداد پرسش", value: fa(data.questions)),
              StatTile(label: "از پاسخ‌های ذخیره‌شده", value: fa(data.servedFromCache)),
              StatTile(label: "مفید بود", value: fa(data.helpfulVotes), color: AppColors.success),
              StatTile(label: "مفید نبود", value: fa(data.notHelpfulVotes), color: data.notHelpfulVotes > 0 ? AppColors.danger : null),
              StatTile(label: "پاسخ ذخیره‌شدهٔ فعال", value: "${fa(data.cachedAnswersActive)} از ${fa(data.cachedAnswersTotal)}"),
              StatTile(label: "متن‌های دانسته‌ها", value: fa(data.knowledgeEntries)),
              StatTile(label: "توکن ورودی", value: grouped(data.promptTokens)),
              StatTile(label: "توکن خروجی", value: grouped(data.completionTokens)),
            ],
          ),
          const SectionTitle("نتیجهٔ پرسش‌ها"),
          AppCard(
            child: Column(
              children: [
                if (outcomes.isEmpty) const Text("هنوز پرسشی ثبت نشده است."),
                for (final e in outcomes)
                  InfoRow(
                    outcomeLabels[e.key] ?? e.key,
                    fa(e.value),
                    valueColor: problemOutcomes.contains(e.key) ? AppColors.danger : null,
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  });
}

class _ReviewTab extends GetView<AssistantReviewController> {
  const _ReviewTab();

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Padding(
        padding: const EdgeInsets.all(12),
        child: Obx(
          () => PillSelector<String>(
            options: const {"unanswered": "بی‌پاسخ‌ها", "bad": "مفید نبود", "all": "همه"},
            value: controller.show.value,
            onChanged: controller.setShow,
          ),
        ),
      ),
      Expanded(
        child: Obx(() {
          final state = StateView.from(
            loading: controller.loading.value,
            isEmpty: controller.items.isEmpty,
            error: controller.error.value,
            emptyMessage: "موردی نیست.",
            onRetry: controller.reload,
          );
          if (state != null) return state;
          return RefreshIndicator(
            onRefresh: controller.reload,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 24),
              children: [
                for (final item in controller.items)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: AppCard(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(child: Text(jalaliDateTime(item.occurredAt), style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor))),
                              StatusChip(outcomeLabels[item.outcome] ?? item.outcome, tone: problemOutcomes.contains(item.outcome) ? Tone.danger : Tone.neutral),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(item.question ?? "(متن پرسش ذخیره نشده است)", style: const TextStyle(fontWeight: FontWeight.w700, height: 1.7)),
                          if (item.answer != null) ...[const SizedBox(height: 4), Text(item.answer!, style: const TextStyle(height: 1.7))],
                          const SizedBox(height: 4),
                          Text(
                            "${item.servedFromCache ? "از پاسخ ذخیره‌شده • " : ""}${item.helpful == null ? "" : (item.helpful! ? "مفید بود • " : "مفید نبود • ")}${fa(item.tokens)} توکن",
                            style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor),
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
  );
}

class _CacheTab extends GetView<AssistantCacheController> {
  const _CacheTab();

  @override
  Widget build(BuildContext context) {
    final isOwner = Get.find<SessionController>().isOwner;
    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: isOwner
          ? FloatingActionButton.extended(onPressed: () => _edit(context, null), icon: const Icon(Icons.add), label: const Text("پاسخ جدید"))
          : null,
      body: Obx(() {
        final state = StateView.from(
          loading: controller.loading.value,
          isEmpty: controller.items.isEmpty,
          error: controller.error.value,
          emptyMessage: "پاسخ ذخیره‌شده‌ای نیست.",
          onRetry: controller.reload,
        );
        if (state != null) return state;
        return RefreshIndicator(
          onRefresh: controller.reload,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
            children: [
              for (final entry in controller.items)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: AppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(child: Text(entry.question, style: const TextStyle(fontWeight: FontWeight.w700, height: 1.6))),
                            if (entry.isCurated) const StatusChip("دستی", tone: Tone.info),
                            const SizedBox(width: 6),
                            StatusChip(entry.isActive ? "فعال" : "غیرفعال", tone: entry.isActive ? Tone.success : Tone.neutral),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(entry.answer, style: const TextStyle(height: 1.7)),
                        const SizedBox(height: 4),
                        Text("${fa(entry.hitCount)} بار استفاده شد • آخرین: ${jalaliText(entry.lastUsedAt)}", style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
                        if (isOwner)
                          Row(
                            children: [
                              TextButton(onPressed: () => _edit(context, entry), child: const Text("ویرایش")),
                              TextButton(
                                onPressed: () async {
                                  final m = await controller.setActive(entry, !entry.isActive);
                                  if (m != null) toast(m, error: true);
                                },
                                child: Text(entry.isActive ? "غیرفعال کردن" : "فعال کردن"),
                              ),
                              TextButton(
                                style: TextButton.styleFrom(foregroundColor: AppColors.danger),
                                onPressed: () async {
                                  if (!await confirm(context, title: "حذف پاسخ", message: "این پاسخ ذخیره‌شده حذف شود؟", danger: true, confirmLabel: "حذف")) return;
                                  final m = await controller.remove(entry);
                                  if (m != null) toast(m, error: true);
                                },
                                child: const Text("حذف"),
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
    );
  }

  void _edit(BuildContext context, CachedAnswer? entry) {
    final question = TextEditingController(text: entry?.question ?? "");
    final answer = TextEditingController(text: entry?.answer ?? "");
    var busy = false;
    String? error;
    showFormSheet<void>(
      context,
      title: entry == null ? "پاسخ جدید" : "ویرایش پاسخ",
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setState) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            LabeledField(label: "پرسش", controller: question, lines: 2),
            LabeledField(label: "پاسخ", controller: answer, lines: 5),
            if (error != null) MessageBar(error!, error: true),
            AppButton(
              label: "ذخیره",
              busy: busy,
              onPressed: () async {
                setState(() => busy = true);
                final m = await controller.save(id: entry?.id, question: question.text.trim(), answer: answer.text.trim());
                if (!sheetContext.mounted) return;
                if (m == null) {
                  Navigator.of(sheetContext).pop();
                  toast("ذخیره شد.");
                } else {
                  setState(() {
                    busy = false;
                    error = m;
                  });
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _KnowledgeTab extends GetView<AssistantKnowledgeController> {
  const _KnowledgeTab();

  @override
  Widget build(BuildContext context) {
    final isOwner = Get.find<SessionController>().isOwner;
    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: isOwner
          ? FloatingActionButton.extended(onPressed: () => _edit(context, null), icon: const Icon(Icons.add), label: const Text("متن جدید"))
          : null,
      body: Obx(() {
        final catalog = controller.catalog.value;
        final state = StateView.from(
          loading: controller.loading.value,
          isEmpty: catalog == null,
          error: controller.error.value,
          emptyMessage: "اطلاعاتی نیست.",
          onRetry: controller.reload,
        );
        if (state != null) return state;
        final data = catalog!;
        return RefreshIndicator(
          onRefresh: controller.reload,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
            children: [
              MessageBar(
                "${fa(data.entries.length)} از ${fa(data.maxEntries)} متن • ${grouped(data.totalChars)} از ${grouped(data.maxChars)} نویسه. "
                "${data.sentWhole ? "همهٔ دانسته‌ها با هر پرسش به مدل فرستاده می‌شود." : "حجم دانسته‌ها از حد گذشته است و فقط بخشی از آن به مدل می‌رسد."}",
                error: !data.sentWhole,
              ),
              for (final entry in data.entries)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: AppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(child: Text(entry.title, style: const TextStyle(fontWeight: FontWeight.w800))),
                            StatusChip(sourceTypeLabels[entry.sourceType] ?? entry.sourceType),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(entry.body, maxLines: 6, overflow: TextOverflow.ellipsis, style: const TextStyle(height: 1.7)),
                        if (entry.url.isNotEmpty) Text(entry.url, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 12)),
                        if (isOwner)
                          Row(
                            children: [
                              TextButton(onPressed: () => _edit(context, entry), child: const Text("ویرایش")),
                              TextButton(
                                style: TextButton.styleFrom(foregroundColor: AppColors.danger),
                                onPressed: () async {
                                  if (!await confirm(context, title: "حذف متن", message: "«${entry.title}» حذف شود؟", danger: true, confirmLabel: "حذف")) return;
                                  final m = await controller.remove(entry);
                                  if (m != null) toast(m, error: true);
                                },
                                child: const Text("حذف"),
                              ),
                            ],
                          ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        );
      }),
    );
  }

  void _edit(BuildContext context, KnowledgeEntry? entry) {
    final title = TextEditingController(text: entry?.title ?? "");
    final body = TextEditingController(text: entry?.body ?? "");
    final url = TextEditingController(text: entry?.url ?? "");
    var type = entry?.sourceType ?? "faq";
    var busy = false;
    String? error;
    showFormSheet<void>(
      context,
      title: entry == null ? "متن جدید" : "ویرایش متن",
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setState) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ChoiceField<String>(label: "نوع", value: type, options: sourceTypeLabels, onChanged: (v) => setState(() => type = v ?? "faq")),
            LabeledField(label: "عنوان", controller: title),
            LabeledField(label: "متن", controller: body, lines: 8),
            LabeledField(label: "نشانی صفحه (اختیاری)", controller: url, ltr: true),
            if (error != null) MessageBar(error!, error: true),
            AppButton(
              label: "ذخیره",
              busy: busy,
              onPressed: () async {
                setState(() => busy = true);
                final m = await controller.save(id: entry?.id, sourceType: type, title: title.text.trim(), body: body.text.trim(), url: url.text.trim());
                if (!sheetContext.mounted) return;
                if (m == null) {
                  Navigator.of(sheetContext).pop();
                  toast("ذخیره شد.");
                } else {
                  setState(() {
                    busy = false;
                    error = m;
                  });
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}
