import "package:flutter/material.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/skeleton.dart";

/// The states every data screen has: loading (a skeleton), error (always with a retry) and empty. A failed load never
/// looks like "no data", so the two are separate.
class StateView extends StatelessWidget {
  const StateView({super.key, required this.icon, required this.message, this.color, this.actionLabel, this.onAction});

  factory StateView.error(String message, {VoidCallback? onRetry}) => StateView(
    icon: Icons.cloud_off_rounded,
    message: message,
    color: AppColors.danger,
    actionLabel: onRetry == null ? null : "تلاش دوباره",
    onAction: onRetry,
  );

  factory StateView.empty(String message, {String? actionLabel, VoidCallback? onAction, IconData icon = Icons.inbox_rounded}) =>
      StateView(icon: icon, message: message, actionLabel: actionLabel, onAction: onAction);

  final IconData icon;
  final String message;
  final Color? color;
  final String? actionLabel;
  final VoidCallback? onAction;

  /// A skeleton screen.
  static Widget loading() => const SkeletonList();

  /// Maps a controller's flags to the right state, or null when there is data to show:
  /// `StateView.from(...) ?? TheList(...)`.
  static Widget? from({
    required bool loading,
    required bool isEmpty,
    String? error,
    required String emptyMessage,
    VoidCallback? onRetry,
  }) {
    if (loading && isEmpty) return StateView.loading();
    if (error != null && isEmpty) return StateView.error(error, onRetry: onRetry);
    if (isEmpty) return StateView.empty(emptyMessage);
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final tint = color ?? p.low;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 84,
              height: 84,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: tint.withValues(alpha: 0.12),
                border: Border.all(color: tint.withValues(alpha: 0.25)),
              ),
              child: Icon(icon, size: 36, color: tint),
            ),
            const SizedBox(height: 18),
            Text(message, textAlign: TextAlign.center, style: TextStyle(color: p.mid, height: 1.8, fontSize: 14)),
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 18),
              AppButton(label: actionLabel!, onPressed: onAction, outlined: true, expand: false, small: true),
            ],
          ],
        ),
      ),
    );
  }
}
