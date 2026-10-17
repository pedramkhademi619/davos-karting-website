import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// Journal entries (دفتر روزنامه) with search, filter by source and by account.
class JournalController extends PagedController<Entry> {
  final TextEditingController search = TextEditingController();
  final RxString source = "".obs;
  final RxnString accountId = RxnString();
  String _query = "";

  @override
  Future<void> fetchPage(int offset) async {
    final page = await ApiService().getJournal(
      q: _query,
      accountId: accountId.value,
      source: source.value,
      offset: offset,
      limit: pageSize,
    );
    items.assignAll(page.items);
    total.value = page.total;
  }

  Future<void> submitSearch(String text) {
    _query = text.trim();
    return restart();
  }

  Future<void> setSource(String value) {
    source.value = value;
    return restart();
  }

  Future<void> setAccount(String? id) {
    accountId.value = id;
    return restart();
  }

  Future<String?> reverse(Entry entry, String reason) => guard(() async {
    await ApiService().reverseEntry(entry.id, reason);
    await reload();
  });

  Future<String?> postManual({
    required String date,
    required String description,
    required bool opening,
    required List<Map<String, dynamic>> lines,
  }) => guard(() async {
    await ApiService().postJournalEntry(date: date, description: description, opening: opening, lines: lines);
    await reload();
  });

  @override
  void onClose() {
    search.dispose();
    super.onClose();
  }
}
