import "package:davos_admin/shared/models/json_read.dart";

/// Persian names of what the assistant did with a question.
const Map<String, String> outcomeLabels = {
  "answered": "پاسخ از دانسته‌ها",
  "quick_answer": "پاسخ سریع (بدون مدل)",
  "small_talk": "سلام و تشکر",
  "insufficient_information": "اطلاعات کافی نبود",
  "refused_unsafe_input": "درخواست مشکوک رد شد",
  "fallback_provider_unavailable": "مدل در دسترس نبود",
  "fallback_budget_exhausted": "بودجهٔ روزانه تمام شد",
};

/// Outcomes that mean the customer did not get an answer: the ones worth reading.
const List<String> problemOutcomes = [
  "insufficient_information",
  "fallback_provider_unavailable",
  "fallback_budget_exhausted",
];

const Map<String, String> sourceTypeLabels = {
  "faq": "پرسش‌های متداول",
  "policy": "قوانین",
  "service": "خدمات",
  "pricing": "قیمت",
  "contact": "تماس",
};

class AssistantOverview {
  const AssistantOverview({
    required this.days,
    required this.questions,
    required this.byOutcome,
    required this.servedFromCache,
    required this.helpfulVotes,
    required this.notHelpfulVotes,
    required this.promptTokens,
    required this.completionTokens,
    required this.cachedAnswersActive,
    required this.cachedAnswersTotal,
    required this.knowledgeEntries,
  });

  factory AssistantOverview.fromJson(Json j) => AssistantOverview(
    days: j.integer("days"),
    questions: j.integer("questions"),
    byOutcome: {for (final e in j.obj("by_outcome").entries) e.key: (e.value as num?)?.toInt() ?? 0},
    servedFromCache: j.integer("served_from_cache"),
    helpfulVotes: j.integer("helpful_votes"),
    notHelpfulVotes: j.integer("not_helpful_votes"),
    promptTokens: j.integer("prompt_tokens"),
    completionTokens: j.integer("completion_tokens"),
    cachedAnswersActive: j.integer("cached_answers_active"),
    cachedAnswersTotal: j.integer("cached_answers_total"),
    knowledgeEntries: j.integer("knowledge_entries"),
  );

  final int days;
  final int questions;
  final Map<String, int> byOutcome;
  final int servedFromCache;
  final int helpfulVotes;
  final int notHelpfulVotes;
  final int promptTokens;
  final int completionTokens;
  final int cachedAnswersActive;
  final int cachedAnswersTotal;
  final int knowledgeEntries;
}

class AssistantInteraction {
  const AssistantInteraction({
    required this.id,
    required this.occurredAt,
    required this.outcome,
    required this.question,
    required this.answer,
    required this.helpful,
    required this.servedFromCache,
    required this.tokens,
  });

  factory AssistantInteraction.fromJson(Json j) => AssistantInteraction(
    id: j.str("interaction_id"),
    occurredAt: j.str("occurred_at"),
    outcome: j.str("outcome"),
    question: j.strOrNull("question_text"),
    answer: j.strOrNull("answer_text"),
    helpful: j.flagOrNull("helpful"),
    servedFromCache: j.flag("served_from_cache"),
    tokens: j.integer("tokens"),
  );

  final String id;
  final String occurredAt;
  final String outcome;
  final String? question;
  final String? answer;
  final bool? helpful;
  final bool servedFromCache;
  final int tokens;
}

class CachedAnswer {
  const CachedAnswer({
    required this.id,
    required this.question,
    required this.answer,
    required this.hitCount,
    required this.isActive,
    required this.isCurated,
    required this.lastUsedAt,
  });

  factory CachedAnswer.fromJson(Json j) => CachedAnswer(
    id: j.str("entry_id"),
    question: j.str("question"),
    answer: j.str("answer"),
    hitCount: j.integer("hit_count"),
    isActive: j.flag("is_active"),
    isCurated: j.flag("is_curated"),
    lastUsedAt: j.str("last_used_at"),
  );

  final String id;
  final String question;
  final String answer;
  final int hitCount;
  final bool isActive;
  final bool isCurated;
  final String lastUsedAt;
}

class KnowledgeEntry {
  const KnowledgeEntry({
    required this.id,
    required this.sourceType,
    required this.title,
    required this.body,
    required this.url,
    required this.updatedAt,
  });

  factory KnowledgeEntry.fromJson(Json j) => KnowledgeEntry(
    id: j.str("entry_id"),
    sourceType: j.str("source_type"),
    title: j.str("title"),
    body: j.str("body"),
    url: j.str("url"),
    updatedAt: j.str("updated_at"),
  );

  final String id;
  final String sourceType;
  final String title;
  final String body;
  final String url;
  final String updatedAt;
}

class KnowledgeCatalog {
  const KnowledgeCatalog({
    required this.entries,
    required this.maxEntries,
    required this.maxChars,
    required this.totalChars,
    required this.sentWhole,
  });

  factory KnowledgeCatalog.fromJson(Json j) => KnowledgeCatalog(
    entries: j.list("entries").map(KnowledgeEntry.fromJson).toList(),
    maxEntries: j.integer("max_entries"),
    maxChars: j.integer("max_chars"),
    totalChars: j.integer("total_chars"),
    sentWhole: j.flag("sent_whole"),
  );

  final List<KnowledgeEntry> entries;
  final int maxEntries;
  final int maxChars;
  final int totalChars;
  final bool sentWhole;
}
