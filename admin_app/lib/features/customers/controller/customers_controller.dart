import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/customers/model/customer.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";

class CustomersController extends PagedController<Customer> {
  final TextEditingController search = TextEditingController();
  String _query = "";

  @override
  Future<void> fetchPage(int offset) async {
    final page = await ApiService().getCustomers(q: _query, offset: offset, limit: pageSize);
    items.assignAll(page.items);
    total.value = page.total;
  }

  Future<void> submitSearch(String text) {
    _query = text.trim();
    return restart();
  }

  Future<void> toggleBlock(Customer customer) async {
    final message = await guard(() => ApiService().setCustomerStatus(customer.userId, customer.blocked ? "active" : "blocked"));
    if (message != null) {
      toast(message, error: true);
      return;
    }
    toast(customer.blocked ? "مشتری آزاد شد." : "مشتری مسدود شد.");
    await reload();
  }

  @override
  void onClose() {
    search.dispose();
    super.onClose();
  }
}
