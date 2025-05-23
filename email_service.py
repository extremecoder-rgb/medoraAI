import os
import emails
from emails.template import JinjaTemplate
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from logger import setup_logger

logger = setup_logger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_options = {
            "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "user": os.getenv("SMTP_USER"),
            "password": os.getenv("SMTP_PASSWORD"),
            "tls": True
        }
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.setup_reminder_job()

    def send_email(self, to_email, subject, template_name, template_data):
        """Send an email using the specified template and data"""
        try:
            template_path = os.path.join("email_templates", f"{template_name}.html")
            with open(template_path, "r") as f:
                template = JinjaTemplate(f.read())

            message = emails.Message(
                subject=subject,
                html=template.render(**template_data),
                mail_from=(os.getenv("EMAIL_FROM_NAME", "Appointment System"), 
                          os.getenv("EMAIL_FROM_ADDRESS", "noreply@example.com"))
            )

            response = message.send(
                to=to_email,
                render=template_data,
                smtp=self.smtp_options
            )
            
            if response.status_code not in [250, 200, 201, 202]:
                logger.error(f"Failed to send email: {response.error}")
                return False
                
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    def send_booking_confirmation(self, appointment):
        """Send booking confirmation email"""
        template_data = {
            "user_name": appointment["name"],
            "doctor_name": appointment.get("doctor_name", "Your Doctor"),
            "appointment_date": appointment["time"].strftime("%B %d, %Y"),
            "appointment_time": appointment["time"].strftime("%I:%M %p"),
            "location": appointment.get("location", "Main Office")
        }
        
        return self.send_email(
            to_email=appointment["email"],
            subject="Appointment Confirmation",
            template_name="booking_confirmation",
            template_data=template_data
        )

    def send_cancellation_confirmation(self, appointment):
        """Send cancellation confirmation email"""
        template_data = {
            "user_name": appointment["name"],
            "doctor_name": appointment.get("doctor_name", "Your Doctor"),
            "appointment_date": appointment["time"].strftime("%B %d, %Y"),
            "appointment_time": appointment["time"].strftime("%I:%M %p"),
            "location": appointment.get("location", "Main Office"),
            "reschedule_url": os.getenv("RESCHEDULE_URL", "https://example.com/reschedule")
        }
        
        return self.send_email(
            to_email=appointment["email"],
            subject="Appointment Cancellation Confirmation",
            template_name="cancellation_confirmation",
            template_data=template_data
        )

    def send_reminder(self, appointment):
        """Send appointment reminder email"""
        template_data = {
            "user_name": appointment["name"],
            "doctor_name": appointment.get("doctor_name", "Your Doctor"),
            "appointment_date": appointment["time"].strftime("%B %d, %Y"),
            "appointment_time": appointment["time"].strftime("%I:%M %p"),
            "location": appointment.get("location", "Main Office"),
            "cancel_url": os.getenv("CANCEL_URL", "https://example.com/cancel")
        }
        
        return self.send_email(
            to_email=appointment["email"],
            subject="Appointment Reminder - 1 Hour Before",
            template_name="appointment_reminder",
            template_data=template_data
        )

    def setup_reminder_job(self):
        """Setup the scheduler job for sending reminders"""
        def check_and_send_reminders():
            try:
                # Get all appointments from the session state
                appointments = st.session_state.get("appointments", [])
                current_time = datetime.now()
                
                for appointment in appointments:
                    # Check if appointment is in 1 hour
                    appointment_time = appointment["time"]
                    time_diff = appointment_time - current_time
                    
                    if timedelta(hours=0, minutes=55) <= time_diff <= timedelta(hours=1, minutes=5):
                        # Send reminder if not already sent
                        if not appointment.get("reminder_sent"):
                            if self.send_reminder(appointment):
                                appointment["reminder_sent"] = True
                                logger.info(f"Reminder sent for appointment: {appointment}")
                                
            except Exception as e:
                logger.error(f"Error in reminder job: {str(e)}")

        # Schedule the job to run every 5 minutes
        self.scheduler.add_job(
            check_and_send_reminders,
            trigger=IntervalTrigger(minutes=5),
            id="reminder_job",
            replace_existing=True
        ) 