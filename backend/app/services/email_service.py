"""Email service — business logic for formatting and sending emails.

Defines HTML templates and dispatches requests to the ResendEmailClient.
All sending methods fail open and handle exceptions internally so that
email delivery failures do not block core platform transactions.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.integrations.resend_email import ResendEmailClient

logger = logging.getLogger(__name__)


# ── CSS & HTML Layout Boilerplate ──────────────────────────────────────────

HTML_WRAPPER = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StaySync Notification</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: #f9fafb;
      margin: 0;
      padding: 0;
      color: #1f2937;
    }}
    .container {{
      max-width: 600px;
      margin: 20px auto;
      background-color: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
    .header {{
      background-color: #4f46e5; /* Indigo primary */
      color: #ffffff;
      padding: 24px;
      text-align: center;
    }}
    .header h1 {{
      margin: 0;
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.025em;
    }}
    .content {{
      padding: 32px 24px;
      line-height: 1.6;
    }}
    .content h2 {{
      margin-top: 0;
      color: #111827;
      font-size: 18px;
      font-weight: 700;
    }}
    .details-box {{
      background-color: #f3f4f6;
      border-radius: 8px;
      padding: 16px;
      margin: 20px 0;
      border: 1px solid #e5e7eb;
    }}
    .details-row {{
      margin: 8px 0;
      font-size: 14px;
    }}
    .details-label {{
      font-weight: 600;
      color: #4b5563;
    }}
    .button-container {{
      text-align: center;
      margin: 24px 0;
    }}
    .button {{
      display: inline-block;
      background-color: #4f46e5;
      color: #ffffff !important;
      text-decoration: none;
      padding: 12px 24px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 14px;
    }}
    .footer {{
      background-color: #f9fafb;
      padding: 20px 24px;
      text-align: center;
      font-size: 12px;
      color: #9ca3af;
      border-top: 1px solid #e5e7eb;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>StaySync</h1>
    </div>
    <div class="content">
      {content_html}
    </div>
    <div class="footer">
      &copy; {year} StaySync. All rights reserved.<br>
      This is an automated notification. Please do not reply directly.
    </div>
  </div>
</body>
</html>
"""


class EmailService:
    """Orchestrates formatting and dispatch of system email notifications."""

    def __init__(self, email_client: ResendEmailClient | None = None) -> None:
        self._email_client = email_client or ResendEmailClient()

    async def _send_safe(self, to: str, subject: str, content_html: str) -> bool:
        """Helper to wrap sending in try-except block to fail open."""
        year = str(datetime.utcnow().year)
        full_html = HTML_WRAPPER.format(content_html=content_html, year=year)

        try:
            return await self._email_client.send_email(
                to=to,
                subject=subject,
                html=full_html,
            )
        except Exception as exc:
            logger.exception("EmailService failed open: could not send email to %s", to)
            return False

    async def send_hold_approved_email(
        self,
        *,
        to: str,
        name: str,
        property_name: str,
        bed_label: str,
        expires_at: str,
    ) -> bool:
        """Notify student that their hold request has been approved."""
        subject = f"Hold Approved: Bed {bed_label} in {property_name}"
        content = f"""
        <h2>Hello {name},</h2>
        <p>Great news! Your request to hold a bed has been approved by the property owner. You now have a temporary reservation.</p>
        
        <div class="details-box">
          <div class="details-row"><span class="details-label">Property:</span> {property_name}</div>
          <div class="details-row"><span class="details-label">Bed/Room:</span> {bed_label}</div>
          <div class="details-row"><span class="details-label">Expires At:</span> {expires_at} (UTC)</div>
        </div>

        <p>Please log in to your dashboard to complete your booking before the hold expires. If you do not book within this window, the hold will automatically expire, and the bed will be released to the next person on the waitlist.</p>
        """
        return await self._send_safe(to, subject, content)

    async def send_hold_expiring_soon_email(
        self,
        *,
        to: str,
        name: str,
        property_name: str,
        bed_label: str,
        expires_at: str,
    ) -> bool:
        """Alert student that their hold expires in 1 hour."""
        subject = f"URGENT: Hold Expiring Soon for {property_name}"
        content = f"""
        <h2>Hello {name},</h2>
        <p>This is a quick reminder that your active bed hold reservation will expire in approximately <strong>1 hour</strong>.</p>
        
        <div class="details-box">
          <div class="details-row"><span class="details-label">Property:</span> {property_name}</div>
          <div class="details-row"><span class="details-label">Bed/Room:</span> {bed_label}</div>
          <div class="details-row"><span class="details-label">Expires At:</span> {expires_at} (UTC)</div>
        </div>

        <p>To secure this accommodation, please log in and finalize your booking immediately. Once expired, your hold cannot be restored, and you will lose your place in the queue.</p>
        """
        return await self._send_safe(to, subject, content)

    async def send_waitlist_promoted_email(
        self,
        *,
        to: str,
        name: str,
        property_name: str,
        bed_label: str,
        expires_at: str,
    ) -> bool:
        """Notify waitlisted student that they have been promoted to an approved hold."""
        subject = f"Waitlist Promotion: Hold Approved for {property_name}"
        content = f"""
        <h2>Hello {name},</h2>
        <p>You have been automatically promoted from the waitlist! A temporary hold has been approved for you.</p>
        
        <div class="details-box">
          <div class="details-row"><span class="details-label">Property:</span> {property_name}</div>
          <div class="details-row"><span class="details-label">Bed/Room:</span> {bed_label}</div>
          <div class="details-row"><span class="details-label">Expires At:</span> {expires_at} (UTC)</div>
        </div>

        <p>Please log in and complete your booking registration before this hold expires to secure your spot.</p>
        """
        return await self._send_safe(to, subject, content)

    async def send_booking_confirmed_email(
        self,
        *,
        to: str,
        name: str,
        property_name: str,
        bed_label: str,
        booking_id: str,
    ) -> bool:
        """Confirm student's booking."""
        subject = f"Booking Confirmed! Bed {bed_label} in {property_name}"
        content = f"""
        <h2>Hello {name},</h2>
        <p>Congratulations! Your booking request is officially confirmed. You have successfully secured your stay.</p>
        
        <div class="details-box">
          <div class="details-row"><span class="details-label">Booking ID:</span> {booking_id}</div>
          <div class="details-row"><span class="details-label">Property:</span> {property_name}</div>
          <div class="details-row"><span class="details-label">Bed/Room:</span> {bed_label}</div>
        </div>

        <p>We have notified the property manager of your confirmation. They will contact you shortly to coordinate check-in procedures and keys.</p>
        """
        return await self._send_safe(to, subject, content)

    async def send_property_stale_email(
        self,
        *,
        to: str,
        name: str,
        property_name: str,
        threshold_days: int,
    ) -> bool:
        """Inform owner that their listing has been marked inactive due to stale data."""
        subject = f"Listing Deactivated: {property_name}"
        content = f"""
        <h2>Hello {name},</h2>
        <p>Your property listing <strong>{property_name}</strong> has been marked as <strong>inactive</strong> because it has not been updated or refreshed for {threshold_days} days.</p>
        
        <p>To make your listing active and visible to students again, please log in to your owner dashboard and click the "Refresh Listing" action on your property card.</p>
        """
        return await self._send_safe(to, subject, content)
