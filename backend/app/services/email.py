import httpx
import logging
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings
from app.schemas.onboarding import EmailConfig
from app.models.communication_log import CommunicationLog
from app.models.workspace import Workspace
from app.db.session import SessionLocal
from app.core.security_utils import decrypt_token

# Google Libraries
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# CORE SENDING LOGIC
# ---------------------------------------------------------

async def _send_gmail_email(
    to_email: str, 
    subject: str, 
    html_content: str, 
    log_data: Dict[str, Any],
    reply_to: Optional[str] = None
):
    """
    Sends email via Gmail API using the Owner's connected account.
    Falls back gracefully if not connected or error occurs.
    """
    workspace_id = log_data.get("workspace_id")
    if not workspace_id:
        logger.error("Missing workspace_id for email sending")
        return

    db = SessionLocal()
    
    # Create Log Entry (Pending)
    log_entry = CommunicationLog(
        workspace_id=workspace_id,
        contact_id=log_data.get("contact_id"),
        booking_id=log_data.get("booking_id"),
        type=log_data.get("type"),
        recipient_email=to_email,
        status="pending"
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    try:
        from app.services.gmail_client import GmailClientService
        from app.models.email_integration import EmailIntegration

        # 1. GET WORKSPACE (for from name)
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            logger.error(f"Workspace {workspace_id} not found.")
            return

        # 2. CHECK CONNECTION (New Model)
        integration = GmailClientService.get_integration(workspace_id, db)
        
        if not integration:
            logger.warning(f"Workspace {workspace_id} has no active Gmail integration. Email skipped.")
            logger.info(f"SKIPPED EMAIL to {to_email}. Subject: {subject}")
            log_entry.status = "failed"
            log_entry.error_message = "Gmail not connected"
            db.commit()
            return

        # 3. BUILD MESSAGE
        message = MIMEMultipart()
        # ... (headers setup is fine) ...
        
        # 3. BUILD MESSAGE (Real)
        message = MIMEMultipart()
        message['to'] = to_email
        message['subject'] = subject
        
        # From Name
        from_name = workspace.google_from_name or workspace.name
        message['from'] = f"{from_name} <{integration.email}>"
        
        if reply_to:
            message['reply-to'] = reply_to

        msg = MIMEText(html_content, 'html')
        message.attach(msg)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        body = {'raw': raw_message}

        # 4. SEND via GMAIL API
        # We run this in executor to avoid blocking async loop
        def build_and_send():
            # This handles token refresh automatically
            service = GmailClientService.get_gmail_client(workspace_id, db)
            return service.users().messages().send(userId='me', body=body).execute()

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, build_and_send)
        
        logger.info(f"Email sent via Gmail API. ID: {result.get('id')}")
        log_entry.status = "success"
        log_entry.sent_at = datetime.now(timezone.utc)
        
    except Exception as e:
        error_msg = f"Gmail Send Failed: {str(e)}"
        logger.error(error_msg)
        log_entry.status = "failed"
        log_entry.error_message = error_msg
        
    finally:
        db.commit()
        db.close()

# ---------------------------------------------------------
# WRAPPER FOR BACKWARD COMPATIBILITY
# Replaces old _send_resend_email
# ---------------------------------------------------------

async def _send_resend_email(
    to_email: str, 
    subject: str, 
    html_content: str, 
    log_data: Dict[str, Any],
    reply_to: Optional[str] = None
):
    """
    Legacy name, new implementation. Routes everything to Gmail.
    """
    await _send_gmail_email(to_email, subject, html_content, log_data, reply_to)

# ---------------------------------------------------------
# TEMPLATE ENGINE
# ---------------------------------------------------------

def _get_map_link(address: str) -> str:
    import urllib.parse
    encoded = urllib.parse.quote(address)
    return f"https://www.google.com/maps/search/?api=1&query={encoded}"

def _render_email_template(
    title: str,
    body_content: str,
    workspace_name: str,
    workspace_address: Optional[str] = None,
    workspace_phone: Optional[str] = None,
    action_button_text: Optional[str] = None,
    action_button_url: Optional[str] = None,
    preview_text: str = ""
) -> str:
    """
    Renders a pixel-perfect, Stripe/HubSpot-quality HTML email.
    """
    # 1. Formatting
    address = workspace_address or "Business Location"
    map_link = _get_map_link(address)
    
    # 2. CSS Styles (Inline for email compatibility)
    style_body = "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #3c4257; background-color: #f7f8fa; margin: 0; padding: 0; width: 100%;"
    style_wrapper = "max-width: 600px; margin: 0 auto; padding: 40px 20px;"
    style_card = "background-color: #ffffff; border-radius: 8px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); padding: 40px; margin-bottom: 24px;"
    style_header = "margin-bottom: 24px;"
    style_logo = "font-weight: 700; font-size: 24px; color: #3c4257; text-decoration: none; display: block;"
    style_h1 = "font-size: 20px; font-weight: 600; color: #1a1f36; margin: 0 0 16px 0;"
    style_p = "margin: 0 0 16px 0; color: #3c4257;"
    style_button_container = "margin: 32px 0;"
    style_button = "display: inline-block; background-color: #5469d4; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 4px; font-weight: 600; font-size: 16px;"
    style_footer = "margin-top: 32px; font-size: 13px; color: #8792a2; text-align: center;"
    style_footer_link = "color: #8792a2; text-decoration: underline;"
    
    # 3. Components
    action_section = ""
    if action_button_text and action_button_url:
        action_section = f"""
        <div style="{style_button_container}">
            <a href="{action_button_url}" style="{style_button}" target="_blank">{action_button_text}</a>
        </div>
        """

    support_info = f"{workspace_phone}" if workspace_phone else ""
    
    # 4. Assembly
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>
    <body style="{style_body}">
        <div style="display: none; max-height: 0px; overflow: hidden;">
            {preview_text}
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        </div>
        
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f7f8fa;">
            <tr>
                <td align="center">
                    <div style="{style_wrapper}">
                        <!-- Header -->
                        <div style="{style_header}">
                             <div style="{style_logo}">{workspace_name}</div>
                        </div>
                        
                        <!-- Main Card -->
                        <div style="{style_card}">
                            <h1 style="{style_h1}">{title}</h1>
                            
                            <div style="color: #3c4257;">
                                {body_content}
                            </div>
                            
                            {action_section}
                            
                            <p style="{style_p}; margin-top: 32px; font-size: 14px; color: #8792a2;">
                                &mdash;<br>{workspace_name} Team
                            </p>
                        </div>
                        
                        <!-- Footer -->
                        <div style="{style_footer}">
                            <p style="margin-bottom: 8px;">
                                {workspace_name}<br>
                                {address}
                            </p>
                            <p style="margin-bottom: 16px;">
                                <a href="{map_link}" style="{style_footer_link}">Get Directions</a>
                                {f'&bull; {support_info}' if support_info else ''}
                            </p>
                            
                            <p style="margin-top: 24px; font-size: 12px; color: #a3acb9;">
                                Problems or questions? Reply to this email.<br>
                                If you did not expect this email, please contact us immediately.
                            </p>
                        </div>
                    </div>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

# ---------------------------------------------------------
# BUSINESS LOGIC EMAILS
# ---------------------------------------------------------

async def send_test_email(workspace_id: int):
    # New helper for the test button
    db = SessionLocal()
    try:
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace or not workspace.google_email: return

        log_data = {
            "workspace_id": workspace.id,
            "type": "test_email"
        }
        
        subject = "CareOps Gmail Integration Test"
        body = """
            <p style="margin: 0 0 16px 0; color: #3c4257;"><strong>It Works!</strong></p>
            <p style="margin: 0 0 16px 0; color: #3c4257;">This email was sent via your connected Google account. You are ready to send booking notifications.</p>
        """
        
        html = _render_email_template(
            title=subject,
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address
        )
        
        await _send_gmail_email(workspace.google_email, subject, html, log_data)
    finally:
        db.close()


async def send_welcome_email(contact_email: str, booking_url: Optional[str] = None):
    from app.models.contact import Contact
    db = SessionLocal()
    email_args = None
    try:
        contact = db.query(Contact).filter(Contact.email == contact_email).order_by(Contact.id.desc()).first()
        if not contact: return
        workspace = contact.workspace

        subject = "Welcome to CareOps – Next Steps"
        
        if booking_url:
            body = f"""
                <p style="margin: 0 0 16px 0; color: #3c4257;">Hi {contact.first_name or 'there'},</p>
                <p style="margin: 0 0 16px 0; color: #3c4257;">Thanks for reaching out. We received your information.</p>
                <p style="margin: 0 0 16px 0; color: #3c4257;"><strong>Please use the link below to schedule your appointment:</strong></p>
            """
            action_text = "Book Appointment"
            action_url = booking_url
        else:
            body = f"""
                <p style="margin: 0 0 16px 0; color: #3c4257;">Hi {contact.first_name or 'there'},</p>
                <p style="margin: 0 0 16px 0; color: #3c4257;">Thanks for connecting with us. We have received your information and will be in touch shortly regarding your needs.</p>
                <p style="margin: 0 0 16px 0; color: #3c4257;">Best regards,</p>
            """
            action_text = None
            action_url = None
        
        html = _render_email_template(
            title=subject,
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            action_button_text=action_text,
            action_button_url=action_url,
            preview_text="Here is your requested information."
        )
        
        log_data = {
            "workspace_id": contact.workspace_id,
            "contact_id": contact.id,
            "type": "welcome"
        }
        
        email_args = (contact_email, subject, html, log_data)
        
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)

async def send_booking_confirmation(booking_id: int):
    from app.models.booking import Booking
    
    db = SessionLocal()
    email_args = None
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking: return
        workspace = booking.workspace
            
        date_str = booking.start_time.strftime('%A, %B %d')
        time_str = booking.start_time.strftime('%I:%M %p')
        service_name = booking.service.name
        customer_name = (booking.contact and booking.contact.first_name) or "there"
        address = getattr(workspace, "address", "Business Location") or "Business Location"
        map_link = _get_map_link(address)
        
        # Links
        from app.core.security_utils import generate_cancel_token
        token = generate_cancel_token(booking.id)
        
        # FIXED: Corrected paths for public pages with security tokens
        reschedule_link = f"{settings.FRONTEND_URL}/booking/{workspace.slug}/reschedule?booking={booking.id}&token={token}"
        cancel_link = f"{settings.FRONTEND_URL}/booking/{workspace.slug}/cancel?booking={booking.id}&token={token}"
        
        subject = f"Your {service_name} is confirmed – {date_str} at {time_str}"
        
        body = f"""
            <p>Hi {customer_name},</p>
            <p>Great news 🎉<br>Your appointment is confirmed.</p>
            
            <div style="background-color: #f7f8fa; padding: 24px; border-radius: 4px; margin: 24px 0;">
                <p style="margin: 0 0 8px 0; color: #3c4257;"><strong>Service:</strong> {service_name}</p>
                <p style="margin: 0 0 8px 0; color: #3c4257;"><strong>Date:</strong> {date_str}</p>
                <p style="margin: 0 0 8px 0; color: #3c4257;"><strong>Time:</strong> {time_str}</p>
                <p style="margin: 0; color: #3c4257;"><strong>Location:</strong> {address}</p>
                <p style="margin: 12px 0 0 0; font-size: 14px;"><a href="{map_link}" style="color: #5469d4; text-decoration: none;">📍 Get Directions</a></p>
            </div>

            <p style="font-size: 14px; color: #3c4257;">
                Need to make changes?<br>
                <a href="{reschedule_link}" style="color: #5469d4;">Reschedule</a> &bull; <a href="{cancel_link}" style="color: #5469d4;">Cancel</a>
            </p>
            
            <p style="margin-top: 24px;">We look forward to seeing you at {workspace.name}.</p>
            <p style="font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 16px; margin-top: 32px;">
                {workspace.name}<br>
                {address}
            </p>
        """
        
        html = _render_email_template(
            title="Appointment Confirmed",
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            preview_text=f"Your appointment for {service_name} is confirmed."
        )
        
        if booking.contact and booking.contact.email:
             log_data = {
                "workspace_id": booking.workspace_id,
                "contact_id": booking.contact_id,
                "booking_id": booking.id,
                "type": "confirmation"
             }
             email_args = (booking.contact.email, subject, html, log_data)
             
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)

async def send_form_magic_link(booking_id: int):
    from app.models.booking import Booking
    
    db = SessionLocal()
    email_args = None
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking or not booking.contact: return
        workspace = booking.workspace

        link = f"{settings.FRONTEND_URL}/forms/intake/{booking_id}"
        customer_name = (booking.contact and booking.contact.first_name) or "there"
        
        subject = "Action needed before your visit"
        
        body = f"""
            <p style="margin: 0 0 16px 0; color: #3c4257;">Hi {customer_name},</p>
            <p style="margin: 0 0 16px 0; color: #3c4257;">Before your appointment, please complete this form:</p>
            <p style="margin: 0 0 16px 0; color: #3c4257;">It takes less than 2 minutes and helps us prepare.</p>
            <p style="margin: 0 0 16px 0; color: #3c4257;">Thank you 🙏</p>
        """
        
        html = _render_email_template(
            title=subject,
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            action_button_text="Complete Intake Form",
            action_button_url=link,
            preview_text="Please complete your intake form before your visit."
        )
        
        if booking.contact.email:
             log_data = {
                "workspace_id": booking.workspace_id,
                "contact_id": booking.contact_id,
                "booking_id": booking.id,
                "type": "form_link"
             }
             email_args = (booking.contact.email, subject, html, log_data)

    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)

async def send_booking_reminder(booking_id: int):
    from app.models.booking import Booking
    
    db = SessionLocal()
    email_args = None
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking or not booking.contact: return
        workspace = booking.workspace

        date_str = booking.start_time.strftime('%A, %B %d')
        time_str = booking.start_time.strftime('%I:%M %p')
        customer_name = (booking.contact and booking.contact.first_name) or "there"
        
        # Links
        from app.core.security_utils import generate_cancel_token
        token = generate_cancel_token(booking.id)
        
        # FIXED: Corrected paths for public pages with security tokens
        reschedule_link = f"{settings.FRONTEND_URL}/booking/{workspace.slug}/reschedule?booking={booking.id}&token={token}"
        cancel_link = f"{settings.FRONTEND_URL}/booking/{workspace.slug}/cancel?booking={booking.id}&token={token}"

        subject = f"Reminder – {date_str} at {time_str}"
        
        body = f"""
            <p>Hi {customer_name},</p>
            <p>Friendly reminder about your upcoming visit.</p>
            
            <div style="background-color: #f7f8fa; padding: 24px; border-radius: 4px; margin: 24px 0;">
                <p style="margin: 0 0 8px 0; color: #3c4257;"><strong>Service:</strong> {booking.service.name}</p>
                <p style="margin: 0 0 8px 0; color: #3c4257;"><strong>Date:</strong> {date_str}</p>
                <p style="margin: 0; color: #3c4257;"><strong>Time:</strong> {time_str}</p>
            </div>
            
            <p style="font-size: 14px; color: #3c4257;">
                Need to update?<br>
                <a href="{reschedule_link}" style="color: #5469d4;">Reschedule</a> &bull; <a href="{cancel_link}" style="color: #5469d4;">Cancel</a>
            </p>
            
            <p style="margin-top: 24px;">See you soon.</p>
        """
        
        html = _render_email_template(
            title="Appointment Reminder",
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            preview_text=f"Reminder for your appointment on {date_str}."
        )
        
        if booking.contact.email:
             log_data = {
                "workspace_id": booking.workspace_id,
                "contact_id": booking.contact_id,
                "booking_id": booking.id,
                "type": "reminder"
             }
             email_args = (booking.contact.email, subject, html, log_data)
             
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)

async def send_reply_email(message_id: int):
    from app.models.conversation import Message, Conversation
    
    db = SessionLocal()
    email_args = None
    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message: return
            
        conversation = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
        if not conversation or not conversation.contact: return
        workspace = db.query(Workspace).filter(Workspace.id == conversation.workspace_id).first()
            
        subject = f"Re: {conversation.subject}"
        
        # Simple body for replies, but wrapped in branding
        body = f"""
            <div style="white-space: pre-wrap;">{message.content}</div>
        """
        
        html = _render_email_template(
            title=subject,
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            preview_text=message.content[:100]
        )
        
        if conversation.contact.email:
             log_data = {
                "workspace_id": conversation.workspace_id,
                "contact_id": conversation.contact_id,
                "type": "reply"
             }
             email_args = (conversation.contact.email, subject, html, log_data)
             
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)

async def send_form_reminder(submission_id: int):
    # Reusing the Intake Form Logic but with urgency
    from app.models.form import FormSubmission
    
    db = SessionLocal()
    email_args = None
    try:
        sub = db.query(FormSubmission).filter(FormSubmission.id == submission_id).first()
        if not sub or not sub.booking: return
        booking = sub.booking
        if not booking.contact or not booking.contact.email: return
        workspace = booking.workspace

        link = f"{settings.FRONTEND_URL}/forms/intake/{booking.id}"
        customer_name = (booking.contact and booking.contact.first_name) or "there"

        subject = "Urgent: Form Incomplete"
        
        body = f"""
            <p>Hi {customer_name},</p>
            <p>Your appointment is coming up, but we still need your intake form.</p>
            <p>Please complete it now to ensure we can keep your appointment.</p>
        """
        
        html = _render_email_template(
            title=subject,
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            action_button_text="Complete Form Now",
            action_button_url=link,
            preview_text="Action required: Please complete your intake form."
        )
        
        log_data = {
            "workspace_id": booking.workspace_id,
            "contact_id": booking.contact_id,
            "booking_id": booking.id,
            "type": "form_reminder"
        }
        email_args = (booking.contact.email, subject, html, log_data)
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)

async def send_inventory_alert(item_id: int):
    from app.models.inventory import InventoryItem
    from app.models.workspace import Workspace
    
    db = SessionLocal()
    email_args = None
    try:
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item: return
        
        workspace = db.query(Workspace).filter(Workspace.id == item.workspace_id).first()
        if not workspace or not workspace.contact_email: return
        
        subject = f"LOGISTICS ALERT: Low Stock for {item.name}"
        body = f"""
            <p><strong>Low Stock Alert</strong></p>
            <p>Item: <strong>{item.name}</strong></p>
            <p>Current Quantity: <span style="color: red; font-weight: bold;">{item.quantity}</span></p>
            <p>Threshold: {item.threshold}</p>
            <p>Please restock immediately to avoid service disruption.</p>
        """
        
        html = _render_email_template(
            title=subject,
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            action_button_text="View Inventory",
            action_button_url=f"{settings.FRONTEND_URL}/inventory"
        )
        
        log_data = {
            "workspace_id": workspace.id,
            "type": "inventory"
        }
        
        email_args = (workspace.contact_email, subject, html, log_data)
        
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)

async def send_staff_invite(email: str, password: str):
    from app.models.user import User
    
    db = SessionLocal()
    email_args = None
    try:
        user = db.query(User).filter(User.email == email).first()
        workspace = user.workspace if user else None
        workspace_name = workspace.name if workspace else "CareOps"
        workspace_address = workspace.address if workspace else None
        
        subject = "You have been invited to CareOps"
        body = f"""
            <h1 style="font-size: 20px; font-weight: 600; color: #1a1f36; margin: 0 0 16px 0;">Welcome to the Team</h1>
            <p style="margin: 0 0 16px 0; color: #3c4257;">You have been invited to join {workspace_name}.</p>
            
            <div style="background-color: #f7f8fa; padding: 15px; margin: 24px 0; border-radius: 6px;">
                <p style="margin: 0 0 5px 0; color: #3c4257;"><strong>Username:</strong> {email}</p>
                <p style="margin: 0; color: #3c4257;"><strong>Password:</strong> {password}</p>
            </div>
            
            <p style="margin: 0 0 16px 0; color: #3c4257;">Please change your password upon logging in.</p>
        """
        
        html = _render_email_template(
            title=subject,
            body_content=body,
            workspace_name=workspace_name,
            workspace_address=workspace_address,
            action_button_text="Login to Workspace",
            action_button_url=f"{settings.FRONTEND_URL}/login"
        )
        
        log_data = {
            "workspace_id": workspace.id if workspace else None,
            "type": "staff_invite"
        }
        
        email_args = (email, subject, html, log_data)
        
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)

async def send_booking_cancellation(booking_id: int):
    from app.models.booking import Booking
    
    db = SessionLocal()
    email_args = None
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking or not booking.contact: return
        workspace = booking.workspace
        
        customer_name = (booking.contact and booking.contact.first_name) or "there"
        date_str = booking.start_time.strftime('%A, %B %d')
        time_str = booking.start_time.strftime('%I:%M %p')
        
        # FIXED: Corrected path for public booking page
        booking_link = f"{settings.FRONTEND_URL}/workspaces/{workspace.slug}/book"

        subject = "Your booking has been cancelled"
        
        body = f"""
            <p style="margin: 0 0 16px 0; color: #3c4257;">Hi {customer_name},</p>
            <p style="margin: 0 0 16px 0; color: #3c4257;">Your appointment for <strong>{date_str} at {time_str}</strong> has been cancelled.</p>
            <p style="margin: 0 0 16px 0; color: #3c4257;">We hope to see you again soon.</p>
            
            <p style="font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 16px; margin-top: 32px;">
                {workspace.name}<br>
                {address}
            </p>
        """,
        
        html = _render_email_template(
            title="Appointment Cancelled",
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            action_button_text="Book Again Anytime",
            action_button_url=booking_link,
            preview_text="Cancellation confirmation for your appointment."
        )
        
        if booking.contact.email:
             log_data = {
                "workspace_id": booking.workspace_id,
                "contact_id": booking.contact_id,
                "booking_id": booking.id,
                "type": "cancellation"
             }
             email_args = (booking.contact.email, subject, html, log_data)
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)

async def send_booking_reschedule(booking_id: int):
    from app.models.booking import Booking
    
    db = SessionLocal()
    email_args = None
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking or not booking.contact: return
        workspace = booking.workspace

        date_str = booking.start_time.strftime('%A, %B %d')
        time_str = booking.start_time.strftime('%I:%M %p')
        customer_name = (booking.contact and booking.contact.first_name) or "there"
        address = getattr(workspace, "address", "Business Location") or "Business Location"
        map_link = _get_map_link(address)
        
        subject = f"New time confirmed – {date_str} at {time_str}"

        body = f"""
            <p>Hi {customer_name},</p>
            <p>Your appointment has been updated.</p>

            <div style="background-color: #f7f8fa; padding: 24px; border-radius: 4px; margin: 24px 0;">
                <p style="margin: 0 0 8px 0; color: #3c4257;"><strong>New Schedule:</strong></p>
                <p style="margin: 0 0 8px 0; color: #3c4257;">{date_str} at {time_str}</p>
                <p style="margin: 0; color: #3c4257;"><strong>Location:</strong> {address}</p>
                <p style="margin: 12px 0 0 0; font-size: 14px;"><a href="{map_link}" style="color: #5469d4; text-decoration: none;">📍 Get Directions</a></p>
            </div>

            <p>We’ll see you then.</p>
        """
        
        html = _render_email_template(
            title="Appointment Rescheduled",
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            preview_text=f"Your appointment is now on {date_str}."
        )
        
        if booking.contact.email:
             log_data = {
                "workspace_id": booking.workspace_id,
                "contact_id": booking.contact_id,
                "booking_id": booking.id,
                "type": "reschedule"
             }
             email_args = (booking.contact.email, subject, html, log_data)
    finally:
        db.close()
    
    if email_args:
        await _send_gmail_email(*email_args)

async def send_visit_completion(booking_id: int):
    from app.models.booking import Booking
    
    db = SessionLocal()
    email_args = None
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking or not booking.contact: return
        workspace = booking.workspace
        
        customer_name = (booking.contact and booking.contact.first_name) or "there"
        booking_link = f"{settings.FRONTEND_URL}/workspaces/{workspace.slug}/book"

        subject = f"Thank you for visiting {workspace.name}"
        
        body = f"""
            <p style="margin: 0 0 16px 0; color: #3c4257;">Hi {customer_name},</p>
            <p style="margin: 0 0 16px 0; color: #3c4257;">Thank you for choosing us ❤️</p>
            <p style="margin: 0 0 16px 0; color: #3c4257;">Have a great day.</p>
        """

        html = _render_email_template(
            title="Thank You",
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            action_button_text="Book Again",
            action_button_url=booking_link,
            preview_text=f"Thanks for visiting {workspace.name}."
        )
        
        if booking.contact.email:
             log_data = {
                "workspace_id": booking.workspace_id,
                "contact_id": booking.contact_id,
                "booking_id": booking.id,
                "type": "thank_you"
             }
             email_args = (booking.contact.email, subject, html, log_data)
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)
        
async def notify_owner_new_message(message_id: int):
    from app.models.conversation import Message, Conversation
    
    db = SessionLocal()
    email_args = None
    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message: return
        
        conversation = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
        workspace = db.query(Workspace).filter(Workspace.id == conversation.workspace_id).first()
        
        if not workspace or not workspace.contact_email: return
        
        subject = f"New Message: {conversation.subject}"
        
        body = f"""
            <p><strong>New message from {message.sender_email}</strong></p>
            <div style="background-color: #f7f8fa; padding: 15px; border-radius: 4px; border-left: 4px solid #5469d4;">
                {message.content}
            </div>
            <p>Reply directly in your dashboard.</p>
        """
        
        html = _render_email_template(
            title="New Inquiry",
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            action_button_text="View in Inbox",
            action_button_url=f"{settings.FRONTEND_URL}/inbox",
            preview_text=f"New message from {message.sender_email}"
        )
        
        log_data = {
            "workspace_id": workspace.id,
            "type": "owner_alert"
        }
        
        email_args = (workspace.contact_email, subject, html, log_data)
        
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)

async def send_daily_owner_alert(workspace_id: int, unanswered_count: int, low_stock_count: int):
    from app.models.workspace import Workspace
    
    db = SessionLocal()
    email_args = None
    try:
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace or not workspace.contact_email: return
        
        if unanswered_count == 0 and low_stock_count == 0:
            return 

        subject = f"Daily Operations Summary: Action Required"
        
        body = f"""
            <p>Here is what needs your attention today:</p>
            <ul>
                <li><strong>{unanswered_count}</strong> unanswered messages</li>
                <li><strong>{low_stock_count}</strong> items with low stock</li>
            </ul>
        """
        
        html = _render_email_template(
            title="Daily Summary",
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            action_button_text="Go to Dashboard",
            action_button_url=f"{settings.FRONTEND_URL}/dashboard"
        )
        
        log_data = {
            "workspace_id": workspace.id,
            "type": "owner_alert"
        }
        
        email_args = (workspace.contact_email, subject, html, log_data)
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)

async def notify_owner_intake(booking_id: int):
    from app.models.booking import Booking
    
    db = SessionLocal()
    email_args = None
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking: return
        
        workspace = booking.workspace
        contact = booking.contact
        if not workspace or not workspace.contact_email: return
        
        subject = f"Intake Form Completed: {contact.first_name}"
        
        body = f"""
            <p><strong>Intake Form Completed</strong></p>
            <p>Customer: <strong>{contact.full_name}</strong></p>
            <p>Service: {booking.service.name}</p>
            <p>Date: {booking.start_time.strftime('%A, %B %d at %I:%M %p')}</p>
            <p>The customer has completed their pre-visit form.</p>
        """
        
        html = _render_email_template(
            title="Intake Received",
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            action_button_text="View Booking",
            action_button_url=f"{settings.FRONTEND_URL}/dashboard/bookings/{booking_id}",
            preview_text=f"Intake form completed by {contact.full_name}"
        )
        
        log_data = {
            "workspace_id": workspace.id,
            "type": "owner_alert"
        }
        
        email_args = (workspace.contact_email, subject, html, log_data)
        
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)

async def send_intake_received_email(submission_id: int):
    from app.models.form import FormSubmission
    
    db = SessionLocal()
    email_args = None
    try:
        sub = db.query(FormSubmission).filter(FormSubmission.id == submission_id).first()
        if not sub or not sub.booking: return
        booking = sub.booking
        if not booking.contact or not booking.contact.email: return
        workspace = booking.workspace

        customer_name = (booking.contact and booking.contact.first_name) or "there"
        service = booking.service.name if booking.service else "your appointment"
        
        subject = "We received your intake form"
        
        body = f"""
            <p>Hi {customer_name},</p>
            <p>Thanks for completing your intake form for <strong>{service}</strong>.</p>
            <p>Your information has been safely received.</p>
            <p>We look forward to seeing you soon.</p>
        """
        
        html = _render_email_template(
            title="Form Received",
            body_content=body,
            workspace_name=workspace.name,
            workspace_address=workspace.address,
            preview_text="Your intake form has been received."
        )
        
        log_data = {
            "workspace_id": booking.workspace_id,
            "contact_id": booking.contact_id,
            "booking_id": booking.id,
            "type": "form_received"
        }
        email_args = (booking.contact.email, subject, html, log_data)
        
    finally:
        db.close()
        
    if email_args:
        await _send_gmail_email(*email_args)
