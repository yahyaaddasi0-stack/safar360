import os
import json
from fastapi import APIRouter, Request, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.credit_service import CreditService

router = APIRouter()

META_VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN", "safar360_secure_token_123")

@router.post(
    "/lemonsqueezy",
    status_code=status.HTTP_200_OK,
    summary="LemonSqueezy Webhook for Payments"
)
async def lemonsqueezy_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        body = await request.body()
        payload = json.loads(body)

        event_name = payload.get("meta", {}).get("event_name")
        custom_data = payload.get("meta", {}).get("custom_data", {})

        user_id = custom_data.get("user_id")

        if not user_id:
            return {"status": "skipped", "reason": "No user_id in custom_data"}

        if event_name == "order_created":
            await CreditService.add_pro_credits(db, user_id=user_id, amount=100)
        elif event_name == "subscription_renewed":
            await CreditService.add_pro_credits(db, user_id=user_id, amount=100)

        return {"status": "success", "event": event_name}

    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/meta", summary="Verify Meta Webhook")
async def verify_meta_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: int = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/meta", summary="Receive Meta/Instagram DMs")
async def receive_meta_webhook(request: Request):
    try:
        payload = await request.json()

        # Parse Instagram DMs
        if payload.get("object") == "instagram":
            entries = payload.get("entry", [])
            for entry in entries:
                messages = entry.get("messaging", [])
                for msg in messages:
                    sender_id = msg.get("sender", {}).get("id")
                    text = msg.get("message", {}).get("text")

                    if sender_id and text:
                        # Preparation to route to Vertex AI logic
                        print(f"✅ [Meta Webhook] Routed to Vertex AI. From {sender_id}: {text}")
                        # In production, we'd trigger an async background task here to hit Vertex
                        # and send the response back via the Graph API.

        return {"status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Meta Parse Error: {str(e)}")
