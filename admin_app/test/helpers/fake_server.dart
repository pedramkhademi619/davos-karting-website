import "dart:convert";
import "dart:typed_data";

import "package:dio/dio.dart";

/// One request the app made, as the fake server saw it.
class Seen {
  Seen(this.method, this.url, this.headers, this.body);

  final String method;
  final String url;
  final Map<String, dynamic> headers;
  final Object? body;
}

/// Stands in for the network: answers by "METHOD path" with a canned JSON body and remembers every request.
class FakeServer implements HttpClientAdapter {
  FakeServer(this.routes);

  /// "GET /api/v1/admin/auth/me" -> response.
  final Map<String, FakeResponse> routes;
  final List<Seen> seen = [];

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    seen.add(Seen(options.method, options.uri.toString(), Map.of(options.headers), options.data));
    final key = "${options.method} ${options.uri.path}";
    final route = routes[key];
    if (route == null) {
      return ResponseBody.fromString(jsonEncode({"message": "پیدا نشد", "code": "not_found"}), 404, headers: {
        Headers.contentTypeHeader: ["application/json"],
      });
    }
    final body = route.json == null ? "" : jsonEncode(route.json);
    return ResponseBody.fromString(body, route.status, headers: {
      Headers.contentTypeHeader: ["application/json"],
      ...route.headers,
    });
  }

  @override
  void close({bool force = false}) {}
}

class FakeResponse {
  const FakeResponse(this.json, {this.status = 200, this.headers = const {}});

  final Object? json;
  final int status;
  final Map<String, List<String>> headers;
}

const meJson = {
  "admin_id": "a1",
  "username": "owner",
  "display_name": "مدیر تست",
  "role": "owner",
  "permissions": ["dashboard", "reservations"],
  "csrf_token": "csrf-123",
};
