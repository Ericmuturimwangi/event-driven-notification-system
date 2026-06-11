import logging
import time
from typing import Dict, Any

from app.core.exceptions import (
    RetryableNotificationError,
    PermanentNotificationError,
    CircuitOpenError,
)

from app.core.circuit_breaker import get_breaker

logger = logging.getLogger(__name__)

class NotificationService:

    @staticmethod
    def send(
        event_type: str,
        recipient: str,
        payload: Dict[str, Any],
    
    ) -> None:
    
        if event_type == "email":
            if "@" not in recipient:
                raise PermanentNotificationError(
                    f"Invalid email recipient: {recipient}"
                )
            provider_call = NotificationService._contact_email_provider
            
        elif event_type == "sms":
            provider_call = NotificationService._contact_sms_provider

        else:
            raise PermanentNotificationError(
                f"Unknown notification type: {event_type}"
            )

        breaker = get_breaker(event_type)

        try:

            breaker.call(provider_call, recipient, payload)

        except pybreaker.CircuitBreakerError:

            logger.warning(
                f"[CircuitBreaker:{event_type}] OPEN - rejected send to "
                f"{recipient} without attempting"
            )

            raise CircuitOpenError(
                f"Circuit OPEN for channel '{event_type}'; provider "
                f"considered down. Send not attempted. "
            )

    @staticmethod
    def _contact_email_provider(recipient: str, payload: Dict[str, Any]) -> None:
        subject = payload.get("subject", "No subject")
        message = payload.get("message", "No message")

        logger.info(
            f"[EMAIL] To: {recipient} | Subject: {subject} | Message: {message}"
        )
        time.sleep(2)

        if "transient-fail" in recipient:
            raise RetryableNotificationError("Simulated SMTP timeout")

        logger.info(f"[EMAIL] Successfully sent to {recipient}")


    @staticmethod
    def _contact_sms_provider(recipient: str, payload: Dict[str, Any]) -> None:
        message = payload.get("message", "No message")
        logger.info(f"[SMS] To: {recipient} | Message: {message}")
        time.sleep(1)

        if "transient-fail" in recipient:
            raise RetryableNotificationError("Simulated Twilio timeout")

        logger.info(f"[SMS] Successfully sent to {recipient}")

        