from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.database import ContentPost, get_db
from app.schemas import (
    ContentPostCreate,
    ContentPostResponse,
    ContentPostUpdate,
    ContentBulkSchedule,
    SchedulerStats,
)
from app.utils.scheduler_service import SchedulerService

router = APIRouter(prefix="/api/scheduler", tags=["Content Scheduler"])


@router.post("/posts", response_model=dict)
def schedule_post(payload: ContentPostCreate, db: Session = Depends(get_db)) -> dict:
    """
    Schedule a single social media post.
    
    Parameters:
    - platform (string, required): facebook, instagram, tiktok, x, linkedin, youtube
    - caption (string, required): Post text (1-4096 characters)
    - media_url (string, optional): URL to image or video
    - hashtags (array, optional): List of hashtags
    - status (string): draft, scheduled, or published (default: scheduled)
    - scheduled_for (datetime, optional): ISO 8601 timestamp
    
    Example:
    ```json
    {
      "platform": "instagram",
      "caption": "We help Nigerian businesses grow with AI + WhatsApp automation.",
      "hashtags": ["#AI", "#Nigeria", "#Growth"],
      "scheduled_for": "2026-10-05T14:30:00"
    }
    ```
    
    Returns:
    ```json
    {
      "id": 1,
      "status": "scheduled",
      "platform": "instagram",
      "scheduled_for": "2026-10-05T14:30:00",
      "message": "Post scheduled successfully"
    }
    ```
    """
    post = ContentPost(
        platform=payload.platform.lower(),
        caption=payload.caption,
        media_url=payload.media_url,
        status=payload.status or "scheduled",
        scheduled_for=payload.scheduled_for
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return {
        "id": post.id,
        "status": post.status,
        "platform": post.platform,
        "scheduled_for": post.scheduled_for.isoformat() if post.scheduled_for else None,
        "message": "Post scheduled successfully"
    }


@router.post("/posts/bulk", response_model=dict)
def schedule_multi_platform(payload: ContentBulkSchedule, db: Session = Depends(get_db)) -> dict:
    """
    Schedule the same post across multiple platforms simultaneously.
    
    Useful for campaigns that need consistent messaging across channels.
    
    Parameters:
    - platforms (array, required): List of platform names
    - caption (string, required): Post text
    - media_url (string, optional): Single media URL for all platforms
    - hashtags (array, optional): Shared hashtags
    - scheduled_for (datetime, optional): Same schedule time for all
    
    Example:
    ```json
    {
      "platforms": ["facebook", "instagram", "tiktok"],
      "caption": "Join us for a free AI automation webinar tomorrow!",
      "hashtags": ["#AI", "#Automation", "#Nigeria"],
      "scheduled_for": "2026-10-06T10:00:00"
    }
    ```
    
    Returns:
    ```json
    {
      "message": "3 posts scheduled across platforms",
      "posts_created": 3,
      "platforms": ["facebook", "instagram", "tiktok"],
      "post_ids": [1, 2, 3]
    }
    ```
    """
    post_ids = []
    
    for platform in payload.platforms:
        post = ContentPost(
            platform=platform.lower(),
            caption=payload.caption,
            media_url=payload.media_url,
            status="scheduled",
            scheduled_for=payload.scheduled_for
        )
        db.add(post)
        db.flush()
        post_ids.append(post.id)
    
    db.commit()
    
    return {
        "message": f"{len(payload.platforms)} posts scheduled across platforms",
        "posts_created": len(payload.platforms),
        "platforms": payload.platforms,
        "post_ids": post_ids
    }


@router.get("/posts", response_model=list[ContentPostResponse])
def list_posts(
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> list[ContentPostResponse]:
    """
    List scheduled and published posts.
    
    Query parameters:
    - platform: Filter by platform (facebook, instagram, tiktok, x, linkedin, youtube)
    - status: Filter by status (draft, scheduled, published, failed)
    - limit: Results per page (1-500, default 50)
    - offset: Pagination offset (default 0)
    
    Example: `/api/scheduler/posts?platform=instagram&status=scheduled&limit=25`
    """
    query = db.query(ContentPost)
    
    if platform:
        query = query.filter(ContentPost.platform == platform.lower())
    
    if status:
        query = query.filter(ContentPost.status == status.lower())
    
    posts = query.order_by(ContentPost.created_at.desc()).offset(offset).limit(limit).all()
    return [ContentPostResponse.from_orm(post) for post in posts]


@router.get("/posts/{post_id}", response_model=ContentPostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)) -> ContentPostResponse:
    """
    Get detailed information about a specific post.
    
    Parameters:
    - post_id (integer, required): Post ID
    
    Example response:
    ```json
    {
      "id": 42,
      "platform": "instagram",
      "caption": "We help Nigerian businesses grow with AI + WhatsApp automation.",
      "status": "published",
      "scheduled_for": "2026-10-05T14:30:00",
      "published_at": "2026-10-05T14:31:15",
      "created_at": "2026-10-04T10:15:00"
    }
    ```
    """
    post = db.query(ContentPost).filter(ContentPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return ContentPostResponse.from_orm(post)


@router.patch("/posts/{post_id}", response_model=dict)
def update_post(post_id: int, payload: ContentPostUpdate, db: Session = Depends(get_db)) -> dict:
    """
    Update a scheduled post.
    
    Only draft and scheduled posts can be updated.
    Parameters:
    - post_id (integer, required): Post ID
    - caption (string, optional): New caption text
    - scheduled_for (datetime, optional): New scheduled time
    - status (string, optional): New status (draft, scheduled, published, failed)
    
    Example:
    ```json
    {
      "caption": "Updated caption for the campaign.",
      "scheduled_for": "2026-10-06T15:00:00"
    }
    ```
    """
    post = db.query(ContentPost).filter(ContentPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.status == "published":
        raise HTTPException(status_code=400, detail="Published posts cannot be edited")
    
    if post.status == "failed":
        raise HTTPException(status_code=400, detail="Failed posts cannot be edited. Delete and reschedule.")
    
    if payload.caption:
        post.caption = payload.caption
    
    if payload.scheduled_for:
        post.scheduled_for = payload.scheduled_for
    
    if payload.status:
        post.status = payload.status
    
    post.updated_at = datetime.utcnow()
    db.add(post)
    db.commit()
    
    return {
        "id": post.id,
        "status": post.status,
        "message": "Post updated successfully"
    }


@router.post("/posts/{post_id}/publish", response_model=dict)
def publish_post_now(post_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Manually publish a scheduled post immediately.
    
    Bypasses scheduled time and publishes right away.
    
    Parameters:
    - post_id (integer, required): Post ID to publish
    
    Example response:
    ```json
    {
      "status": "published",
      "post_id": 42,
      "platform": "instagram",
      "published_at": "2026-10-04T11:25:33"
    }
    ```
    """
    post = db.query(ContentPost).filter(ContentPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.status == "published":
        raise HTTPException(status_code=400, detail="Post is already published")
    
    post.status = "published"
    post.published_at = datetime.utcnow()
    post.updated_at = datetime.utcnow()
    db.add(post)
    db.commit()
    
    # TODO: Call social media APIs to actually publish
    # service = SchedulerService(settings.social_tokens)
    # result = service.publish(post.platform, post.caption, post.media_url)
    
    return {
        "status": "published",
        "post_id": post.id,
        "platform": post.platform,
        "published_at": post.published_at.isoformat()
    }


@router.delete("/posts/{post_id}", response_model=dict)
def delete_post(post_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Delete a scheduled or draft post.
    
    Published posts cannot be deleted (data retention).
    
    Parameters:
    - post_id (integer, required): Post ID
    """
    post = db.query(ContentPost).filter(ContentPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.status == "published":
        raise HTTPException(status_code=400, detail="Cannot delete published posts")
    
    db.delete(post)
    db.commit()
    
    return {
        "message": "Post deleted successfully",
        "post_id": post_id
    }


@router.get("/stats", response_model=SchedulerStats)
def scheduler_statistics(db: Session = Depends(get_db)) -> SchedulerStats:
    """
    Get social media scheduler statistics.
    
    Returns counts and breakdown by platform.
    
    Example response:
    ```json
    {
      "total_posts": 42,
      "published": 25,
      "scheduled": 12,
      "draft": 5,
      "failed": 0,
      "platforms": {
        "instagram": 15,
        "facebook": 12,
        "tiktok": 10,
        "x": 5
      }
    }
    ```
    """
    total = db.query(ContentPost).count()
    published = db.query(ContentPost).filter(ContentPost.status == "published").count()
    scheduled = db.query(ContentPost).filter(ContentPost.status == "scheduled").count()
    draft = db.query(ContentPost).filter(ContentPost.status == "draft").count()
    failed = db.query(ContentPost).filter(ContentPost.status == "failed").count()
    
    # Count by platform
    from sqlalchemy import func
    platform_counts = db.query(
        ContentPost.platform,
        func.count(ContentPost.id).label("count")
    ).group_by(ContentPost.platform).all()
    
    platforms = {platform: count for platform, count in platform_counts}
    
    return SchedulerStats(
        total_posts=total,
        published=published,
        scheduled=scheduled,
        draft=draft,
        failed=failed,
        platforms=platforms
    )


@router.get("/queue/upcoming")
def get_upcoming_posts(
    hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get posts scheduled to publish in the next N hours.
    
    Useful for campaign preview and manual overrides.
    
    Parameters:
    - hours (integer): Look-ahead window (1-720 hours, default 24)
    
    Example: `/api/scheduler/queue/upcoming?hours=48`
    """
    now = datetime.utcnow()
    future = now + timedelta(hours=hours)
    
    posts = db.query(ContentPost).filter(
        and_(
            ContentPost.status == "scheduled",
            ContentPost.scheduled_for >= now,
            ContentPost.scheduled_for <= future
        )
    ).order_by(ContentPost.scheduled_for.asc()).all()
    
    return {
        "look_ahead_hours": hours,
        "posts_upcoming": len(posts),
        "posts": [
            {
                "id": p.id,
                "platform": p.platform,
                "caption": p.caption[:100] + "..." if len(p.caption) > 100 else p.caption,
                "scheduled_for": p.scheduled_for.isoformat()
            }
            for p in posts
        ]
    }
