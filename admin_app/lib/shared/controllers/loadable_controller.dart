import "package:get/get.dart";

import "package:davos_admin/core/constants/constants.dart";
import "package:davos_admin/core/services/api_service/api_service.dart";

/// Base for a screen that loads something: exposes `loading` and `error` so the view can show the right state, and
/// [guard] to run an action with the same error handling everywhere.
abstract class LoadableController extends GetxController {
  final RxBool loading = false.obs;
  final Rxn<String> error = Rxn<String>();

  /// What this screen fetches. Implementations set their own observables.
  Future<void> fetch();

  @override
  void onReady() {
    super.onReady();
    reload();
  }

  /// Runs [fetch] showing the spinner and capturing a failure as [error].
  Future<void> reload() async {
    loading.value = true;
    error.value = null;
    try {
      await fetch();
    } on ApiError catch (e) {
      error.value = e.message;
    } catch (_) {
      error.value = serverErrorText;
    } finally {
      loading.value = false;
    }
  }

  /// Runs an action that changes something. Returns null on success or the message to show.
  Future<String?> guard(Future<void> Function() action) async {
    try {
      await action();
      return null;
    } on ApiError catch (e) {
      return e.message;
    } catch (_) {
      return serverErrorText;
    }
  }
}

/// A [LoadableController] over a paged list: `items`, `total`, and next/previous page.
abstract class PagedController<T> extends LoadableController {
  final RxList<T> items = <T>[].obs;
  final RxInt total = 0.obs;
  final RxInt offset = 0.obs;

  int get pageSize => Constants.pageSize;

  /// One page starting at [offset]. Must fill [items] and [total].
  Future<void> fetchPage(int offset);

  @override
  Future<void> fetch() => fetchPage(offset.value);

  bool get hasPrevious => offset.value > 0;
  bool get hasNext => offset.value + pageSize < total.value;

  Future<void> restart() {
    offset.value = 0;
    return reload();
  }

  Future<void> next() {
    if (!hasNext) return Future.value();
    offset.value += pageSize;
    return reload();
  }

  Future<void> previous() {
    if (!hasPrevious) return Future.value();
    offset.value = (offset.value - pageSize).clamp(0, 1 << 30);
    return reload();
  }
}
