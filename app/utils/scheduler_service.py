from __future__ import annotations

from datetime import datetime
from typing import Optional


class SchedulerService:
    """Social media scheduling and publishing service.
    
    Handles:
    - Schedule preparation and validation
    - Multi-platform posting
    - Publishing coordination
    - Retry logic for failed posts
    """
    
    @staticmethod
    def validate_caption_length(platform: str, caption: str) -> tuple[bool, str]:
        """Validate caption length for platform limits.
        
        Args:
            platform: Social media platform
            caption: Post caption text
        
        Returns:
            (is_valid, error_message)
        """
        limits = {
            "facebook": 63206,
            "instagram": 2200,
            "tiktok": 2200,
            "x": 280,
            "linkedin": 13000,
            "youtube": 5000,
        }
        
        max_length = limits.get(platform.lower(), 4096)
        
        if len(caption) > max_length:
            return False, f"{platform} has a {max_length} character limit. Current: {len(caption)}"
        
        return True, "Valid"
    
    @staticmethod
    def optimize_caption_for_platform(platform: str, caption: str, hashtags: Optional[list[str]] = None) -> str:
        """Optimize caption formatting for specific platform.
        
        Args:
            platform: Social media platform
            caption: Original caption text
            hashtags: Optional hashtags to append
        
        Returns:
            Optimized caption
        """
        optimized = caption
        
        # Add hashtags
        if hashtags:
            hashtag_text = " ".join(hashtags)
            optimized = f"{caption}\n\n{hashtag_text}"
        
        # Platform-specific optimizations
        if platform.lower() == "tiktok":
            optimized = optimized.replace("#", "")
            optimized = f"🎬 {optimized}"
        elif platform.lower() == "x":
            # Twitter has strict length limits, strip excess
            if len(optimized) > 280:
                optimized = optimized[:270] + "... 🔗"
        
        return optimized
    
    @staticmethod
    def schedule_post_batch(posts: list[dict]) -> dict:
        """Schedule multiple posts at once.
        
        Args:
            posts: List of post dictionaries with platform, caption, etc.
        
        Returns:
            Batch result summary
        """
        successful = 0
        failed = 0
        errors = []
        
        for post in posts:
            platform = post.get("platform")
            caption = post.get("caption")
            
            is_valid, error_msg = SchedulerService.validate_caption_length(platform, caption)
            if is_valid:
                successful += 1
            else:
                failed += 1
                errors.append({"post": caption[:50], "error": error_msg})
        
        return {
            "total": len(posts),
            "successful": successful,
            "failed": failed,
            "errors": errors
        }
    
    @staticmethod
    def build_welcome_message(name: str) -> str:
        """Build a personalized welcome message.
        
        Args:
            name: Lead name
        
        Returns:
            Formatted welcome message
        """
        return (
            f"Hello {name}! 👋\n\n"
            "Thanks for reaching out to King Mave Digital.\n\n"
            "We help Nigerian businesses grow with:\n"
            "✅ AI Content Automation\n"
            "✅ Facebook & Instagram Ads\n"
            "✅ WhatsApp Sales Funnels\n"
            "✅ TikTok & YouTube Strategy\n\n"
            "Reply with 'START' for your free growth plan."
        )
