"""
Email Service - Send emails via SMTP or API

Configuration:
    EMAIL_PROVIDER: 'smtp' or 'sendgrid' or 'ses'
    SMTP_HOST: smtp.gmail.com
    SMTP_PORT: 587
    SMTP_USER: your@email.com
    SMTP_PASS: your_password
    FROM_EMAIL: noreply@dailystockanalysis.com
    FROM_NAME: Daily Stock Analysis
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """Email sending service"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.provider = self.config.get('EMAIL_PROVIDER', 'smtp')
        self.from_email = self.config.get('FROM_EMAIL', 'noreply@dailystockanalysis.com')
        self.from_name = self.config.get('FROM_NAME', 'Daily Stock Analysis')
        self._smtp_connection = None
        
        logger.info(f"EmailService initialized (provider: {self.provider})")
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an email.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body (optional)
            
        Returns:
            Result dict with success status
        """
        try:
            if self.provider == 'smtp':
                return self._send_via_smtp(to_email, subject, html_content, text_content)
            elif self.provider == 'sendgrid':
                return self._send_via_sendgrid(to_email, subject, html_content, text_content)
            elif self.provider == 'ses':
                return self._send_via_ses(to_email, subject, html_content, text_content)
            else:
                # Test mode - just log
                logger.info(f"[TEST EMAIL] To: {to_email}, Subject: {subject}")
                return {'success': True, 'message': 'Test mode - email logged'}
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_via_smtp(self, to_email: str, subject: str, 
                       html_content: str, text_content: Optional[str]) -> Dict[str, Any]:
        """Send via SMTP"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = to_email
        
        # Add text version
        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        
        # Add HTML version
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send
        smtp_host = self.config.get('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = self.config.get('SMTP_PORT', 587)
        smtp_user = self.config.get('SMTP_USER')
        smtp_pass = self.config.get('SMTP_PASS')
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(self.from_email, to_email, msg.as_string())
        
        logger.info(f"Email sent to {to_email}: {subject}")
        
        return {
            'success': True,
            'message': 'Email sent successfully',
            'sent_at': datetime.now().isoformat(),
        }
    
    def _send_via_sendgrid(self, to_email: str, subject: str,
                           html_content: str, text_content: Optional[str]) -> Dict[str, Any]:
        """Send via SendGrid"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=self.config.get('SENDGRID_API_KEY'))
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
            )
            
            response = sg.send(message)
            
            return {
                'success': response.status_code == 202,
                'message': 'Email sent via SendGrid',
                'status_code': response.status_code,
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_via_ses(self, to_email: str, subject: str,
                      html_content: str, text_content: Optional[str]) -> Dict[str, Any]:
        """Send via AWS SES"""
        try:
            import boto3
            
            client = boto3.client(
                'ses',
                region_name=self.config.get('AWS_REGION', 'us-east-1'),
                aws_access_key_id=self.config.get('AWS_ACCESS_KEY'),
                aws_secret_access_key=self.config.get('AWS_SECRET_KEY'),
            )
            
            response = client.send_email(
                Source=f"{self.from_name} <{self.from_email}>",
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Html': {'Data': html_content},
                        'Text': {'Data': text_content or ''},
                    }
                }
            )
            
            return {
                'success': True,
                'message': 'Email sent via SES',
                'message_id': response['MessageId'],
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Convenience methods for common emails
    
    def send_welcome(self, to_email: str, user_name: str, api_key: str) -> Dict[str, Any]:
        """Send welcome email"""
        from .templates import EmailTemplates
        
        subject = "Welcome to Daily Stock Analysis! 🎉"
        html = EmailTemplates.welcome(user_name, api_key)
        text = EmailTemplates.welcome_text(user_name, api_key)
        
        return self.send_email(to_email, subject, html, text)
    
    def send_payment_confirmation(self, to_email: str, plan: str, amount: float, 
                                  transaction_id: str) -> Dict[str, Any]:
        """Send payment confirmation"""
        from .templates import EmailTemplates
        
        subject = f"Payment Confirmation - {plan.capitalize()} Plan"
        html = EmailTemplates.payment_confirmation(plan, amount, transaction_id)
        text = EmailTemplates.payment_confirmation_text(plan, amount, transaction_id)
        
        return self.send_email(to_email, subject, html, text)
    
    def send_password_reset(self, to_email: str, reset_link: str, 
                           expires_in: int = 3600) -> Dict[str, Any]:
        """Send password reset email"""
        from .templates import EmailTemplates
        
        subject = "Reset Your Password"
        html = EmailTemplates.password_reset(reset_link, expires_in)
        text = EmailTemplates.password_reset_text(reset_link, expires_in)
        
        return self.send_email(to_email, subject, html, text)
    
    def send_subscription_reminder(self, to_email: str, plan: str, 
                                   days_until_renewal: int) -> Dict[str, Any]:
        """Send subscription renewal reminder"""
        from .templates import EmailTemplates
        
        subject = f"Your {plan.capitalize()} Plan Renews in {days_until_renewal} Days"
        html = EmailTemplates.subscription_reminder(plan, days_until_renewal)
        text = EmailTemplates.subscription_reminder_text(plan, days_until_renewal)
        
        return self.send_email(to_email, subject, html, text)
    
    def send_api_limit_warning(self, to_email: str, plan: str, 
                               usage_percent: float) -> Dict[str, Any]:
        """Send API usage warning"""
        from .templates import EmailTemplates
        
        subject = f"API Usage Alert - {usage_percent:.0f}% Used"
        html = EmailTemplates.api_limit_warning(plan, usage_percent)
        text = EmailTemplates.api_limit_warning_text(plan, usage_percent)
        
        return self.send_email(to_email, subject, html, text)
    
    def send_trial_expiring(self, to_email: str, days_left: int,
                           plan: str) -> Dict[str, Any]:
        """Send trial expiring soon notification"""
        from .templates import EmailTemplates
        
        subject = f"Your Pro Trial Ends in {days_left} Days!"
        html = EmailTemplates.trial_expiring(days_left, plan)
        text = EmailTemplates.trial_expiring_text(days_left, plan)
        
        return self.send_email(to_email, subject, html, text)
