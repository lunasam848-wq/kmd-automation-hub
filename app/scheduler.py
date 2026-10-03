from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.database import ContentPost


class SchedulerService:
    @staticmethod
    def publish_post(post: ContentPost) -> ContentPost:
        post.status = "published"
        post.published_at = datetime.utcnow()
        post.updated_at = datetime.utcnow()
        return post

    @staticmethod
    def build_message_for_lead(name: str) -> str:
        return (
            f"Hello {name}! Thanks for contacting King Mave Digital. "
            "We help businesses grow with AI, ads, content, and WhatsApp automation. "
            "Reply with 'START' to get your growth plan."
        )

    @staticmethod
    def summarize_platform(platform: str) -> str:
        return {
            "facebook": "Facebook",
            "instagram": "Instagram",
            "tiktok": "TikTok",
            "x": "X / Twitter",
            "whatsapp": "WhatsApp",
            "linkedin": "LinkedIn",
        }.get(platform.lower(), platform.title())
