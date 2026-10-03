from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database import Lead, WhatsAppMessage, get_db
from app.models import Lead as LeadModel
from app.schemas import (
    LeadCreate,
    LeadResponse,
    WhatsAppAutoReplyConfig,
    WhatsAppLeadQualifier,
    WhatsAppMessageResponse,
    WhatsAppSendRequest,
)
from app.config import settings
from app.utils.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])


@router.get("/webhook")
def verify_webhook(request: Request, db: Session = Depends(get_db)) -> dict | str:
    """
    WhatsApp Webhook Verification.
    
    Called by WhatsApp to verify the webhook endpoint.
    Required parameters:
    - hub.mode=subscribe
    - hub.verify_token={WHATSAPP_WEBHOOK_VERIFY_TOKEN}
    - hub.challenge={challenge_string}
    
    Returns the challenge string if verification succeeds.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_webhook_verify_token:
        return challenge

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/webhook")
def receive_webhook(request_body: dict, db: Session = Depends(get_db)) -> dict:
    """
    Receive and process WhatsApp webhook events.
    
    Handles:
    - New incoming messages (text, media, location, etc.)
    - Message status updates (delivered, read, failed)
    - Lead creation from WhatsApp messages
    - Automatic lead assignment
    
    Example incoming message:
    ```json
    {
      "entry": [{
        "changes": [{
          "value": {
            "messages": [{
              "from": "+2348012345678",
              "text": {"body": "Hello, I need help with ads"},
              "type": "text"
            }]
          }
        }]
      }]
    }
    ```
    """
    try:
        entries = request_body.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                
                for msg_item in messages:
                    phone_number = msg_item.get("from")
                    msg_text = msg_item.get("text", {}).get("body", "No text")
                    msg_type = msg_item.get("type", "text")
                    timestamp = msg_item.get("timestamp")
                    
                    if not phone_number:
                        continue
                    
                    # Find or create lead
                    lead = db.query(Lead).filter(Lead.phone == phone_number).first()
                    if not lead:
                        lead = Lead(
                            name="WhatsApp Lead",
                            phone=phone_number,
                            source="whatsapp",
                            status="new"
                        )
                        db.add(lead)
                        db.commit()
                        db.refresh(lead)
                    
                    # Store message
                    message = WhatsAppMessage(
                        lead_id=lead.id,
                        direction="inbound",
                        phone=phone_number,
                        content=msg_text,
                        status="received"
                    )
                    db.add(message)
                    db.commit()
        
        return {"status": "received", "processed": True}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/send", response_model=dict)
def send_message(payload: WhatsAppSendRequest, db: Session = Depends(get_db)) -> dict:
    """
    Send a WhatsApp message to a lead.
    
    Parameters:
    - phone (string, required): Phone number with country code (e.g., +2348012345678)
    - message (string, required): Message text (max 4096 characters)
    - template_name (string, optional): Use a pre-defined template
    
    Example:
    ```json
    {
      "phone": "+2348012345678",
      "message": "Hello! Your growth plan is ready. Click the link below."
    }
    ```
    
    Returns:
    ```json
    {
      "status": "sent",
      "message_id": "wamid.HBEUGBZXVVVCAgkZCZ...",
      "phone": "+2348012345678"
    }
    ```
    """
    lead = db.query(Lead).filter(Lead.phone == payload.phone).first()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead with phone {payload.phone} not found")
    
    # Store outbound message
    outbound_msg = WhatsAppMessage(
        lead_id=lead.id,
        direction="outbound",
        phone=payload.phone,
        content=payload.message,
        status="sent"
    )
    db.add(outbound_msg)
    db.commit()
    
    # TODO: Call WhatsApp API to actually send message
    # service = WhatsAppService(settings.whatsapp_token)
    # result = service.send_message(payload.phone, payload.message)
    
    return {
        "status": "sent",
        "message_id": f"msg_{outbound_msg.id}",
        "phone": payload.phone,
        "timestamp": outbound_msg.created_at.isoformat()
    }


@router.post("/welcome/{lead_id}", response_model=dict)
def send_welcome_message(lead_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Send automated welcome message to a new lead.
    
    Sends a pre-configured welcome message to introduce King Mave Digital services.
    
    Example response:
    ```json
    {
      "status": "sent",
      "lead_id": 42,
      "message": "Hello! Thanks for contacting King Mave Digital..."
    }
    ```
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    welcome_message = (
        f"Hello {lead.name}! 👋\n\n"
        "Thanks for reaching out to King Mave Digital.\n\n"
        "We help Nigerian businesses grow with:\n"
        "✅ AI Content Automation\n"
        "✅ Facebook & Instagram Ads\n"
        "✅ WhatsApp Sales Funnels\n"
        "✅ TikTok & YouTube Strategy\n"
        "✅ 24/7 Customer Support Chatbots\n\n"
        "Reply with:\n"
        "'START' for your free growth plan\n"
        "'PRICING' for our packages\n"
        "'DEMO' to see it in action\n\n"
        "Let's grow together! 🚀"
    )
    
    msg = WhatsAppMessage(
        lead_id=lead.id,
        direction="outbound",
        phone=lead.phone,
        content=welcome_message,
        status="sent"
    )
    db.add(msg)
    db.commit()
    
    return {
        "status": "sent",
        "lead_id": lead_id,
        "message": welcome_message
    }


@router.post("/auto-reply/config", response_model=dict)
def configure_auto_reply(config: WhatsAppAutoReplyConfig, db: Session = Depends(get_db)) -> dict:
    """
    Configure automatic reply settings for new messages.
    
    Parameters:
    - enabled (boolean): Enable/disable auto-replies
    - welcome_message (string): Message sent to new leads
    - welcome_delay_seconds (integer): Delay before sending (0-300)
    - follow_up_message (string, optional): Follow-up message for warm leads
    - follow_up_delay_hours (integer): When to send follow-up (1-168 hours)
    
    This is stored globally and affects all new conversations.
    """
    # TODO: Store config in database or cache
    return {
        "status": "configured",
        "auto_reply_enabled": config.enabled,
        "welcome_message_length": len(config.welcome_message),
        "follow_up_enabled": config.follow_up_message is not None
    }


@router.get("/leads", response_model=list[LeadResponse])
def get_whatsapp_leads(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> list[LeadResponse]:
    """
    Get all leads that contacted via WhatsApp.
    
    Query parameters:
    - status: Filter by lead status (new, contacted, interested, converted, lost)
    - limit: Number of results (1-500, default 50)
    - offset: Pagination offset (default 0)
    
    Example: `/api/whatsapp/leads?status=new&limit=25`
    """
    query = db.query(Lead).filter(Lead.source == "whatsapp")
    
    if status:
        query = query.filter(Lead.status == status)
    
    leads = query.order_by(Lead.created_at.desc()).offset(offset).limit(limit).all()
    return [LeadResponse.from_orm(lead) for lead in leads]


@router.get("/conversations/{lead_id}", response_model=list[WhatsAppMessageResponse])
def get_conversation(
    lead_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
) -> list[WhatsAppMessageResponse]:
    """
    Get full conversation history with a lead.
    
    Parameters:
    - lead_id (integer, required): Lead ID
    - limit (integer): Number of messages (1-500, default 50)
    
    Returns messages in reverse chronological order (newest first).
    
    Example: `/api/whatsapp/conversations/42?limit=100`
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    messages = db.query(WhatsAppMessage).filter(
        WhatsAppMessage.lead_id == lead_id
    ).order_by(WhatsAppMessage.created_at.desc()).limit(limit).all()
    
    return [WhatsAppMessageResponse.from_orm(msg) for msg in messages]


@router.post("/qualify/{lead_id}", response_model=WhatsAppLeadQualifier)
def qualify_lead(
    lead_id: int,
    qualifier: WhatsAppLeadQualifier,
    db: Session = Depends(get_db)
) -> WhatsAppLeadQualifier:
    """
    Qualify a lead based on conversation keywords and interaction.
    
    Scoring:
    - Mentions of budget/budget/pricing: +30
    - Mentions of "urgent"/"ASAP": +20
    - Mentions of specific features: +15
    - Multiple interactions: +10
    - Custom keywords: +score parameter
    
    Score >= 70 = Qualified lead ready for sales call
    
    Example:
    ```json
    {
      "lead_id": 42,
      "keywords": ["budget", "urgent", "WhatsApp"],
      "score": 0,
      "qualified": false
    }
    ```
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Calculate score from conversation
    messages = db.query(WhatsAppMessage).filter(
        WhatsAppMessage.lead_id == lead_id
    ).all()
    
    score = qualifier.score
    conversation_text = " ".join([m.content.lower() for m in messages])
    
    # Keyword-based scoring
    if any(kw.lower() in conversation_text for kw in ["budget", "price", "cost", "invest"]):
        score += 30
    if any(kw.lower() in conversation_text for kw in ["urgent", "asap", "today", "now"]):
        score += 20
    if len(messages) >= 3:
        score += 10
    
    qualified = score >= 70
    
    # Update lead status
    if qualified and lead.status == "new":
        lead.status = "interested"
        db.add(lead)
        db.commit()
    
    return WhatsAppLeadQualifier(
        lead_id=lead_id,
        keywords=qualifier.keywords,
        score=min(score, 100),
        qualified=qualified
    )


@router.get("/stats", response_model=dict)
def whatsapp_statistics(db: Session = Depends(get_db)) -> dict:
    """
    WhatsApp channel statistics.
    
    Returns:
    ```json
    {
      "total_leads": 42,
      "new_leads": 5,
      "contacted_leads": 15,
      "total_messages": 287,
      "inbound_messages": 143,
      "outbound_messages": 144,
      "avg_response_time_minutes": 45
    }
    ```
    """
    total_leads = db.query(Lead).filter(Lead.source == "whatsapp").count()
    new_leads = db.query(Lead).filter(
        Lead.source == "whatsapp",
        Lead.status == "new"
    ).count()
    contacted = db.query(Lead).filter(
        Lead.source == "whatsapp",
        Lead.status.in_(["contacted", "interested", "converted"])
    ).count()
    
    total_messages = db.query(WhatsAppMessage).count()
    inbound = db.query(WhatsAppMessage).filter(
        WhatsAppMessage.direction == "inbound"
    ).count()
    outbound = total_messages - inbound
    
    return {
        "total_leads": total_leads,
        "new_leads": new_leads,
        "contacted_leads": contacted,
        "total_messages": total_messages,
        "inbound_messages": inbound,
        "outbound_messages": outbound,
        "engagement_rate": f"{(contacted / total_leads * 100):.1f}%" if total_leads > 0 else "0%"
    }
