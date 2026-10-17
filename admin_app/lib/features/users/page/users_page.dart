import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/auth/controller/session_controller.dart";
import "package:davos_admin/features/users/controller/users_controller.dart";
import "package:davos_admin/features/users/model/panel_user.dart";
import "package:davos_admin/features/users/page/permission_picker.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/state_view.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

class UsersPage extends GetView<UsersController> {
  const UsersPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("کاربران پنل")),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _create(context),
        icon: const Icon(Icons.person_add_alt_1_rounded),
        label: const Text("افزودن کاربر"),
      ),
      body: Obx(() {
        final state = StateView.from(
          loading: controller.loading.value,
          isEmpty: controller.users.isEmpty,
          error: controller.error.value,
          emptyMessage: "کاربری ثبت نشده است.",
          onRetry: controller.reload,
        );
        if (state != null) return state;
        final myId = Get.find<SessionController>().me.value?.adminId;
        return RefreshIndicator(
          onRefresh: controller.reload,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
            children: [
              for (final user in controller.users)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: AppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(child: Text(user.shownName, style: const TextStyle(fontWeight: FontWeight.w800))),
                            StatusChip(user.isOwner ? "مدیر" : "کارمند", tone: user.isOwner ? Tone.info : Tone.neutral),
                            const SizedBox(width: 6),
                            StatusChip(user.isActive ? "فعال" : "غیرفعال", tone: user.isActive ? Tone.success : Tone.danger),
                          ],
                        ),
                        Text(user.username, textDirection: TextDirection.ltr, style: TextStyle(color: Theme.of(context).hintColor)),
                        const SizedBox(height: 4),
                        Text("آخرین ورود: ${user.lastLoginAt == null ? "—" : jalaliDateTime(user.lastLoginAt)}", style: const TextStyle(fontSize: 12)),
                        if (!user.isOwner) ...[
                          const SizedBox(height: 6),
                          Text(
                            user.customPermissions ? "دسترسی‌ها: ${_labels(user)}" : "دسترسی‌ها: پیش‌فرض کارمند",
                            style: const TextStyle(fontSize: 12, height: 1.7),
                          ),
                          Row(
                            children: [
                              TextButton(onPressed: () => _editPermissions(context, user), child: const Text("تعیین دسترسی")),
                              if (user.adminId != myId)
                                TextButton(
                                  onPressed: () async {
                                    final message = await controller.setActive(user, !user.isActive);
                                    if (message != null) toast(message, error: true);
                                  },
                                  child: Text(user.isActive ? "غیرفعال کردن" : "فعال کردن"),
                                ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
            ],
          ),
        );
      }),
    );
  }

  String _labels(PanelUser user) {
    final catalog = controller.catalog.value;
    if (catalog == null) return user.permissions.join("، ");
    final names = {for (final e in catalog.entries) e.key: e.label};
    return user.permissions.map((k) => names[k] ?? k).join("، ");
  }

  void _editPermissions(BuildContext context, PanelUser user) {
    final catalog = controller.catalog.value;
    if (catalog == null) return;
    var keys = List<String>.from(user.permissions);
    var busy = false;
    String? error;
    showFormSheet<void>(
      context,
      title: "دسترسی‌های ${user.shownName}",
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setState) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            PermissionPicker(catalog: catalog, value: keys, onChanged: (v) => setState(() => keys = v)),
            if (error != null) MessageBar(error!, error: true),
            const SizedBox(height: 8),
            AppButton(
              label: "ذخیره",
              busy: busy,
              onPressed: () async {
                setState(() => busy = true);
                final message = await controller.savePermissions(user, keys);
                if (!sheetContext.mounted) return;
                if (message == null) {
                  Navigator.of(sheetContext).pop();
                  toast("دسترسی‌ها ذخیره شد.");
                } else {
                  setState(() {
                    busy = false;
                    error = message;
                  });
                }
              },
            ),
            const SizedBox(height: 8),
            AppButton(
              label: "برگرداندن به پیش‌فرض کارمند",
              outlined: true,
              onPressed: busy
                  ? null
                  : () async {
                      final message = await controller.savePermissions(user, null);
                      if (!sheetContext.mounted) return;
                      if (message == null) {
                        Navigator.of(sheetContext).pop();
                        toast("دسترسی‌ها به پیش‌فرض برگشت.");
                      } else {
                        setState(() => error = message);
                      }
                    },
            ),
          ],
        ),
      ),
    );
  }

  void _create(BuildContext context) {
    final catalog = controller.catalog.value;
    if (catalog == null) return;
    final username = TextEditingController();
    final displayName = TextEditingController();
    final password = TextEditingController();
    var role = "staff";
    var keys = catalog.entries.where((e) => e.defaultForStaff).map((e) => e.key).toList();
    var busy = false;
    String? error;
    showFormSheet<void>(
      context,
      title: "افزودن کاربر",
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setState) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            LabeledField(label: "نام کاربری (انگلیسی)", controller: username, ltr: true),
            LabeledField(label: "نام نمایشی", controller: displayName),
            LabeledField(label: "رمز عبور (حداقل ۱۰ نویسه)", controller: password, password: true),
            ChoiceField<String>(
              label: "نقش",
              value: role,
              options: const {"staff": "کارمند", "owner": "مدیر (دسترسی کامل)"},
              onChanged: (v) => setState(() => role = v ?? "staff"),
            ),
            if (role == "staff") PermissionPicker(catalog: catalog, value: keys, onChanged: (v) => setState(() => keys = v)),
            if (error != null) MessageBar(error!, error: true),
            const SizedBox(height: 8),
            AppButton(
              label: "افزودن",
              busy: busy,
              onPressed: () async {
                setState(() {
                  busy = true;
                  error = null;
                });
                final message = await controller.create(
                  username: username.text.trim(),
                  displayName: displayName.text.trim(),
                  password: password.text,
                  role: role,
                  permissions: keys,
                );
                if (!sheetContext.mounted) return;
                if (message == null) {
                  Navigator.of(sheetContext).pop();
                  toast("کاربر اضافه شد.");
                } else {
                  setState(() {
                    busy = false;
                    error = message;
                  });
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}
