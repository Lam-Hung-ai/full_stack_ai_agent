from typing import Annotated

from fastapi import Depends, Request

from app.modules.agent.runner import Runner


def get_runner(request: Request) -> Runner:
    """The process-wide runner created in the app lifespan."""
    return request.app.state.runner


RunnerDep = Annotated[Runner, Depends(get_runner)]
