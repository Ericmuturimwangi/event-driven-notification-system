import logging
import time
from typing import Dict, Any

from app.core.exceptions import (
    RetryableNotificationError,
    PermanentNotificationError,
)

logger = logging.getLogger(__name__)

class NotificationService:

    @staticmethod
    def send(
        event_type: str,
        recipient: str,
        payload: Dict[str, Any],
    
    ) -> None:
    
        if event_type == "email":
            NotificationService._send_email(recipient, payload)
        elif event_type == "sms":
            NotificationService._send_sms(recipient, payload)

        else:
            raise PermanentNotificationError(
                f"Unknown notification type: {event_type}"
            )

    @staticmethod
    def _send_email(recipient: str, payload: Dict[str, Any]) -> None:

        if "@" not in recipient:
            raise PermanentNotificationError(
                f"Invalid email recipient: {recipient}"
            )

        subject = payload.get("subject", "No subject")
        message = payload.get("message", "No message")

        logger.info(
            f"[EMAIL] To: {recipient} | Subject: {subject} | Message: {message}"
        )

        time.sleep(2)

        if "transient-fail" in recipient:
            raise RetryableNotificationError("Simulated SMTP timeout")
        if "permanent-fail" in recipient:
            raise PermanentNotificationError("Simulated hard bounce (550)")

        logger.info(f"[EMAIL] Successfully sent to {recipient}")
        

    @staticmethod
    def _send_sms(recipient: str, payload: Dict[str, Any]) -> None:

        message = payload.get("message", "No message")

        logger.info(f"[SMS] To: {recipient} | Message: {message}")

        time.sleep(1)

        if "transient-fail" in recipient:
            raise RetryableNotificationError("Simulated Twilio timeot")

        if "permanent-fail" in recipient:
            raise PermanentNotificationError("Simulated invalid number (21211)")

        logger.info(f"[SMS] Successfully sent to {recipient}")
    
        