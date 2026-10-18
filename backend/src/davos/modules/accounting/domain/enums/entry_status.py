from enum import StrEnum


class EntryStatus(StrEnum):
    POSTED = "posted"
    REVERSED = "reversed"  # cancelled by a later reversing entry; the original stays in the books
