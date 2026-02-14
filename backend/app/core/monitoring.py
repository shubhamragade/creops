"""
Monitoring Lite

Structured logging helpers for key business events.
No heavy frameworks. Just clarity.
"""

import logging

logger = logging.getLogger(__name__)


def log_booking_created(booking_id, service_name, contact_email):
    """Log booking creation event"""
    logger.info(f"[BOOKING] Created booking_id={booking_id} service={service_name} contact={contact_email}")


def log_email_attempted(email_type, recipient, status):
    """Log email attempt event"""
    logger.info(f"[EMAIL] type={email_type} recipient={recipient} status={status}")


def log_reply_pause(conversation_id, paused_until):
    """Log conversation pause event"""
    logger.info(f"[AUTOMATION] Conversation {conversation_id} paused until {paused_until}")


def log_inventory_changed(item_id, item_name, old_qty, new_qty, reason=""):
    """Log inventory change event"""
    reason_text = f" reason={reason}" if reason else ""
    logger.info(f"[INVENTORY] item={item_name} (id={item_id}) changed from {old_qty} to {new_qty}{reason_text}")
