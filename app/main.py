from __future__ import annotations

from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import ContentPost, Lead, WhatsAppMessage, get_db, init_db
from app.models import (
    AnalyticsSummary,
    ContentPostCreate,
    LeadCreate,
    WhatsAppOutboundMessage,
)
from app.routes import scheduler_router, whatsapp_router
from app.scheduler import SchedulerService

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(whatsapp_router)
app.include_router(scheduler_router)


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_env}


@app.get("/", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    return HTMLResponse(
        """
        <html>
          <head>
            <title>King Mave Digital Automation Hub</title>
            <style>
              body { font-family: Arial, sans-serif; background: #071323; color: #eaf8ff; margin: 0; padding: 24px; }
              .container { max-width: 1100px; margin: 0 auto; }
              .card { background: #0f1d35; border: 1px solid #22d3ee; border-radius: 12px; padding: 20px; margin-top: 18px; }
              button { background: linear-gradient(135deg, #06b6d4, #8b5cf6); border: none; color: white; border-radius: 10px; padding: 10px 16px; cursor: pointer; }
              input, textarea, select { width: 100%; box-sizing: border-box; border-radius: 8px; border: 1px solid #335; background: #0a1326; color: white; padding: 10px; margin: 6px 0; }
              .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
              .metric { background: #0b1b2d; border: 1px solid #1e40af; border-radius: 12px; padding: 16px; }
            </style>
          </head>
          <body>
            <div class="container">
              <h1>King Mave Digital Automation Hub</h1>
              <div class="grid">
                <div class="metric"><strong>Total Leads</strong><div id="totalLeads">0</div></div>
                <div class="metric"><strong>New Leads</strong><div id="newLeads">0</div></div>
                <div class="metric"><strong>Published Posts</strong><div id="publishedPosts">0</div></div>
                <div class="metric"><strong>Scheduled Posts</strong><div id="scheduledPosts">0</div></div>
              </div>

              <div class="card">
                <h2>Create Lead</h2>
                <input id="leadName" placeholder="Name" />
                <input id="leadPhone" placeholder="Phone" />
                <input id="leadEmail" placeholder="Email" />
                <input id="leadSource" placeholder="Source" />
                <input id="leadInterest" placeholder="Interest" />
                <textarea id="leadNotes" placeholder="Notes"></textarea>
                <button onclick="createLead()">Save Lead</button>
              </div>

              <div class="card">
                <h2>Create Scheduled Post</h2>
                <select id="postPlatform">
                  <option value="instagram">Instagram</option>
                  <option value="facebook">Facebook</option>
                  <option value="tiktok">TikTok</option>
                  <option value="x">X / Twitter</option>
                  <option value="whatsapp">WhatsApp</option>
                </select>
                <textarea id="postCaption" placeholder="Caption"></textarea>
                <input id="postMediaUrl" placeholder="Media URL (optional)" />
                <input id="postScheduledFor" type="datetime-local" />
                <button onclick="createPost()">Schedule Post</button>
              </div>
            </div>

            <script>
              async function createLead() {
                const payload = {
                  name: document.getElementById('leadName').value,
                  phone: document.getElementById('leadPhone').value,
                  email: document.getElementById('leadEmail').value,
                  source: document.getElementById('leadSource').value || 'website',
                  interest: document.getElementById('leadInterest').value,
                  notes: document.getElementById('leadNotes').value,
                };
                const response = await fetch('/api/leads', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(payload)
                });
                const result = await response.json();
                alert(result.message || 'Lead created');
                loadSummary();
              }

              async function createPost() {
                const payload = {
                  platform: document.getElementById('postPlatform').value,
                  caption: document.getElementById('postCaption').value,
                  media_url: document.getElementById('postMediaUrl').value,
                  scheduled_for: document.getElementById('postScheduledFor').value ? new Date(document.getElementById('postScheduledFor').value).toISOString() : null,
                  status: 'scheduled'
                };
                const response = await fetch('/api/scheduler/posts', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(payload)
                });
                const result = await response.json();
                alert(result.message || 'Post scheduled');
                loadSummary();
              }

              async function loadSummary() {
                const response = await fetch('/api/analytics/summary');
                const summary = await response.json();
                document.getElementById('totalLeads').textContent = summary.total_leads;
                document.getElementById('newLeads').textContent = summary.new_leads;
                document.getElementById('publishedPosts').textContent = summary.published_posts;
                document.getElementById('scheduledPosts').textContent = summary.scheduled_posts;
              }

              loadSummary();
            </script>
          </body>
        </html>
        """
    )


@app.post("/api/leads", response_model=dict)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> dict:
    existing = db.query(Lead).filter(Lead.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Lead with this phone number already exists.")

    lead = Lead(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        source=payload.source,
        interest=payload.interest,
        notes=payload.notes,
        status="new",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    return {"message": "Lead created successfully", "lead_id": lead.id}


@app.get("/api/leads")
def list_leads(db: Session = Depends(get_db)) -> list[dict]:
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    return [
        {
            "id": lead.id,
            "name": lead.name,
            "phone": lead.phone,
            "email": lead.email,
            "source": lead.source,
            "interest": lead.interest,
            "notes": lead.notes,
            "status": lead.status,
            "created_at": lead.created_at.isoformat(),
        }
        for lead in leads
    ]


@app.get("/api/analytics/summary")
def analytics_summary(db: Session = Depends(get_db)) -> AnalyticsSummary:
    total_leads = db.query(Lead).count()
    new_leads = db.query(Lead).filter(Lead.status == "new").count()
    converted_leads = db.query(Lead).filter(Lead.status == "converted").count()
    total_posts = db.query(ContentPost).count()
    scheduled_posts = db.query(ContentPost).filter(ContentPost.status == "scheduled").count()
    published_posts = db.query(ContentPost).filter(ContentPost.status == "published").count()

    return AnalyticsSummary(
        total_leads=total_leads,
        new_leads=new_leads,
        converted_leads=converted_leads,
        total_posts=total_posts,
        scheduled_posts=scheduled_posts,
        published_posts=published_posts,
    )


@app.get("/api/scheduler/posts")
def list_posts(db: Session = Depends(get_db)) -> list[dict]:
    posts = db.query(ContentPost).order_by(ContentPost.created_at.desc()).all()
    return [
        {
            "id": post.id,
            "platform": post.platform,
            "caption": post.caption,
            "media_url": post.media_url,
            "status": post.status,
            "scheduled_for": post.scheduled_for.isoformat() if post.scheduled_for else None,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "created_at": post.created_at.isoformat(),
        }
        for post in posts
    ]


@app.post("/api/scheduler/posts", response_model=dict)
def schedule_post(payload: ContentPostCreate, db: Session = Depends(get_db)) -> dict:
    post = ContentPost(
        platform=payload.platform,
        caption=payload.caption,
        media_url=payload.media_url,
        status=payload.status,
        scheduled_for=payload.scheduled_for,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {"message": "Post scheduled successfully", "post_id": post.id}


@app.post("/api/scheduler/posts/{post_id}/publish", response_model=dict)
def publish_post(post_id: int, db: Session = Depends(get_db)) -> dict:
    post = db.query(ContentPost).filter(ContentPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post = SchedulerService.publish_post(post)
    db.add(post)
    db.commit()
    return {"message": "Post published", "platform": post.platform, "post_id": post.id}


@app.get("/api/whatsapp/webhook")
def whatsapp_verify(request: Request) -> JSONResponse:
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_webhook_verify_token:
        return JSONResponse(content=challenge)

    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/api/whatsapp/webhook")
def whatsapp_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    try:
        payload = request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    entries = payload.get("entry", [])
    for entry in entries:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            for item in messages:
                number = item.get("from")
                text = item.get("text", {}).get("body")
                if not number:
                    continue

                lead = db.query(Lead).filter(Lead.phone == number).first()
                if not lead:
                    lead = Lead(name="New WhatsApp Lead", phone=number, source="whatsapp", status="new")
                    db.add(lead)
                    db.commit()
                    db.refresh(lead)

                message = WhatsAppMessage(
                    lead_id=lead.id,
                    direction="inbound",
                    phone=number,
                    content=text or "No text received",
                    status="received",
                )
                db.add(message)
                db.commit()

    return {"status": "received"}


@app.post("/api/whatsapp/send")
def send_whatsapp_message(payload: WhatsAppOutboundMessage, db: Session = Depends(get_db)) -> dict:
    lead = db.query(Lead).filter(Lead.phone == payload.phone).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    outbound_message = WhatsAppMessage(
        lead_id=lead.id,
        direction="outbound",
        phone=payload.phone,
        content=payload.message,
        status="sent",
    )
    db.add(outbound_message)
    db.commit()

    return {"status": "sent", "phone": payload.phone, "message": payload.message}


@app.post("/api/whatsapp/welcome")
def send_welcome_message(phone: str, name: str, db: Session = Depends(get_db)) -> dict:
    lead = db.query(Lead).filter(Lead.phone == phone).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    message = SchedulerService.build_welcome_message(name)
    response = send_whatsapp_message(WhatsAppOutboundMessage(phone=phone, message=message), db)
    return response


@app.get("/api/messages")
def list_messages(db: Session = Depends(get_db)) -> list[dict]:
    messages = db.query(WhatsAppMessage).order_by(WhatsAppMessage.created_at.desc()).all()
    return [
        {
            "id": message.id,
            "lead_id": message.lead_id,
            "direction": message.direction,
            "phone": message.phone,
            "content": message.content,
            "status": message.status,
            "created_at": message.created_at.isoformat(),
        }
        for message in messages
    ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
