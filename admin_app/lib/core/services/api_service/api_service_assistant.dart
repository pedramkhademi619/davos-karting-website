part of "api_service.dart";

extension ApiServiceAssistant on ApiService {
  Future<AssistantOverview> getAssistantOverview(int days) async => AssistantOverview.fromJson(
    Map<String, dynamic>.from(await get(Urls.assistantOverview, query: {"days": days}) as Map),
  );

  /// [show]: all | unanswered | answered. [helpful]: false for the answers customers marked as not useful.
  Future<PageResult<AssistantInteraction>> getInteractions({
    String show = "all",
    bool? helpful,
    int offset = 0,
    int limit = 30,
  }) async => PageResult.parse(
    await get(Urls.assistantInteractions, query: {"show": show, "helpful": helpful, "offset": offset, "limit": limit}),
    AssistantInteraction.fromJson,
  );

  Future<PageResult<CachedAnswer>> getCachedAnswers({int offset = 0, int limit = 30}) async =>
      PageResult.parse(await get(Urls.assistantCache, query: {"offset": offset, "limit": limit}), CachedAnswer.fromJson);

  Future<void> saveCachedAnswer({String? id, required String question, required String answer}) {
    final body = {"question": question, "answer": answer};
    return id == null ? post(Urls.assistantCache, body: body) : put("${Urls.assistantCacheItem}$id", body: body);
  }

  Future<void> setCachedAnswerActive(String id, bool active) =>
      post("${Urls.assistantCacheItem}$id/active", body: {"active": active});

  Future<void> deleteCachedAnswer(String id) => delete("${Urls.assistantCacheItem}$id");

  Future<KnowledgeCatalog> getKnowledge() async =>
      KnowledgeCatalog.fromJson(Map<String, dynamic>.from(await get(Urls.assistantKnowledge) as Map));

  Future<void> saveKnowledge({
    String? id,
    required String sourceType,
    required String title,
    required String body,
    required String url,
  }) {
    final payload = {"source_type": sourceType, "title": title, "body": body, "url": url};
    return id == null
        ? post(Urls.assistantKnowledge, body: payload)
        : put("${Urls.assistantKnowledgeItem}$id", body: payload);
  }

  Future<void> deleteKnowledge(String id) => delete("${Urls.assistantKnowledgeItem}$id");
}
