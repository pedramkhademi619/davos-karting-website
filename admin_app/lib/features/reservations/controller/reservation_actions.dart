import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/features/reservations/model/reservation.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_button.dart";

/// The two things done to a ticket at the counter. Each returns true when something changed, so the screen can reload.
abstract class ReservationActions {
  static Future<bool> checkIn(Reservation r) async {
    try {
      await ApiService().markAttended(r.id);
      HapticFeedback.mediumImpact();
      toast("ورود بلیت ${fa(r.ticketNumber)} ثبت شد.");
      return true;
    } catch (e) {
      toast(errorMessage(e), error: true);
      return false;
    }
  }

  /// Asks for a reason (a paid ticket warns that the money must be refunded), then cancels.
  static Future<bool> cancel(BuildContext context, Reservation r) async {
    final reason = TextEditingController();
    final yes = await showDialog<bool>(
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
                Text("لغو بلیت ${fa(r.ticketNumber)}", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                const SizedBox(height: 10),
                Text(
                  r.status == "confirmed" && r.isOnline
                      ? "این رزرو آنلاین پرداخت شده است؛ بعد از لغو باید مبلغ به مشتری برگردانده شود."
                      : "رزرو لغو می‌شود و ظرفیتش آزاد می‌شود.",
                  style: TextStyle(height: 1.8, color: dialogContext.pit.mid),
                ),
                const SizedBox(height: 14),
                TextField(controller: reason, decoration: const InputDecoration(hintText: "دلیل لغو (اختیاری)")),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(child: AppButton(label: "بازگشت", outlined: true, onPressed: () => Navigator.of(dialogContext).pop(false))),
                    const SizedBox(width: 10),
                    Expanded(child: AppButton(label: "لغو رزرو", danger: true, onPressed: () => Navigator.of(dialogContext).pop(true))),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
    final text = reason.text.trim();
    reason.dispose();
    if (yes != true) return false;
    try {
      await ApiService().cancelReservation(r.id, text);
      toast("بلیت ${fa(r.ticketNumber)} لغو شد.");
      return true;
    } catch (e) {
      toast(errorMessage(e), error: true);
      return false;
    }
  }
}
