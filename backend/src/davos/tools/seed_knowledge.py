"""Fill an empty assistant knowledge base from the .txt files now and print what happened.

    docker compose exec api python -m davos.tools.seed_knowledge

The API does the same at start-up. It only does anything on a fresh installation: once the knowledge base has any
entry, the staff panel is the only place where it is edited, and the files are never read again.
"""

from __future__ import annotations

import asyncio
import sys

from davos.composition.application_container import ApplicationContainer
from davos.platform.settings.app_settings import AppSettings


async def _run() -> int:
    settings = AppSettings()
    if not settings.assistant_knowledge_dir:
        print("ASSISTANT_KNOWLEDGE_DIR is not set, so there is nothing to import.")
        return 2
    container = ApplicationContainer.build(settings)
    try:
        use_case = container.seed_knowledge_from_documents()
        if use_case is None:
            return 2
        report = await use_case.execute()
    finally:
        await container.aclose()
    if report.skipped_because_not_empty:
        print("The knowledge base already has entries, so the files were not read. Edit it in the staff panel.")
        return 0
    print(f"imported: {report.imported}   drafts (not imported): {report.drafts}")
    for problem in report.problems:
        print(f"  NOT USED  {problem.name}.txt  ->  {problem.reason}")
    return 1 if report.problems else 0


def main() -> None:
    sys.exit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
