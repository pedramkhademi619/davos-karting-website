import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/auth/controller/session_controller.dart";
import "package:davos_admin/features/dashboard/model/dashboard_summary.dart";
import "package:davos_admin/features/reservations/model/reservation.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// Everything the "Today" tab shows. Each part is fetched only if the signed-in person may see it, and one part failing
/// does not blank the others.
class TodayController extends LoadableController {
  final Rxn<DashboardSummary> summary = Rxn<DashboardSummary>();
  final Rxn<DayBoard> board = Rxn<DayBoard>();
  final RxList<Reservation> tickets = <Reservation>[].obs;
  final RxnString systemOverall = RxnString();

  final String day = businessDayIso();

  SessionController get _session => Get.find<SessionController>();

  @override
  Future<void> fetch() async {
    final api = ApiService();
    final jobs = <Future<void>>[];
    final failures = <String>[];
    var attempted = 0;

    void run(Future<void> Function() job) {
      attempted++;
      jobs.add(() async {
        try {
          await job();
        } on ApiError catch (e) {
          failures.add(e.message);
        } catch (_) {
          failures.add(serverErrorText);
        }
      }());
    }

    if (_session.can("dashboard")) run(() async => summary.value = await api.getDashboard());
    if (_session.can("reservations")) {
      run(() async => board.value = await api.getBoard(day));
      run(() async {
        final page = await api.getReservations(dateFrom: day, dateTo: day, limit: 200);
        tickets.assignAll(page.items);
      });
    }
    if (_session.can("system")) {
      // A status check that fails is itself useful information, but it must not hide the rest of the screen.
      jobs.add(() async {
        try {
          systemOverall.value = (await api.getSystemStatus()).overall;
        } catch (_) {
          systemOverall.value = null;
        }
      }());
    }
    await Future.wait(jobs);
    if (attempted > 0 && failures.length == attempted) throw ApiError(failures.first);
  }

  /// Tickets that count towards the day (not cancelled or expired).
  List<Reservation> get live => tickets.where((r) => r.status == "confirmed" || r.status == "attended" || r.status == "held").toList();

  int get attended => tickets.where((r) => r.status == "attended").length;
  int get expected => tickets.where((r) => r.status == "confirmed" || r.status == "attended").length;
  int get people => live.fold(0, (s, r) => s + r.people);
  int get karts => live.fold(0, (s, r) => s + r.karts);
  int get held => tickets.where((r) => r.status == "held").length;

  /// The first open session that has not started yet (Tehran time), or null.
  SessionSlot? nextSession([DateTime? now]) {
    final b = board.value;
    if (b == null) return null;
    final t = (now ?? DateTime.now()).toUtc().add(const Duration(hours: 3, minutes: 30));
    final stamp = "${t.hour.toString().padLeft(2, "0")}:${t.minute.toString().padLeft(2, "0")}";
    final open = b.sessions.where((s) => !s.blocked && s.time.compareTo(stamp) >= 0).toList()..sort((a, c) => a.time.compareTo(c.time));
    return open.isEmpty ? null : open.first;
  }

  /// Anything the owner should look at, most urgent first.
  List<TodayAlert> get alerts {
    final out = <TodayAlert>[];
    final s = summary.value;
    if (systemOverall.value == "down") out.add(const TodayAlert("danger", "یکی از سرویس‌ها از کار افتاده است", "وضعیت سرویس‌ها را ببینید.", "system"));
    if (systemOverall.value == "degraded") out.add(const TodayAlert("warning", "بعضی سرویس‌ها نیاز به توجه دارند", "وضعیت سرویس‌ها را ببینید.", "system"));
    if (s != null && !s.onlineBookingEnabled) out.add(const TodayAlert("warning", "رزرو آنلاین بسته است", "مشتریان از سایت نمی‌توانند رزرو کنند.", "settings"));
    if (s != null && !s.paymentsEnabled) out.add(const TodayAlert("warning", "پرداخت آنلاین غیرفعال است", "رزروها بدون پرداخت تایید نمی‌شوند.", "settings"));
    final heldNow = s?.heldNow ?? held;
    if (heldNow > 0) out.add(TodayAlert("info", "$heldNow رزرو در انتظار پرداخت", "اگر مهلت تمام شود، ظرفیت دوباره آزاد می‌شود.", "reservations"));
    final credit = s?.smsCreditToman;
    if (credit != null && credit < 200000) out.add(const TodayAlert("danger", "اعتبار پیامک رو به پایان است", "برای ارسال کد ورود و تایید رزرو باید شارژ شود.", "sms"));
    return out;
  }
}

/// One line of the "needs attention" list. [tone] is danger/warning/info; [target] is the section it opens.
class TodayAlert {
  const TodayAlert(this.tone, this.title, this.hint, this.target);

  final String tone;
  final String title;
  final String hint;
  final String target;
}
