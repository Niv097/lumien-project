from typing import Dict, Any
from datetime import datetime

# Email HTML Templates
EMAIL_TEMPLATES = {
    "new_case": """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #0284c7;">🚨 New Fraud Case Received</h2>
            <p>A new fraud case requires your immediate attention.</p>
            <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Case ID:</strong> {case_id}</p>
                <p><strong>Acknowledgement No:</strong> {acknowledgement_no}</p>
                <p><strong>Amount:</strong> ₹{amount:,.2f}</p>
                <p><strong>SLA Deadline:</strong> {sla_deadline}</p>
            </div>
            <a href="{case_link}" style="background: #0284c7; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">View Case</a>
            <p style="color: #64748b; font-size: 12px; margin-top: 30px;">
                This is an automated notification from Lumien Intermediary Hub.
            </p>
        </div>
    </body>
    </html>
    """,
    
    "status_update": """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #10b981;">✅ Status Update Synced</h2>
            <p>Your action on the fraud case has been successfully synced with I4C.</p>
            <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Case ID:</strong> {case_id}</p>
                <p><strong>New Status:</strong> {status}</p>
                <p><strong>I4C Response:</strong> {i4c_response}</p>
                <p><strong>Sync Time:</strong> {sync_time}</p>
            </div>
            <a href="{case_link}" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">View Case</a>
        </div>
    </body>
    </html>
    """,
    
    "hold_success": """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #059669;">💰 Hold Action Successful</h2>
            <p>Funds have been successfully held in the fraud case.</p>
            <div style="background: #ecfdf5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Case ID:</strong> {case_id}</p>
                <p><strong>Amount Held:</strong> ₹{hold_amount:,.2f}</p>
                <p><strong>Hold Reference:</strong> {hold_ref}</p>
                <p><strong>Transaction ID:</strong> {transaction_id}</p>
            </div>
            <a href="{case_link}" style="background: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">View Case</a>
        </div>
    </body>
    </html>
    """,
    
    "sla_warning": """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #d97706;">⏰ SLA Warning</h2>
            <p>A fraud case is approaching its SLA deadline and requires immediate action.</p>
            <div style="background: #fffbeb; padding: 15px; border-radius: 8px; border-left: 4px solid #d97706; margin: 20px 0;">
                <p><strong>Case ID:</strong> {case_id}</p>
                <p><strong>Time Remaining:</strong> {time_remaining}</p>
                <p><strong>Amount at Risk:</strong> ₹{amount:,.2f}</p>
            </div>
            <a href="{case_link}" style="background: #d97706; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Take Action Now</a>
        </div>
    </body>
    </html>
    """,
    
    "kyc_submitted": """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #7c3aed;">📄 KYC Pack Submitted</h2>
            <p>Your KYC documentation pack has been submitted to I4C.</p>
            <div style="background: #f5f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Pack ID:</strong> {pack_id}</p>
                <p><strong>Case ID:</strong> {case_id}</p>
                <p><strong>Submitted At:</strong> {submitted_at}</p>
                <p><strong>Acknowledgement:</strong> {ack_ref}</p>
            </div>
        </div>
    </body>
    </html>
    """,
    
    "lea_request": """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #dc2626;">🛡️ LEA Request Received</h2>
            <p>A Law Enforcement Agency has requested information.</p>
            <div style="background: #fef2f2; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Request ID:</strong> {request_id}</p>
                <p><strong>Agency:</strong> {lea_type}</p>
                <p><strong>Due Date:</strong> {due_date}</p>
                <p><strong>Priority:</strong> {priority}</p>
            </div>
            <a href="{request_link}" style="background: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">View Request</a>
        </div>
    </body>
    </html>
    """
}

# SMS Text Templates (short, under 160 chars ideally)
SMS_TEMPLATES = {
    "new_case": "Lumien Alert: New fraud case {case_id} for ₹{amount}. SLA: {sla_deadline}. Action required: {case_link}",
    
    "status_update": "Lumien: Case {case_id} status updated to {status}. I4C sync: {i4c_response}. View: {case_link}",
    
    "hold_success": "Lumien: ₹{hold_amount} held successfully in case {case_id}. Ref: {hold_ref}",
    
    "sla_warning": "URGENT Lumien: Case {case_id} SLA expires in {time_remaining}. Amount: ₹{amount}. Act now: {case_link}",
    
    "kyc_submitted": "Lumien: KYC pack {pack_id} submitted to I4C. Ack: {ack_ref}",
    
    "lea_request": "Lumien Alert: LEA request {request_id} from {lea_type}. Due: {due_date}. Priority: {priority}"
}

class NotificationTemplates:
    """Notification template manager"""
    
    @staticmethod
    def get_email_template(template_name: str, data: Dict[str, Any]) -> str:
        """Get formatted email HTML"""
        template = EMAIL_TEMPLATES.get(template_name, EMAIL_TEMPLATES["new_case"])
        return template.format(**data)
    
    @staticmethod
    def get_sms_template(template_name: str, data: Dict[str, Any]) -> str:
        """Get formatted SMS text"""
        template = SMS_TEMPLATES.get(template_name, SMS_TEMPLATES["new_case"])
        message = template.format(**data)
        
        # Truncate if too long for single SMS
        if len(message) > 160:
            message = message[:157] + "..."
        
        return message
