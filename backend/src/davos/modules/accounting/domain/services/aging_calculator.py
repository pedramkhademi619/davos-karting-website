from __future__ import annotations

import uuid
from collections import defaultdict, deque
from collections.abc import Sequence
from datetime import date

from davos.modules.accounting.domain.value_objects.party_balance import PartyBalance
from davos.modules.accounting.domain.value_objects.party_line import PartyLine


class AgingCalculator:
    """Ages what is owed to each supplier. Credits are bills, debits are payments; payments settle the oldest bill first
    and the age of what remains is counted from that bill's date."""

    @staticmethod
    def age(lines: Sequence[PartyLine], as_of: date) -> list[PartyBalance]:
        by_party: dict[uuid.UUID, list[PartyLine]] = defaultdict(list)
        for line in lines:
            by_party[line.party_id].append(line)
        result: list[PartyBalance] = []
        for party_id, items in by_party.items():
            bills: deque[tuple[date, int]] = deque()
            advance = 0
            for line in sorted(items, key=lambda item: item.entry_date):
                if line.credit_irr:
                    bills.append((line.entry_date, line.credit_irr))
                paid = line.debit_irr
                while paid and bills:
                    bill_date, remaining = bills.popleft()
                    take = min(paid, remaining)
                    paid -= take
                    if remaining > take:
                        bills.appendleft((bill_date, remaining - take))
                advance += paid
            buckets = [0, 0, 0, 0]
            for bill_date, amount in bills:
                days = (as_of - bill_date).days
                buckets[0 if days <= 30 else 1 if days <= 60 else 2 if days <= 90 else 3] += amount
            owed = sum(buckets)
            if owed or advance:
                result.append(PartyBalance(party_id, owed, buckets[0], buckets[1], buckets[2], buckets[3], advance))
        return sorted(result, key=lambda b: -b.owed_irr)
