import "package:dio/dio.dart";

import "package:davos_admin/core/constants/urls.dart";
import "package:davos_admin/core/interceptors/session_interceptor.dart";
import "package:davos_admin/core/services/storage_service/storage_service.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/features/assistant/model/assistant_models.dart";
import "package:davos_admin/features/auth/model/admin_me.dart";
import "package:davos_admin/features/customers/model/customer.dart";
import "package:davos_admin/features/dashboard/model/dashboard_summary.dart";
import "package:davos_admin/features/payments/model/admin_payment.dart";
import "package:davos_admin/features/reservations/model/reservation.dart";
import "package:davos_admin/features/settings/model/schedule_settings.dart";
import "package:davos_admin/features/sms/model/sms_models.dart";
import "package:davos_admin/features/system/model/system_status.dart";
import "package:davos_admin/features/users/model/panel_user.dart";
import "package:davos_admin/shared/models/json_read.dart";

part "api_service_accounting.dart";
part "api_service_admin.dart";
part "api_service_assistant.dart";
part "api_service_reservations.dart";

/// A failed API call, with the message ready to show. The server's own messages are Persian and safe to display as they
/// are; everything else gets a fixed Persian text.
class ApiError implements Exception {
  ApiError(this.message, {this.status = 0, this.code = "error", this.fields = const {}});

  final String message;
  final int status;
  final String code;

  /// Field name -> message, for validation errors (HTTP 422).
  final Map<String, String> fields;

  bool get isUnauthenticated => status == 401;

  @override
  String toString() => message;
}

const String networkErrorText =
    "ارتباط با سرور برقرار نشد. اتصال اینترنت را بررسی کنید و دوباره تلاش کنید.";
const String serverErrorText = "خطایی در سرور رخ داد. کمی بعد دوباره تلاش کنید.";

/// The text to show for any thrown error.
String errorMessage(Object error) =>
    error is ApiError ? error.message : serverErrorText;

/// Every HTTP call the app makes.
///
/// A singleton, so there is one Dio and one session interceptor. Dio has no baseUrl (see urls.dart) and every
/// method takes a full URL. Methods throw [ApiError]; controllers catch it and show [ApiError.message].
class ApiService {
  ApiService._internal() {
    dio = Dio(
      BaseOptions(
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 30),
        sendTimeout: const Duration(seconds: 30),
        headers: {"Accept": "application/json"},
        validateStatus: (status) => status != null && status < 400,
      ),
    );
    dio.interceptors.add(SessionInterceptor(_storage));
  }

  static final ApiService _instance = ApiService._internal();

  factory ApiService() => _instance;

  late final Dio dio;
  final StorageService _storage = StorageService();

  /// Replaces the HTTP client (tests plug a fake in here).
  void useAdapter(HttpClientAdapter adapter) => dio.httpClientAdapter = adapter;

  Future<dynamic> get(String url, {Map<String, dynamic>? query}) =>
      _send("GET", url, query: query);

  Future<dynamic> post(String url, {Object? body, bool signIn = false}) =>
      _send("POST", url, body: body, signIn: signIn);

  Future<dynamic> put(String url, {Object? body}) =>
      _send("PUT", url, body: body);

  Future<dynamic> delete(String url) => _send("DELETE", url);

  Future<dynamic> _send(
    String method,
    String url, {
    Object? body,
    Map<String, dynamic>? query,
    bool signIn = false,
  }) async {
    try {
      final response = await dio.request<dynamic>(
        url,
        data: body,
        queryParameters: _clean(query),
        options: Options(method: method, extra: {"signIn": signIn}),
      );
      return response.data;
    } on DioException catch (error) {
      throw _toError(error);
    }
  }

  /// Drops empty filters so the URL only carries what the user actually chose.
  Map<String, dynamic>? _clean(Map<String, dynamic>? query) {
    if (query == null) return null;
    final out = <String, dynamic>{};
    query.forEach((key, value) {
      if (value == null || value == "") return;
      out[key] = value is bool ? value.toString() : value;
    });
    return out;
  }

  ApiError _toError(DioException error) {
    final response = error.response;
    if (response == null) {
      return ApiError(networkErrorText);
    }
    final status = response.statusCode ?? 0;
    final data = response.data;
    if (data is Map) {
      final message = data["message"];
      final fields = <String, String>{};
      final details = data["details"];
      if (details is List) {
        for (final item in details) {
          if (item is Map && item["field"] is String && item["message"] is String) {
            fields[item["field"] as String] = item["message"] as String;
          }
        }
      }
      return ApiError(
        message is String && status < 500 ? message : serverErrorText,
        status: status,
        code: data["code"] is String ? data["code"] as String : "error",
        fields: fields,
      );
    }
    if (status == 429) {
      return ApiError(
        "تعداد درخواست‌ها زیاد است. کمی صبر کنید و دوباره تلاش کنید.",
        status: 429,
        code: "rate_limited",
      );
    }
    return ApiError(
      status >= 500 ? serverErrorText : "درخواست انجام نشد.",
      status: status,
    );
  }
}
