def application(environ, start_response):
    import os
    import sys

    # Add the project directory to the Python path
    project_home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_home not in sys.path:
        sys.path.append(project_home)

    # Set the default settings module for the 'django' program
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

    # Return the WSGI application
    return application(environ, start_response)