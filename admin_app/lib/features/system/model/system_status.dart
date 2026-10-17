import "package:davos_admin/shared/models/json_read.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

/// ok, degraded, down, disabled or test.
const Map<String, String> levelLabels = {
  "ok": "سالم",
  "degraded": "نیازمند توجه",
  "down": "از کار افتاده",
  "disabled": "غیرفعال",
  "test": "حالت آزمایشی",
};

Tone levelTone(String level) => switch (level) {
  "ok" => Tone.success,
  "degraded" || "test" => Tone.warning,
  "down" => Tone.danger,
  _ => Tone.neutral,
};

class ServicePart {
  const ServicePart({required this.label, required this.level, required this.detail});

  factory ServicePart.fromJson(Json j) =>
      ServicePart(label: j.str("label"), level: j.str("level"), detail: j.str("detail"));

  final String label;
  final String level;
  final String detail;
}

class ServiceStatus {
  const ServiceStatus({
    required this.key,
    required this.group,
    required this.label,
    required this.level,
    required this.summary,
    required this.latencyMs,
    required this.parts,
  });

  factory ServiceStatus.fromJson(Json j) => ServiceStatus(
    key: j.str("key"),
    group: j.str("group"),
    label: j.str("label"),
    level: j.str("level"),
    summary: j.str("summary"),
    latencyMs: j.integerOrNull("latency_ms"),
    parts: j.list("parts").map(ServicePart.fromJson).toList(),
  );

  final String key;
  final String group;
  final String label;
  final String level;
  final String summary;
  final int? latencyMs;
  final List<ServicePart> parts;
}

class SystemStatus {
  const SystemStatus({required this.overall, required this.checkedAt, required this.services});

  factory SystemStatus.fromJson(Json j) => SystemStatus(
    overall: j.str("overall"),
    checkedAt: j.str("checked_at"),
    services: j.list("services").map(ServiceStatus.fromJson).toList(),
  );

  final String overall;
  final String checkedAt;
  final List<ServiceStatus> services;
}
