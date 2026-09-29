from __future__ import annotations

import math


class WilsonInterval:
    """95 % Wilson score interval for a pass rate: honest for small samples and rates near 100 %, where the normal
    approximation would claim an interval above 1."""

    Z = 1.959964

    @classmethod
    def of(cls, passed: int, total: int) -> tuple[float, float]:
        if total == 0:
            return (0.0, 0.0)
        p = passed / total
        z2 = cls.Z * cls.Z
        centre = (p + z2 / (2 * total)) / (1 + z2 / total)
        half = cls.Z * math.sqrt(p * (1 - p) / total + z2 / (4 * total * total)) / (1 + z2 / total)
        return (max(0.0, centre - half), min(1.0, centre + half))
