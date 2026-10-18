import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/payments/model/admin_payment.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";
import "package:davos_admin/shared/models/json_read.dart";
import "package:flutter/material.dart";

class PaymentsController extends PagedController<AdminPayment> {
  final TextEditingController search = TextEditingController();
  final RxString status = "".obs;
  final RxInt paidTotalToman = 0.obs;
  String _query = "";

  @override
  Future<void> fetchPage(int offset) async {
    final page = await ApiService().getPayments(status: status.value, q: _query, offset: offset, limit: pageSize);
    items.assignAll(page.items);
    total.value = page.total;
    paidTotalToman.value = page.extra.integer("paid_total_toman");
  }

  Future<void> submitSearch(String text) {
    _query = text.trim();
    return restart();
  }

  Future<void> setStatus(String value) {
    status.value = value;
    return restart();
  }

  @override
  void onClose() {
    search.dispose();
    super.onClose();
  }
}
