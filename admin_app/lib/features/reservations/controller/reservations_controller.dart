import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/reservations/model/reservation.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";
import "package:davos_admin/shared/models/json_read.dart";

/// One day of the board (sessions with free karts) and the tickets of that day.
class ReservationsController extends LoadableController {
  final RxString day = businessDayIso().obs;
  final Rxn<DayBoard> board = Rxn<DayBoard>();
  final RxList<Reservation> reservations = <Reservation>[].obs;

  /// "all", "confirmed", "attended", "held" or "cancelled".
  final RxString filter = "all".obs;

  @override
  Future<void> fetch() async {
    final api = ApiService();
    final loaded = await Future.wait([
      api.getBoard(day.value),
      api.getReservations(dateFrom: day.value, dateTo: day.value, limit: 200),
    ]);
    board.value = loaded[0] as DayBoard;
    reservations.assignAll((loaded[1] as PageResult<Reservation>).items);
  }

  Future<void> setDay(String iso) {
    day.value = iso;
    return reload();
  }

  /// Tickets passing the status filter.
  List<Reservation> get visible {
    switch (filter.value) {
      case "confirmed":
        return reservations.where((r) => r.status == "confirmed").toList();
      case "attended":
        return reservations.where((r) => r.status == "attended").toList();
      case "held":
        return reservations.where((r) => r.status == "held").toList();
      case "cancelled":
        return reservations.where((r) => r.status == "cancelled" || r.status == "expired").toList();
      default:
        return reservations.toList();
    }
  }

  /// Tickets that count towards the day (not cancelled or expired).
  List<Reservation> get live => reservations.where((r) => r.status == "confirmed" || r.status == "attended" || r.status == "held").toList();

  int get ticketCount => live.length;
  int get kartCount => live.fold(0, (s, r) => s + r.karts);
  int get peopleCount => live.fold(0, (s, r) => s + r.people);
  int get revenueToman => live.where((r) => r.status != "held").fold(0, (s, r) => s + r.amountToman);
}
