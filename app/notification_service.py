import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NotificationService:

    @staticmethod
    def send( 
        event_type: str, 
        recipient: str, 
        payload: Dict[str, Any],
    ) -> bool:


        if event_type == "email":
            return NotificationService._send_email(recipient, payload)
        elif event_type == "sms":
            return NotificationService._send_sms(recipient, payload)
        else:
            logger.warning(f"Unknown notification type: {event_type}")
            return False


    @staticmethod
    def _send_email(recipient: str, payload: Dict[str, Any]) -> bool:

        subject = payload.get("subject", "No subject")
        message = payload.get("message", "No message")

        logger.info(
            f"[EMAIL] To: {recipient} | Subject: {subject} | Message: {message}"
        )

        time.sleep(2)

        logger.info(f"[EMAIL] Successfully sent to {recipient}")
        return True

    @staticmethod
    def _send_sms(recipient: str, payload: Dict[str, Any]) -> bool:

        message = payload.get("message", "No message")

        logger.info(f"[SMS] To: {recipient} | Message: {message}")

        time.sleep(1)

        logger.info(f"[SMS] Successfully sent to {recipient}")
        return True
        