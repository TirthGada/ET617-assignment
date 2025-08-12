import os
import sys
from pathlib import Path

# Add the project directory to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_platform.settings')

# Import Django and initialize
import django
from django.core.wsgi import get_wsgi_application

# Initialize Django
django.setup()

# Get the WSGI application
application = get_wsgi_application()

# This is the entry point for Vercel
app = application
