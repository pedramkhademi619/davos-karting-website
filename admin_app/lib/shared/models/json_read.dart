/// Tolerant readers for the API's JSON. A missing or null field becomes a harmless default instead of an exception, so
/// one new field on the server can never blank a whole screen.
typedef Json = Map<String, dynamic>;

extension JsonRead on Map<String, dynamic> {
  String str(String key, [String fallback = ""]) {
    final value = this[key];
    return value == null ? fallback : value.toString();
  }

  String? strOrNull(String key) {
    return this[key]?.toString();
  }

  int integer(String key, [int fallback = 0]) {
    final value = this[key];
    if (value is num) return value.toInt();
    return int.tryParse(value?.toString() ?? "") ?? fallback;
  }

  int? integerOrNull(String key) {
    final value = this[key];
    if (value == null) return null;
    if (value is num) return value.toInt();
    return int.tryParse(value.toString());
  }

  double number(String key, [double fallback = 0]) {
    final value = this[key];
    if (value is num) return value.toDouble();
    return double.tryParse(value?.toString() ?? "") ?? fallback;
  }

  bool flag(String key, [bool fallback = false]) {
    final value = this[key];
    return value is bool ? value : fallback;
  }

  bool? flagOrNull(String key) {
    final value = this[key];
    return value is bool ? value : null;
  }

  Json obj(String key) {
    final value = this[key];
    return value is Map ? Map<String, dynamic>.from(value) : <String, dynamic>{};
  }

  List<Json> list(String key) => asJsonList(this[key]);

  List<String> strings(String key) {
    final value = this[key];
    return value is List ? value.map((e) => e.toString()).toList() : <String>[];
  }
}

List<Json> asJsonList(Object? value) => value is List
    ? value.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList()
    : <Json>[];

/// {items, total} as most list endpoints return it.
class PageResult<T> {
  const PageResult({required this.items, required this.total, this.extra = const {}});

  final List<T> items;
  final int total;

  /// Anything else the page carried (the payments page adds a paid total).
  final Json extra;

  static PageResult<T> parse<T>(Object? body, T Function(Json) read) {
    final json = body is Map ? Map<String, dynamic>.from(body) : <String, dynamic>{};
    final items = json.list("items").map(read).toList();
    return PageResult<T>(items: items, total: json.integer("total", items.length), extra: json);
  }
}
