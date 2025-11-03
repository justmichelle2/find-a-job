# Campus Job Board - Replit Setup

## Overview
A Django-based job board web application that connects students with internships and job opportunities. The platform supports two user roles: Students (job seekers) who can browse and apply for positions, and Companies (employers) who can post jobs and manage applications.

## Current State
- **Status**: Fully configured and running on Replit
- **Language**: Python 3.11 with Django 5.2.7
- **Database**: SQLite (development), ready for PostgreSQL in production
- **Web Server**: Django dev server (development), Gunicorn (production)
- **Port**: 5000 (webview)

## Recent Changes
- **2025-11-03**: Major Feature Update
  - Added comprehensive dashboard system (Admin, Company, Student)
  - Expanded job categories (15 categories including IT, Healthcare, Education, etc.)
  - Added multi-currency support for salary (USD, GHS, EUR, GBP, NGN, etc.)
  - Implemented CV and document upload system
  - Added email notification system for applications
  - Implemented job approval workflow for admins
  - Added application status management (Accept/Reject)
  - Enhanced admin portal with statistics
  - Added job editing and deletion functionality
  - Fixed salary input to accept comma-formatted numbers

- **2025-11-03**: Initial Replit setup
  - Installed Python 3.11 and Django 5.2.7
  - Configured Django settings for Replit proxy (ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS)
  - Set up workflow to run dev server on 0.0.0.0:5000
  - Configured deployment with Gunicorn
  - Created .gitignore for Python/Django

## Project Architecture

### Structure
```
jobboard/
├── jobboard/           # Main Django project configuration
│   ├── settings.py     # Project settings (configured for Replit)
│   ├── urls.py         # Main URL routing
│   ├── wsgi.py         # WSGI configuration
│   └── asgi.py         # ASGI configuration
├── jobs/               # Jobs app (core functionality)
│   ├── models.py       # JobPost and Application models
│   ├── views.py        # Class-based and function-based views
│   ├── forms.py        # Job posting and application forms
│   ├── urls.py         # Job-related URL routing
│   ├── admin.py        # Django admin customizations
│   └── templates/      # Job-related templates
├── users/              # User authentication app
│   ├── models.py       # CustomUser model with is_company field
│   ├── views.py        # Registration and login views
│   ├── forms.py        # User registration and login forms
│   └── templates/      # Authentication templates
├── templates/          # Global templates
│   └── base.html       # Base template with Bootstrap 5
├── static/             # Static files (CSS, JS, images)
├── manage.py           # Django management script
└── requirements.txt    # Python dependencies
```

### Key Features
- **User Roles**: Students and Companies with role-based access control
- **Job Management**: Browse, search, filter, and apply for jobs
- **Application Tracking**: Track application status (pending, accepted, rejected)
- **Admin Panel**: Full Django admin interface for managing users, jobs, and applications
- **Bootstrap 5**: Responsive UI with modern design

### Models
- **CustomUser**: Extended Django user model with `is_company` field
- **JobPost**: Job listings with categories, types, deadlines, and requirements
- **Application**: Job applications linking students to jobs with status tracking

## Tech Stack
- **Backend**: Django 5.2.7
- **Database**: SQLite (development)
- **Frontend**: Bootstrap 5, Bootstrap Icons
- **Production Server**: Gunicorn
- **Python**: 3.11

## Replit Configuration

### Workflows
- **Django Dev Server**: Runs on 0.0.0.0:5000 with webview output
  - Command: `python manage.py runserver 0.0.0.0:5000`
  - Hot-reload enabled for development

### Deployment
- **Target**: Autoscale (stateless web app)
- **Command**: Gunicorn WSGI server
- **Port**: 5000

### Django Settings (Replit-specific)
- `ALLOWED_HOSTS = ['*']` - Allows Replit proxy domains
- `CSRF_TRUSTED_ORIGINS` - Configured for Replit domains
- `X_FRAME_OPTIONS = 'SAMEORIGIN'` - Allows iframe embedding

## Getting Started on Replit

### First Time Setup
The application is already configured and running. To set up a new admin account:

1. Open the Shell and run:
   ```bash
   python manage.py createsuperuser
   ```

2. Access the application:
   - Main site: Click the "Webview" tab
   - Admin panel: Navigate to `/admin/`

### Testing the Application

**As a Student:**
1. Click "Register" and create an account (do NOT check "I am a company")
2. Browse available jobs
3. Use search and filters to find opportunities
4. Apply for jobs with a cover letter
5. Track applications in "My Applications"

**As a Company:**
1. Click "Register" and create an account (CHECK "I am a company")
2. Click "Post Job" to create a job listing
3. Fill in job details and requirements
4. View and manage applications in "My Jobs"

**As an Admin:**
1. Go to `/admin/` and log in with superuser credentials
2. Manage users, jobs, and applications
3. Use bulk actions to accept/reject applications

## Development Notes

### Database
- Currently using SQLite for simplicity
- Database file: `db.sqlite3`
- Migrations are already applied
- To reset database: Delete `db.sqlite3` and run `python manage.py migrate`

### Making Changes
- Code changes auto-reload with Django dev server
- After model changes, run: `python manage.py makemigrations && python manage.py migrate`
- Static file changes may require cache refresh

### Common Commands
```bash
# Create superuser
python manage.py createsuperuser

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Access Django shell
python manage.py shell

# Collect static files (for production)
python manage.py collectstatic
```

## Future Enhancements
- Upgrade to PostgreSQL for production
- Add email notifications for application updates
- Implement resume upload functionality
- Add company verification process
- Enhance search with advanced filters
- Add user profile pages

## Support
For Django-specific questions, refer to the [Django Documentation](https://docs.djangoproject.com/).
