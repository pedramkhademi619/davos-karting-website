import "package:get/get.dart";

/// Which tab of the bottom bar is open.
class ShellController extends GetxController {
  final RxInt index = 0.obs;

  /// The last tab ("More"), whatever number of tabs the person has.
  int lastIndex = 3;

  void open(int tab) => index.value = tab;
}
