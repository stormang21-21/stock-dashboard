"""
Email Module - Send transactional emails

Usage:
    from modules.email import EmailService
    
    email = EmailService()
    email.send_welcome(user_email, user_name)
    email.send_payment_confirmation(...)
"""

from .service import EmailService
from .templates import EmailTemplates

__all__ = ["EmailService", "EmailTemplates"]
