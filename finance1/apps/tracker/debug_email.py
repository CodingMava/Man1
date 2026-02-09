import os
import django
from django.conf import settings

# Setup Django environment
# Load .env file manually if it exists (copying logic from manage.py)
import os
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, val = line.strip().split('=', 1)
                os.environ.setdefault(key, val)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
django.setup()

from django.core.mail import send_mail

def test_email():
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not Set')}")
    print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not Set')}")
    print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not Set')}")
    
    recipient = input("Enter recipient email (or press Enter to skip send test): ").strip()
    if not recipient:
        print("Skipping send test.")
        return

    try:
        print(f"Attempting to send email to {recipient}...")
        send_mail(
            subject='Test Email from Finance App',
            message='This is a test email to verify your configuration.',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'test@example.com'),
            recipient_list=[recipient],
            fail_silently=False,
        )
        print("SUCCESS: Email sent successfully!")
    except Exception as e:
        print(f"FAILURE: Could not send email. Error: {e}")

if __name__ == '__main__':
    test_email()
