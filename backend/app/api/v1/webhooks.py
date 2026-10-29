from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"]
)

VERIFY_TOKEN = "motordesk_verify_token"


@router.get("/meta")
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    if (
        hub_mode == "subscribe"
        and hub_verify_token == VERIFY_TOKEN
    ):
        return PlainTextResponse(hub_challenge)

    raise HTTPException(status_code=403)
"""Recepción de callbacks externos, aislados de las rutas interactivas."""
