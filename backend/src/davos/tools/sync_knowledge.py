"""Publish the assistant's knowledge files now and print what happened.

    docker compose exec api python -m davos.tools.sync_knowledge

The API does the same at start-up; run this after editing files to see, per file, whether it is used and why not.
"""

from __future__ import annotations

import asyncio
import sys

from davos.composition.application_container import ApplicationContainer
from davos.platform.settings.app_settings import AppSettings


async def _run() -> int:
    settings = AppSettings()
    if not settings.assistant_knowledge_dir:
        print("ASSISTANT_KNOWLEDGE_DIR is not set, so there is nothing to publish.")
        return 2
    container = ApplicationContainer.build(settings)
    try:
        use_case = container.sync_knowledge_documents()
        if use_case is None:
            return 2
        report = await use_case.execute()
    finally:
        await container.aclose()
    print(f"published: {report.published}   drafts (not quoted): {report.drafts}   removed: {report.removed}")
    for problem in report.problems:
        print(f"  NOT USED  {problem.name}.txt  ->  {problem.reason}")
    return 1 if report.problems else 0


def main() -> None:
    sys.exit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
