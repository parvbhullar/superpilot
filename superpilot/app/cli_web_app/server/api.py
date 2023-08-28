import uuid

from fastapi import APIRouter, FastAPI, Request

from superpilot.core.runner.cli_web_app.server.schema import InteractRequestBody

router = APIRouter()


@router.post("/pilots")
async def create_pilot(request: Request):
    """Create a new pilot."""
    pilot_id = uuid.uuid4().hex
    return {"pilot_id": pilot_id}


@router.post("/pilots/{pilot_id}")
async def interact(request: Request, pilot_id: str, body: InteractRequestBody):
    """Interact with an pilot."""

    # check headers

    # check if pilot_id exists

    # get pilot object from somewhere, e.g. a database/disk/global dict

    # continue pilot interaction with user input

    return {
        "thoughts": {
            "thoughts": {
                "text": "text",
                "reasoning": "reasoning",
                "plan": "plan",
                "criticism": "criticism",
                "speak": "speak",
            },
            "commands": {
                "name": "name",
                "args": {"arg_1": "value_1", "arg_2": "value_2"},
            },
        },
        "messages": ["message1", pilot_id],
    }


app = FastAPI()
app.include_router(router, prefix="/api/v1")
