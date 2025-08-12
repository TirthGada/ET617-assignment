import os
import sys
from pathlib import Path

# Add the project directory to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set environment variables for Vercel
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_platform.settings')
os.environ.setdefault('DEBUG', 'False')

# Import Django and initialize
import django
django.setup()

# Import our initialization helper
from vercel_init import get_initialized_application

# Get the WSGI application with database initialization
application = get_initialized_application()

# This is the entry point for Vercel
app = application
