import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/assistant/model/assistant_models.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// Overview of what the assistant did over the last days.
class AssistantOverviewController extends LoadableController {
  final RxInt days = 7.obs;
  final Rxn<AssistantOverview> overview = Rxn<AssistantOverview>();

  @override
  Future<void> fetch() async => overview.value = await ApiService().getAssistantOverview(days.value);

  Future<void> setDays(int value) {
    days.value = value;
    return reload();
  }
}

/// The stored questions, to read what customers asked and where the assistant fell short.
class AssistantReviewController extends PagedController<AssistantInteraction> {
  /// "unanswered", "all" or "bad" (marked not useful by the customer).
  final RxString show = "unanswered".obs;

  @override
  Future<void> fetchPage(int offset) async {
    final api = ApiService();
    final page = show.value == "bad"
        ? await api.getInteractions(helpful: false, offset: offset, limit: pageSize)
        : await api.getInteractions(show: show.value == "all" ? "all" : "unanswered", offset: offset, limit: pageSize);
    items.assignAll(page.items);
    total.value = page.total;
  }

  Future<void> setShow(String value) {
    show.value = value;
    return restart();
  }
}

/// Stored answers reused for questions with the same meaning.
class AssistantCacheController extends PagedController<CachedAnswer> {
  @override
  Future<void> fetchPage(int offset) async {
    final page = await ApiService().getCachedAnswers(offset: offset, limit: pageSize);
    items.assignAll(page.items);
    total.value = page.total;
  }

  Future<String?> save({String? id, required String question, required String answer}) => guard(() async {
    await ApiService().saveCachedAnswer(id: id, question: question, answer: answer);
    await reload();
  });

  Future<String?> setActive(CachedAnswer entry, bool active) => guard(() async {
    await ApiService().setCachedAnswerActive(entry.id, active);
    await reload();
  });

  Future<String?> remove(CachedAnswer entry) => guard(() async {
    await ApiService().deleteCachedAnswer(entry.id);
    await reload();
  });
}

/// Texts the assistant may answer from.
class AssistantKnowledgeController extends LoadableController {
  final Rxn<KnowledgeCatalog> catalog = Rxn<KnowledgeCatalog>();

  @override
  Future<void> fetch() async => catalog.value = await ApiService().getKnowledge();

  Future<String?> save({
    String? id,
    required String sourceType,
    required String title,
    required String body,
    required String url,
  }) => guard(() async {
    await ApiService().saveKnowledge(id: id, sourceType: sourceType, title: title, body: body, url: url);
    await reload();
  });

  Future<String?> remove(KnowledgeEntry entry) => guard(() async {
    await ApiService().deleteKnowledge(entry.id);
    await reload();
  });
}
