import "dart:async";

import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/features/reservations/model/reservation.dart";

/// Find a ticket by number, code, name or mobile while typing (the counter's "who is this?" tool).
class TicketSearchController extends GetxController {
  final TextEditingController text = TextEditingController();
  final RxList<Reservation> results = <Reservation>[].obs;
  final RxBool searching = false.obs;
  final RxBool searched = false.obs;
  final Rxn<String> error = Rxn<String>();
  Timer? _debounce;
  int _serial = 0;

  void onChanged(String value) {
    _debounce?.cancel();
    if (latin(value.trim()).isEmpty) {
      results.clear();
      searched.value = false;
      searching.value = false;
      return;
    }
    searching.value = true;
    _debounce = Timer(const Duration(milliseconds: 350), search);
  }

  Future<void> search() async {
    final query = latin(text.text.trim());
    if (query.isEmpty) return;
    final mine = ++_serial;
    searching.value = true;
    error.value = null;
    try {
      final page = await ApiService().getReservations(q: query, limit: 40);
      if (mine != _serial) return;
      results.assignAll(page.items);
      searched.value = true;
    } catch (e) {
      if (mine == _serial) error.value = errorMessage(e);
    } finally {
      if (mine == _serial) searching.value = false;
    }
  }

  @override
  void onClose() {
    _debounce?.cancel();
    text.dispose();
    super.onClose();
  }
}
