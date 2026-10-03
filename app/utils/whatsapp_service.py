from __future__ import annotations

import json
from typing import Optional


class WhatsAppService:
    """WhatsApp Business API integration service.
    
    Handles:
    - Sending messages via WhatsApp API
    - Webhook payload parsing
    - Message templating
    - Status tracking
    """
    
    def __init__(self, token: str, phone_number_id: str):
        self.token = token
        self.phone_number_id = phone_number_id
        self.api_url = f"https://graph.instagram.com/v18.0/{phone_number_id}/messages"
    
    def send_message(self, phone: str, message: str, media_url: Optional[str] = None) -> dict:
        """Send a text or media message to a phone number.
        
        Args:
            phone: Recipient phone number with country code
            message: Message text content
            media_url: Optional URL to media attachment
        
        Returns:
            API response with message ID
        """
        # TODO: Implement actual API call
        # import requests
        # payload = {
        #     "messaging_product": "whatsapp",
        #     "to": phone,
        #     "type": "text",
        #     "text": {"body": message}
        # }
        # response = requests.post(
        #     self.api_url,
        #     json=payload,
        #     headers={"Authorization": f"Bearer {self.token}"}
        # )
        # return response.json()
        
        return {
            "messages": [{"id": f"wamid_{phone}_{message[:10]}"}],
            "contacts": [{"input": phone, "wa_id": phone}]
        }
    
    def send_template(self, phone: str, template_name: str, params: Optional[list] = None) -> dict:
        """Send a pre-approved message template.
        
        Args:
            phone: Recipient phone number
            template_name: Name of approved template
            params: Template parameters/variables
        
        Returns:
            API response
        """
        # TODO: Implement actual API call
        return {
            "messages": [{"id": f"wamid_{phone}_template_{template_name}"}]
        }
    
    def mark_as_read(self, message_id: str) -> dict:
        """Mark a received message as read.
        
        Args:
            message_id: WhatsApp message ID
        
        Returns:
            API response
        """
        # TODO: Implement actual API call
        return {"success": True}
    
    def upload_media(self, file_path: str, media_type: str) -> str:
        """Upload media to WhatsApp.
        
        Args:
            file_path: Local file path
            media_type: image, video, document, or audio
        
        Returns:
            Media ID for reference in messages
        """
        # TODO: Implement actual API call
        return f"media_id_{media_type}_{file_path.split('/')[-1]}"
