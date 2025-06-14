import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

class EmailManager:
    def __init__(self):
        self.sender_email = os.getenv('EMAIL_USER')
        self.sender_password = os.getenv('EMAIL_PASS')
        self.smtp_server = os.getenv('EMAIL_HOST')
        self.smtp_port = int(os.getenv('EMAIL_PORT', 587)) # Default to 587 for TLS

        if not all([self.sender_email, self.sender_password, self.smtp_server]):
            print("[EmailManager] WARNING: Email credentials not fully configured. Email sending will be skipped.")

    def send_appointment_confirmation_email(self, recipient_email, parent_name, student_name, teacher_name, date_time, purpose):
        if not self.sender_email or not self.sender_password or not self.smtp_server:
            print("[EmailManager] Skipping email sending due to missing credentials.")
            return False

        subject = f"Appointment Confirmation: {parent_name} with {teacher_name}"
        body = f"""
        Dear {parent_name},

        This email confirms your appointment with {teacher_name} for {student_name}.

        **Details:**
        - Date and Time: {date_time}
        - Purpose: {purpose if purpose else 'General Inquiry'}

        We look forward to seeing you then.

        Sincerely,
        Delhi Public School Reception
        """

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls() # Enable TLS encryption
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            print(f"[EmailManager] Confirmation email sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"[EmailManager] Failed to send email to {recipient_email}: {e}")
            return False 