import "package:flutter_test/flutter_test.dart";

import "package:davos_admin/core/constants/urls.dart";
import "package:davos_admin/core/interceptors/session_interceptor.dart";
import "package:davos_admin/core/services/api_service/api_service.dart";

import "helpers/fake_server.dart";

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  final api = ApiService();

  setUp(SessionHolder.clear);

  test("sign-in keeps the session cookie and every later call sends it, with the CSRF token on writes", () async {
    final server = FakeServer({
      "POST /api/v1/admin/auth/login": const FakeResponse(meJson, headers: {
        "set-cookie": ["davos_admin=tok123; Path=/api/v1/admin; HttpOnly; SameSite=Strict"],
      }),
      "GET /api/v1/admin/dashboard": const FakeResponse({"today_confirmed": 3}),
      "POST /api/v1/admin/reservations/r1/attended": const FakeResponse({}),
    });
    api.useAdapter(server);

    final me = await api.signIn("owner", "pw");
    SessionHolder.csrfToken = me.csrfToken;
    expect(me.shownName, "مدیر تست");
    expect(me.isOwner, isTrue);
    expect(SessionHolder.cookies["davos_admin"], "tok123");

    await api.getDashboard();
    await api.markAttended("r1");

    final read = server.seen.firstWhere((s) => s.method == "GET");
    expect(read.headers["Cookie"], "davos_admin=tok123");
    expect(read.headers.containsKey("X-CSRF-Token"), isFalse);

    final write = server.seen.firstWhere((s) => s.url.endsWith("/attended"));
    expect(write.headers["Cookie"], "davos_admin=tok123");
    expect(write.headers["X-CSRF-Token"], "csrf-123");
  });

  test("a failed call turns the server's Persian message into an ApiError", () async {
    api.useAdapter(
      FakeServer({
        "POST /api/v1/admin/auth/login": const FakeResponse({
          "message": "نام کاربری یا رمز عبور درست نیست.",
          "code": "invalid_credentials",
        }, status: 401),
      }),
    );
    expect(
      api.signIn("x", "y"),
      throwsA(isA<ApiError>().having((e) => e.message, "message", "نام کاربری یا رمز عبور درست نیست.")),
    );
  });

  test("an expired session (401 on a normal call) tells the app to sign out", () async {
    var expired = false;
    SessionHolder.onExpired = () => expired = true;
    api.useAdapter(FakeServer({"GET /api/v1/admin/dashboard": const FakeResponse({"message": "x"}, status: 401)}));
    await expectLater(api.getDashboard(), throwsA(isA<ApiError>()));
    expect(expired, isTrue);
    SessionHolder.onExpired = null;
  });

  test("validation details come back per field", () async {
    api.useAdapter(
      FakeServer({
        "POST ${Uri.parse(Urls.vendors).path}": const FakeResponse({
          "message": "اطلاعات نادرست است.",
          "code": "validation_error",
          "details": [
            {"field": "name", "message": "نام لازم است."},
          ],
        }, status: 422),
      }),
    );
    try {
      await api.saveVendor(name: "", phone: "", note: "", active: true);
      fail("should have thrown");
    } on ApiError catch (e) {
      expect(e.fields["name"], "نام لازم است.");
      expect(e.status, 422);
    }
  });

  test("with no connection the message is the fixed Persian text", () async {
    api.useAdapter(FakeServer({})..routes.clear());
    // An unknown route answers 404 with JSON; a dead network has no response at all.
    expect(errorMessage(ApiError(networkErrorText)), networkErrorText);
  });
}
