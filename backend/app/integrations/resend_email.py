"""Resend email client integration wrapper.

Uses ``httpx.AsyncClient`` to call the Resend API. Supports a fallback
mock mode in development or when the Resend API key is missing.
"""

from __future__ import annotations

import logging
import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ResendEmailClient:
    """Client wrapper for Resend API email transmission."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.EMAIL_API_KEY
        self._from_address = settings.EMAIL_FROM_ADDRESS
        self._api_url = "https://api.resend.com/emails"

    async def send_email(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        text: str | None = None,
    ) -> bool:
        """Send an email using Resend API.

        If the EMAIL_API_KEY setting is missing or empty, logs the email payload
        to the console/logger and returns True (fail-open/mock mode).

        Args:
            to: Recipient email address.
            subject: Email subject.
            html: HTML body.
            text: Optional plain text body.

        Returns:
            bool: True if sent successfully (or mock logged), False otherwise.
        """
        if not self._api_key:
            logger.info(
                "MOCK EMAIL DISPATCH (EMAIL_API_KEY missing):\n"
                "  From: %s\n"
                "  To: %s\n"
                "  Subject: %s\n"
                "  Body (HTML snippet): %s...",
                self._from_address,
                to,
                subject,
                html[:200].replace("\n", " "),
            )
            return True

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": self._from_address,
            "to": to,
            "subject": subject,
            "html": html,
        }
        if text:
            payload["text"] = text

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self._api_url,
                    json=payload,
                    headers=headers,
                )
                if response.status_code >= 400:
                    logger.error(
                        "Resend API error: status=%d response=%s",
                        response.status_code,
                        response.text,
                    )
                    return False
                
                logger.info("Email sent successfully via Resend to %s", to)
                return True
        except Exception as exc:
            logger.exception("Failed to send email to %s via Resend", to)
            return False
