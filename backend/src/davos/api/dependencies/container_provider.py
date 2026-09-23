from __future__ import annotations

from fastapi import Request

from davos.composition.application_container import ApplicationContainer


def get_container(request: Request) -> ApplicationContainer:
    container: ApplicationContainer = request.app.state.container
    return container
