import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project root to path
# Assuming wsgi.py is in the same directory as settings.py and manage.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

application = get_wsgi_application()
