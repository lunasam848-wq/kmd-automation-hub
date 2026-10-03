from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    """Create a new lead from website, WhatsApp, or other source."""
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=10, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    source: str = Field(default="website", max_length=100)
    interest: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    """Update lead status and information."""
    status: Optional[str] = Field(None, max_length=50)
    interest: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class LeadResponse(LeadCreate):
    """Lead response with metadata."""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WhatsAppMessageIn(BaseModel):
    """Inbound WhatsApp message from webhook."""
    from_number: str = Field(..., alias="from")
    text: Optional[str] = None
    body: Optional[str] = None

    class Config:
        populate_by_name = True


class WhatsAppSendRequest(BaseModel):
    """Send WhatsApp message to a lead."""
    phone: str = Field(..., min_length=10, max_length=50)
    message: str = Field(..., min_length=1, max_length=4096)
    template_name: Optional[str] = None  # For templated messages


class WhatsAppAutoReplyConfig(BaseModel):
    """Configure automatic WhatsApp replies."""
    enabled: bool = True
    welcome_message: str = Field(
        default="Hello! Thanks for contacting King Mave Digital. We help businesses grow with AI, ads, content, and WhatsApp automation. Reply with 'START' to get your growth plan."
    )
    welcome_delay_seconds: int = Field(default=2, ge=0, le=300)
    follow_up_message: Optional[str] = None
    follow_up_delay_hours: int = Field(default=24, ge=1, le=168)


class WhatsAppLeadQualifier(BaseModel):
    """Lead scoring/qualification from WhatsApp interaction."""
    lead_id: int
    keywords: list[str] = Field(default_factory=list)
    score: int = Field(default=0, ge=0, le=100)
    qualified: bool = False


class WhatsAppMessageResponse(BaseModel):
    """WhatsApp message log entry."""
    id: int
    lead_id: Optional[int]
    direction: str
    phone: str
    content: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ContentPostCreate(BaseModel):
    """Schedule a new social media post."""
    platform: str = Field(..., pattern="^(facebook|instagram|tiktok|x|linkedin|youtube)$")
    caption: str = Field(..., min_length=1, max_length=4096)
    media_url: Optional[str] = Field(None, max_length=500)
    hashtags: Optional[list[str]] = Field(default_factory=list)
    status: str = Field(default="scheduled", pattern="^(draft|scheduled|published|failed)$")
    scheduled_for: Optional[datetime] = None


class ContentPostUpdate(BaseModel):
    """Update scheduled post."""
    caption: Optional[str] = Field(None, max_length=4096)
    scheduled_for: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(draft|scheduled|published|failed)$")


class ContentPostResponse(ContentPostCreate):
    """Content post response with metadata."""
    id: int
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentBulkSchedule(BaseModel):
    """Schedule the same post across multiple platforms."""
    platforms: list[str] = Field(..., min_items=1)
    caption: str = Field(..., min_length=1, max_length=4096)
    media_url: Optional[str] = None
    hashtags: Optional[list[str]] = None
    scheduled_for: Optional[datetime] = None


class SchedulerStats(BaseModel):
    """Scheduler statistics."""
    total_posts: int
    published: int
    scheduled: int
    draft: int
    failed: int
    platforms: dict[str, int]  # count per platform


class AnalyticsSummary(BaseModel):
    """Analytics summary dashboard."""
    total_leads: int
    new_leads: int
    contacted_leads: int
    converted_leads: int
    lost_leads: int
    total_posts: int
    scheduled_posts: int
    published_posts: int
    failed_posts: int
    whatsapp_messages_total: int
    whatsapp_inbound: int
    whatsapp_outbound: int
    platforms_count: dict[str, int]

    class Config:
        from_attributes = True


class WebhookPayload(BaseModel):
    """Generic webhook payload for WhatsApp."""
    entry: list[dict]
