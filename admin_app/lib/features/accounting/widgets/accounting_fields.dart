import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/features/accounting/controller/accounting_data_controller.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";

/// A drop-down of accounts from the shared chart.
class AccountField extends StatelessWidget {
  const AccountField({
    super.key,
    required this.label,
    required this.value,
    required this.onChanged,
    this.type,
    this.where,
    this.optional = false,
  });

  final String label;
  final String? value;
  final ValueChanged<String?> onChanged;
  final String? type;
  final bool Function(Account)? where;
  final bool optional;

  @override
  Widget build(BuildContext context) {
    final data = Get.find<AccountingDataController>();
    return Obx(() {
      final options = data.options(data.postable(type: type, where: where));
      return ChoiceField<String>(
        label: optional ? "$label (اختیاری)" : label,
        value: value,
        options: {if (optional) "": "—", ...options},
        onChanged: (v) => onChanged(v == "" ? null : v),
      );
    });
  }
}

/// A drop-down of suppliers.
class VendorField extends StatelessWidget {
  const VendorField({super.key, required this.value, required this.onChanged, this.label = "تامین‌کننده", this.optional = true});

  final String? value;
  final ValueChanged<String?> onChanged;
  final String label;
  final bool optional;

  @override
  Widget build(BuildContext context) {
    final data = Get.find<AccountingDataController>();
    return Obx(
      () => ChoiceField<String>(
        label: optional ? "$label (اختیاری)" : label,
        value: value,
        options: {if (optional) "": "—", ...data.vendorOptions},
        onChanged: (v) => onChanged(v == "" ? null : v),
      ),
    );
  }
}
