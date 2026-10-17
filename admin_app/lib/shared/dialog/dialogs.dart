import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/shared/widgets/app_button.dart";

/// Yes/no question. Returns true only when the user confirms.
Future<bool> confirm(
  BuildContext context, {
  required String title,
  required String message,
  String confirmLabel = "تایید",
  bool danger = false,
}) async {
  final result = await showDialog<bool>(
    context: context,
    builder: (dialogContext) => Directionality(
      textDirection: TextDirection.rtl,
      child: Dialog(
        child: Padding(
          padding: const EdgeInsets.all(22),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
              const SizedBox(height: 10),
              Text(message, style: TextStyle(height: 1.8, color: dialogContext.pit.mid)),
              const SizedBox(height: 22),
              Row(
                children: [
                  Expanded(child: AppButton(label: "انصراف", outlined: true, onPressed: () => Navigator.of(dialogContext).pop(false))),
                  const SizedBox(width: 10),
                  Expanded(child: AppButton(label: confirmLabel, danger: danger, onPressed: () => Navigator.of(dialogContext).pop(true))),
                ],
              ),
            ],
          ),
        ),
      ),
    ),
  );
  return result ?? false;
}

/// A tall bottom sheet with a title for forms. [builder] receives the sheet's context (close it with
/// `Navigator.of(context).pop()`, not Get.back(), which would close a snackbar first and leave the sheet open).
Future<T?> showFormSheet<T>(BuildContext context, {required String title, required WidgetBuilder builder}) {
  return showModalBottomSheet<T>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    showDragHandle: true,
    builder: (sheetContext) => Directionality(
      textDirection: TextDirection.rtl,
      child: Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(sheetContext).viewInsets.bottom),
        child: DraggableScrollableSheet(
          expand: false,
          initialChildSize: 0.9,
          minChildSize: 0.5,
          maxChildSize: 0.95,
          builder: (_, scroll) => ListView(
            controller: scroll,
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 28),
            children: [
              Padding(
                padding: const EdgeInsets.only(bottom: 18),
                child: Text(title, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700)),
              ),
              builder(sheetContext),
            ],
          ),
        ),
      ),
    ),
  );
}

/// A short message floating above the bottom bar.
void toast(String message, {bool error = false}) {
  Get.closeAllSnackbars();
  final color = error ? AppColors.danger : AppColors.success;
  Get.rawSnackbar(
    messageText: Row(
      children: [
        Icon(error ? Icons.error_rounded : Icons.check_circle_rounded, color: color, size: 22),
        const SizedBox(width: 10),
        Expanded(
          child: Text(message, textDirection: TextDirection.rtl, style: const TextStyle(color: Color(0xFFF4F4F1), height: 1.6, fontSize: 13.5, fontWeight: FontWeight.w500)),
        ),
      ],
    ),
    backgroundColor: const Color(0xFF1F222A),
    margin: const EdgeInsets.fromLTRB(16, 16, 16, 100),
    borderRadius: 18,
    borderColor: color.withValues(alpha: 0.4),
    borderWidth: 1,
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    duration: Duration(seconds: error ? 5 : 3),
    snackPosition: SnackPosition.BOTTOM,
    animationDuration: const Duration(milliseconds: 350),
  );
}
