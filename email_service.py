import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import schedule
import time
import threading
from logger import setup_logger
from config import AppConfig
from dotenv import load_dotenv

logger = setup_logger(__name__)
load_dotenv()

class EmailService:
    def __init__(self):
        self.config = AppConfig()
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.reminder_thread = None
        self.is_running = False
        self.email_enabled = bool(self.smtp_username and self.smtp_password)

    def send_email(self, recipient_email, subject, body):
        if not self.email_enabled:
            logger.warning("Email service is disabled. Configure SMTP credentials to enable email features.")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            logger.info(f"Email sent to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    def send_booking_confirmation(self, appointment):
        if not self.email_enabled:
            logger.warning("Email service is disabled. Skipping booking confirmation email.")
            return False
            
        subject = "Appointment Confirmation"
        body = f"""
        <html>
            <body>
                <h2>Your appointment has been confirmed!</h2>
                <p>Details:</p>
                <ul>
                    <li>Doctor: {appointment['doctor_name']}</li>
                    <li>Date: {appointment['time'].strftime('%B %d, %Y')}</li>
                    <li>Time: {appointment['time'].strftime('%I:%M %p')}</li>
                    <li>Location: {appointment['location']}</li>
                </ul>
                <p>Thank you for choosing our service!</p>
            </body>
        </html>
        """
        return self.send_email(appointment['email'], subject, body)

    def send_cancellation_confirmation(self, appointment):
        if not self.email_enabled:
            logger.warning("Email service is disabled. Skipping cancellation confirmation email.")
            return False
            
        subject = "Appointment Cancellation Confirmation"
        body = f"""
        <html>
            <body>
                <h2>Your appointment has been cancelled</h2>
                <p>Details of cancelled appointment:</p>
                <ul>
                    <li>Doctor: {appointment['doctor_name']}</li>
                    <li>Date: {appointment['time'].strftime('%B %d, %Y')}</li>
                    <li>Time: {appointment['time'].strftime('%I:%M %p')}</li>
                </ul>
                <p>If you would like to schedule a new appointment, please visit our website or contact us.</p>
            </body>
        </html>
        """
        return self.send_email(appointment['email'], subject, body)

    def send_reminder(self, appointment):
        if not self.email_enabled:
            logger.warning("Email service is disabled. Skipping reminder email.")
            return False
            
        subject = "Appointment Reminder"
        body = f"""
        <html>
            <body>
                <h2>Reminder: You have an upcoming appointment</h2>
                <p>Details:</p>
                <ul>
                    <li>Doctor: {appointment['doctor_name']}</li>
                    <li>Date: {appointment['time'].strftime('%B %d, %Y')}</li>
                    <li>Time: {appointment['time'].strftime('%I:%M %p')}</li>
                    <li>Location: {appointment['location']}</li>
                </ul>
                <p>Please arrive 10 minutes before your scheduled time.</p>
            </body>
        </html>
        """
        return self.send_email(appointment['email'], subject, body)

    def check_and_send_reminders(self, appointments):
        if not self.email_enabled:
            return
            
        try:
            now = datetime.now()
            for appointment in appointments:
                appointment_time = appointment['time']
                time_diff = appointment_time - now
                
               
                if timedelta(hours=23) <= time_diff <= timedelta(hours=25):
                    self.send_reminder(appointment)
                    logger.info(f"Sent 24-hour reminder for appointment with {appointment['doctor_name']}")
                
                
                elif timedelta(minutes=55) <= time_diff <= timedelta(minutes=65):
                    self.send_reminder(appointment)
                    logger.info(f"Sent 1-hour reminder for appointment with {appointment['doctor_name']}")
        except Exception as e:
            logger.error(f"Error in reminder job: {str(e)}")

    def start_reminder_service(self, appointments):
        if not self.email_enabled:
            logger.warning("Email service is disabled. Reminder service will not start.")
            return
            
        def reminder_job():
            while self.is_running:
                self.check_and_send_reminders(appointments)
                time.sleep(300) 

        if not self.is_running:
            self.is_running = True
            self.reminder_thread = threading.Thread(target=reminder_job)
            self.reminder_thread.daemon = True
            self.reminder_thread.start()
            logger.info("Reminder service started")

    def stop_reminder_service(self):
        self.is_running = False
        if self.reminder_thread:
            self.reminder_thread.join(timeout=1)
        logger.info("Reminder service stopped")

    def send_appointment_confirmation(self, appointment_data):
       
        try:
            if not all([self.smtp_username, self.smtp_password, self.sender_email]):
                logger.warning("Email configuration incomplete. Skipping email send.")
                return False

            if not appointment_data.get('email'):
                logger.warning("No recipient email provided. Skipping email send.")
                return False

            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = appointment_data['email']
            msg['Subject'] = "Appointment Confirmation - Smart Medical System"

            
            body = f"""
            Dear {appointment_data['name']},

            Your appointment has been confirmed with the following details:

            Doctor: {appointment_data['doctor_name']}
            Date & Time: {appointment_data['time'].strftime('%A, %B %d, %Y at %I:%M %p')}
            Type: {appointment_data['type']}
            Location: {appointment_data.get('location', 'Main Office')}

            Please arrive 15 minutes before your scheduled time.
            If you need to reschedule or cancel, please use our online system or contact us directly.

            Best regards,
            Smart Medical System Team
            """

            msg.attach(MIMEText(body, 'plain'))

            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Confirmation email sent to {appointment_data['email']}")
            return True

        except Exception as e:
            logger.error(f"Failed to send confirmation email: {str(e)}")
            return False

email_service = EmailService() 