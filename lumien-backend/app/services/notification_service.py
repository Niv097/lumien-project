from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.models import models
from app.services.email_service import email_service
from app.services.sms_service import sms_service
from app.services.notification_templates import NotificationTemplates

class NotificationService:
    """Main notification service that handles in-app, email, and SMS notifications"""
    
    def __init__(self, db: Session):
        self.db = db
        self.templates = NotificationTemplates()
    
    def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
        link: Optional[str] = None,
        send_email: bool = False,
        send_sms: bool = False,
        email_data: Optional[Dict[str, Any]] = None,
        sms_data: Optional[Dict[str, Any]] = None
    ) -> models.Notification:
        """Create in-app notification and optionally send email/SMS"""
        
        # Create in-app notification
        notification = models.Notification(
            notification_id=f"NOT-{uuid.uuid4().hex[:8].upper()}",
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            link=link,
            read=False,
            created_at=datetime.utcnow()
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        # Get user preferences
        user = self.db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return notification
        
        prefs = self.db.query(models.NotificationPreference).filter(
            models.NotificationPreference.user_id == user_id
        ).first()
        
        # Default preferences if not set
        email_enabled = prefs.email_notifications if prefs else True
        sms_enabled = prefs.sms_notifications if prefs else False
        
        # Send email if enabled and requested
        if send_email and email_enabled and user.email and email_data:
            html_body = self.templates.get_email_template(email_data.get("template", "new_case"), email_data)
            email_service.send_email(
                to_email=user.email,
                subject=title,
                html_body=html_body
            )
        
        # Send SMS if enabled and requested
        if send_sms and sms_enabled and user.mobile_number and sms_data:
            sms_message = self.templates.get_sms_template(sms_data.get("template", "new_case"), sms_data)
            sms_service.send_sms(user.mobile_number, sms_message)
        
        return notification
    
    def notify_new_case(self, case_data: Dict[str, Any], bank_users: List[models.User]):
        """Notify bank users of new fraud case"""
        for user in bank_users:
            # In-app notification
            self.create_notification(
                user_id=user.id,
                title="New Fraud Case Received",
                message=f"Case {case_data['acknowledgement_no']} for ₹{case_data.get('amount', 0):,.2f} requires action",
                notification_type="warning",
                link=f"/case/{case_data['acknowledgement_no']}",
                send_email=True,
                send_sms=True,
                email_data={
                    "template": "new_case",
                    "case_id": case_data.get('acknowledgement_no'),
                    "acknowledgement_no": case_data.get('acknowledgement_no'),
                    "amount": case_data.get('amount', 0),
                    "sla_deadline": case_data.get('sla_deadline', '23 hours'),
                    "case_link": f"https://lumien.local/case/{case_data['acknowledgement_no']}"
                },
                sms_data={
                    "template": "new_case",
                    "case_id": case_data.get('acknowledgement_no'),
                    "amount": case_data.get('amount', 0),
                    "sla_deadline": case_data.get('sla_deadline', '23h'),
                    "case_link": f"https://lumien.local/case/{case_data['acknowledgement_no']}"
                }
            )
    
    def notify_status_update(self, user_id: int, case_data: Dict[str, Any]):
        """Notify user of successful status update"""
        self.create_notification(
            user_id=user_id,
            title="Status Update Synced",
            message=f"Case {case_data['case_id']} status updated to {case_data['status']}",
            notification_type="success",
            link=f"/case/{case_data['case_id']}",
            send_email=True,
            email_data={
                "template": "status_update",
                "case_id": case_data['case_id'],
                "status": case_data['status'],
                "i4c_response": case_data.get('i4c_response', 'Success'),
                "sync_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "case_link": f"https://lumien.local/case/{case_data['case_id']}"
            },
            sms_data={
                "template": "status_update",
                "case_id": case_data['case_id'],
                "status": case_data['status'],
                "i4c_response": case_data.get('i4c_response', 'Success'),
                "case_link": f"https://lumien.local/case/{case_data['case_id']}"
            }
        )
    
    def notify_hold_success(self, user_id: int, hold_data: Dict[str, Any]):
        """Notify user of successful hold action"""
        self.create_notification(
            user_id=user_id,
            title="Hold Action Successful",
            message=f"₹{hold_data['hold_amount']:,.2f} held in case {hold_data['case_id']}",
            notification_type="success",
            link=f"/case/{hold_data['case_id']}",
            send_email=True,
            email_data={
                "template": "hold_success",
                "case_id": hold_data['case_id'],
                "hold_amount": hold_data['hold_amount'],
                "hold_ref": hold_data.get('hold_reference', 'N/A'),
                "transaction_id": hold_data.get('transaction_id', 'N/A'),
                "case_link": f"https://lumien.local/case/{hold_data['case_id']}"
            },
            sms_data={
                "template": "hold_success",
                "case_id": hold_data['case_id'],
                "hold_amount": hold_data['hold_amount'],
                "hold_ref": hold_data.get('hold_reference', 'N/A')
            }
        )
    
    def notify_sla_warning(self, case_data: Dict[str, Any], bank_users: List[models.User]):
        """Warn users of approaching SLA deadline"""
        for user in bank_users:
            self.create_notification(
                user_id=user.id,
                title="SLA Warning: Case Due Soon",
                message=f"Case {case_data['case_id']} SLA expires in {case_data['time_remaining']}",
                notification_type="error",
                link=f"/case/{case_data['case_id']}",
                send_email=True,
                send_sms=True,
                email_data={
                    "template": "sla_warning",
                    "case_id": case_data['case_id'],
                    "time_remaining": case_data['time_remaining'],
                    "amount": case_data.get('amount', 0),
                    "case_link": f"https://lumien.local/case/{case_data['case_id']}"
                },
                sms_data={
                    "template": "sla_warning",
                    "case_id": case_data['case_id'],
                    "time_remaining": case_data['time_remaining'],
                    "amount": case_data.get('amount', 0),
                    "case_link": f"https://lumien.local/case/{case_data['case_id']}"
                }
            )
    
    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[models.Notification]:
        """Get notifications for user"""
        query = self.db.query(models.Notification).filter(
            models.Notification.user_id == user_id
        )
        
        if unread_only:
            query = query.filter(models.Notification.read == False)
        
        return query.order_by(models.Notification.created_at.desc()).limit(limit).all()
    
    def mark_notification_read(self, notification_id: str, user_id: int) -> bool:
        """Mark notification as read"""
        notification = self.db.query(models.Notification).filter(
            models.Notification.notification_id == notification_id,
            models.Notification.user_id == user_id
        ).first()
        
        if notification:
            notification.read = True
            self.db.commit()
            return True
        return False
    
    def mark_all_read(self, user_id: int) -> int:
        """Mark all notifications as read"""
        result = self.db.query(models.Notification).filter(
            models.Notification.user_id == user_id,
            models.Notification.read == False
        ).update({"read": True})
        
        self.db.commit()
        return result

# Utility function to get notification service
def get_notification_service(db: Session) -> NotificationService:
    return NotificationService(db)
