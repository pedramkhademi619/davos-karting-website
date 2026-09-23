"""Removes cached answers that can no longer be served (the daily scheduled job does the same).

docker compose exec api python -m davos.tools.purge_semantic_cache
"""

from __future__ import annotations

import asyncio
import sys

from davos.composition.application_container import ApplicationContainer
from davos.platform.settings.app_settings import AppSettings


async def _run() -> int:
    container = ApplicationContainer.build(AppSettings())
    try:
        removed = await container.purge_semantic_cache().execute()
    finally:
        await container.aclose()
    print(f"removed {removed} cached answer(s) that can no longer be served")
    return 0


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
