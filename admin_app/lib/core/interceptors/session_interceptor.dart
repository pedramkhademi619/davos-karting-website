import "package:dio/dio.dart";

import "package:davos_admin/core/services/storage_service/storage_service.dart";

/// The staff session lives in a cookie (httpOnly on the web, so the browser handles it there). A native app has no
/// cookie jar, so this interceptor plays that part: it keeps whatever the server sets, sends it back, and adds the CSRF
/// token the API demands on every state-changing call.
class SessionHolder {
  static final Map<String, String> cookies = {};
  static String? csrfToken;

  /// Called when the server says the session is gone (401 on a call that is not the sign-in itself).
  static void Function()? onExpired;

  static bool get hasSession => cookies.isNotEmpty;

  static String get cookieHeader =>
      cookies.entries.map((e) => "${e.key}=${e.value}").join("; ");

  static void clear() {
    cookies.clear();
    csrfToken = null;
  }

  /// "a=1; b=2" -> cookies map (the form persisted in secure storage).
  static void restore(String? header, String? csrf) {
    cookies.clear();
    if (header != null && header.isNotEmpty) {
      for (final part in header.split(";")) {
        final index = part.indexOf("=");
        if (index <= 0) continue;
        cookies[part.substring(0, index).trim()] = part.substring(index + 1).trim();
      }
    }
    csrfToken = csrf;
  }
}

class SessionInterceptor extends Interceptor {
  SessionInterceptor(this._storage);

  final StorageService _storage;

  static const _safeMethods = {"GET", "HEAD", "OPTIONS"};

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (SessionHolder.hasSession) {
      options.headers["Cookie"] = SessionHolder.cookieHeader;
    }
    final csrf = SessionHolder.csrfToken;
    if (csrf != null && !_safeMethods.contains(options.method.toUpperCase())) {
      options.headers["X-CSRF-Token"] = csrf;
    }
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    final setCookies = response.headers.map["set-cookie"];
    if (setCookies != null && setCookies.isNotEmpty) {
      var changed = false;
      for (final raw in setCookies) {
        final first = raw.split(";").first;
        final index = first.indexOf("=");
        if (index <= 0) continue;
        final name = first.substring(0, index).trim();
        final value = first.substring(index + 1).trim();
        final lower = raw.toLowerCase();
        final deleted = value.isEmpty || lower.contains("max-age=0") || value == '""';
        if (deleted) {
          changed = SessionHolder.cookies.remove(name) != null || changed;
        } else {
          SessionHolder.cookies[name] = value;
          changed = true;
        }
      }
      if (changed) {
        _storage.writeSession(cookie: SessionHolder.cookieHeader);
      }
    }
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final isSignIn = err.requestOptions.extra["signIn"] == true;
    if (err.response?.statusCode == 401 && !isSignIn) {
      SessionHolder.onExpired?.call();
    }
    handler.next(err);
  }
}
