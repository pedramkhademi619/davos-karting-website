import "package:flutter/material.dart";

import "package:davos_admin/core/theme/pit.dart";

/// A search field with a clear button; calls [onSearch] on submit.
class SearchBox extends StatelessWidget {
  const SearchBox({super.key, required this.controller, required this.onSearch, this.hint = "جستجو", this.onChanged, this.autofocus = false});

  final TextEditingController controller;
  final ValueChanged<String> onSearch;
  final ValueChanged<String>? onChanged;
  final String hint;
  final bool autofocus;

  @override
  Widget build(BuildContext context) => TextField(
    controller: controller,
    autofocus: autofocus,
    textInputAction: TextInputAction.search,
    onSubmitted: onSearch,
    onChanged: onChanged,
    decoration: InputDecoration(
      hintText: hint,
      prefixIcon: Icon(Icons.search_rounded, color: context.pit.mid),
      suffixIcon: IconButton(
        icon: const Icon(Icons.close_rounded, size: 18),
        onPressed: () {
          controller.clear();
          onSearch("");
        },
      ),
    ),
  );
}
