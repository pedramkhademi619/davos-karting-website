part of "api_service.dart";

extension ApiServiceReservations on ApiService {
  Future<PageResult<Reservation>> getReservations({
    String? dateFrom,
    String? dateTo,
    String status = "",
    String q = "",
    int offset = 0,
    int limit = 50,
  }) async => PageResult.parse(
    await get(
      Urls.reservations,
      query: {"date_from": dateFrom, "date_to": dateTo, "status": status, "q": q, "offset": offset, "limit": limit},
    ),
    Reservation.fromJson,
  );

  Future<DayBoard> getBoard(String date) async =>
      DayBoard.fromJson(Map<String, dynamic>.from(await get(Urls.reservationBoard, query: {"date": date}) as Map));

  Future<Reservation> createCounterReservation({
    required String date,
    required String time,
    required int singles,
    required int doubles,
    required String name,
    required String mobile,
    required String note,
    required int amountToman,
    required bool allowOverbooking,
    required String paymentMethod,
  }) async => Reservation.fromJson(
    Map<String, dynamic>.from(
      await post(
        Urls.reservations,
        body: {
          "date": date,
          "time": time,
          "single_count": singles,
          "double_count": doubles,
          "contact_name": name,
          "contact_mobile": mobile,
          "note": note,
          "amount_toman": amountToman,
          "allow_overbooking": allowOverbooking,
          "payment_method": paymentMethod,
        },
      ) as Map,
    ),
  );

  Future<void> cancelReservation(String id, String reason) =>
      post("${Urls.reservationItem}$id/cancel", body: {"reason": reason});

  Future<void> markAttended(String id) => post("${Urls.reservationItem}$id/attended");
}
