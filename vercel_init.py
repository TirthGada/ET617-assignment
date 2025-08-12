"""
Vercel initialization script to set up database and sample data
"""
import os
import django
from django.core.management import execute_from_command_line

# Flag to track if initialization has been done
_initialized = False

def initialize_database():
    """Initialize the database with tables and sample data"""
    global _initialized
    if _initialized:
        return
    
    try:
        # Run migrations to create tables
        from django.core.management import call_command
        call_command('migrate', verbosity=0, interactive=False)
        
        # Create sample data
        try:
            call_command('create_sample_data', verbosity=0)
        except:
            pass  # Sample data creation might fail, continue anyway
        
        _initialized = True
    except Exception as e:
        print(f"Database initialization error: {e}")
        # Continue anyway to allow the app to start
        _initialized = True

def get_initialized_application():
    """Get Django application with database initialized"""
    from django.core.wsgi import get_wsgi_application
    
    # Get the base application
    base_app = get_wsgi_application()
    
    def application(environ, start_response):
        # Initialize database on first request
        initialize_database()
        
        # Call the actual Django application
        return base_app(environ, start_response)
    
    return application
