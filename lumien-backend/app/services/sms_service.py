import requests
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class SMSService:
    """SMS notification service using external SMS gateway"""
    
    def __init__(self):
        # Support multiple SMS providers
        self.provider = os.getenv("SMS_PROVIDER", "twilio")  # twilio, msg91, aws_sns
        
        # Twilio credentials
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_from_number = os.getenv("TWILIO_FROM_NUMBER", "")
        
        # MSG91 credentials (Indian provider)
        self.msg91_auth_key = os.getenv("MSG91_AUTH_KEY", "")
        self.msg91_sender_id = os.getenv("MSG91_SENDER_ID", "LUMIEN")
        
        # AWS SNS
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region = os.getenv("AWS_REGION", "ap-south-1")
        
        self.enabled = bool(
            (self.twilio_account_sid and self.twilio_auth_token) or
            self.msg91_auth_key or
            (self.aws_access_key and self.aws_secret_key)
        )
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS to phone number"""
        if not self.enabled:
            print("SMS service not configured - skipping SMS send")
            return False
        
        # Normalize phone number
        to_number = self._normalize_number(to_number)
        
        try:
            if self.provider == "twilio" and self.twilio_account_sid:
                return self._send_twilio(to_number, message)
            elif self.provider == "msg91" and self.msg91_auth_key:
                return self._send_msg91(to_number, message)
            elif self.provider == "aws_sns" and self.aws_access_key:
                return self._send_aws_sns(to_number, message)
            else:
                print(f"SMS provider {self.provider} not configured")
                return False
                
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")
            return False
    
    def _normalize_number(self, number: str) -> str:
        """Normalize phone number to E.164 format"""
        # Remove spaces, dashes, and + prefix
        number = number.replace(" ", "").replace("-", "").replace("+", "")
        
        # Add country code if missing (assume India +91)
        if len(number) == 10:
            number = "91" + number
        
        return "+" + number
    
    def _send_twilio(self, to_number: str, message: str) -> bool:
        """Send via Twilio"""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
        
        response = requests.post(
            url,
            auth=(self.twilio_account_sid, self.twilio_auth_token),
            data={
                "From": self.twilio_from_number,
                "To": to_number,
                "Body": message
            }
        )
        
        if response.status_code == 201:
            print(f"SMS sent via Twilio to {to_number}")
            return True
        else:
            print(f"Twilio error: {response.text}")
            return False
    
    def _send_msg91(self, to_number: str, message: str) -> bool:
        """Send via MSG91 (India)"""
        url = "https://api.msg91.com/api/v2/sendsms"
        
        payload = {
            "sender": self.msg91_sender_id,
            "route": "4",  # Transactional route
            "country": "91",
            "sms": [{
                "message": message,
                "to": [to_number.replace("+91", "")]
            }]
        }
        
        headers = {
            "authkey": self.msg91_auth_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print(f"SMS sent via MSG91 to {to_number}")
            return True
        else:
            print(f"MSG91 error: {response.text}")
            return False
    
    def _send_aws_sns(self, to_number: str, message: str) -> bool:
        """Send via AWS SNS"""
        import boto3
        
        try:
            client = boto3.client(
                'sns',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            response = client.publish(
                PhoneNumber=to_number,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': 'LUMIEN'
                    }
                }
            )
            
            print(f"SMS sent via AWS SNS to {to_number}")
            return True
            
        except Exception as e:
            print(f"AWS SNS error: {str(e)}")
            return False

# Global SMS service instance
sms_service = SMSService()
