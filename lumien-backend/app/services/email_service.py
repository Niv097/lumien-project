import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    """SMTP Email notification service"""
    
    def __init__(self):
        self.smtp_host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.smtp_user = os.getenv("EMAIL_SMTP_USER", "")
        self.smtp_password = os.getenv("EMAIL_SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.enabled = bool(self.smtp_user and self.smtp_password)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """Send HTML email via SMTP"""
        if not self.enabled:
            print("Email service not configured - skipping email send")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email
            
            # Plain text version
            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            
            # HTML version
            msg.attach(MIMEText(html_body, "html"))
            
            # Send via SMTP with TLS
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            print(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    def send_bulk_email(
        self,
        to_emails: List[str],
        subject: str,
        html_body: str
    ) -> List[str]:
        """Send email to multiple recipients"""
        failed = []
        for email in to_emails:
            if not self.send_email(email, subject, html_body):
                failed.append(email)
        return failed

# Global email service instance
email_service = EmailService()
