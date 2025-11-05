from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = "Diagnostics for email/SMS notification configuration. Prints backend, from address, and whether SendGrid/Twilio are configured."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Notification Diagnostics"))

        # Email backend details
        email_backend = getattr(settings, 'EMAIL_BACKEND', 'undefined')
        default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'undefined')
        sendgrid_present = bool(os.environ.get('SENDGRID_API_KEY'))
        email_host = getattr(settings, 'EMAIL_HOST', None)
        email_port = getattr(settings, 'EMAIL_PORT', None)
        email_use_tls = getattr(settings, 'EMAIL_USE_TLS', None)

        self.stdout.write(f"EMAIL_BACKEND: {email_backend}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {default_from}")
        self.stdout.write(f"SendGrid API key present: {sendgrid_present}")
        if email_host:
            self.stdout.write(f"EMAIL_HOST: {email_host}")
        if email_port:
            self.stdout.write(f"EMAIL_PORT: {email_port}")
        if email_use_tls is not None:
            self.stdout.write(f"EMAIL_USE_TLS: {email_use_tls}")

        # Try import and resolve email backend class
        try:
            from django.core.mail import get_connection
            conn = get_connection()
            self.stdout.write(self.style.SUCCESS(f"Resolved email backend connection: {conn.__class__.__name__}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to initialize email backend: {e}"))

        # Twilio details
        tw_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        tw_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        tw_from = getattr(settings, 'TWILIO_FROM_NUMBER', '')
        self.stdout.write(f"TWILIO_ACCOUNT_SID set: {bool(tw_sid)}")
        self.stdout.write(f"TWILIO_FROM_NUMBER: {tw_from if tw_from else 'not set'}")

        # Try Twilio client import/construct (without sending)
        try:
            if tw_sid and tw_token:
                from twilio.rest import Client
                _client = Client(tw_sid, tw_token)
                # Don't perform network calls; construction indicates package available and creds provided
                self.stdout.write(self.style.SUCCESS("Twilio client import and construction OK"))
            else:
                self.stdout.write("Twilio not configured (set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN to enable).")
        except ImportError:
            self.stdout.write(self.style.ERROR("Twilio package not installed. Install with: pip install twilio"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Twilio client construction failed: {e}"))

        self.stdout.write(self.style.MIGRATE_LABEL("Done."))
