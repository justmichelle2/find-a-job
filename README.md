# Campus Job Board and Internship Finder

A Django-based job board web application that helps students find internships and job opportunities posted by verified companies.

## Features

- **User Roles**:
  - **Students (Job Seekers)**: Browse jobs, apply for positions, track applications
  - **Companies (Employers)**: Post jobs, manage applications
  - **Admin**: Manage users, job posts, and applications via Django admin panel

- **Job Features**:
  - Browse and search for job listings
  - Filter by category and job type
  - Detailed job descriptions
  - Application tracking
  - Application deadline management

- **Authentication**:
  - User registration with role selection
  - Secure login/logout
  - Role-based access control

## Installation

1. **Clone or download this project**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

7. **Access the application**:
   - Open your browser and go to: `http://127.0.0.1:8000/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

## Project Structure

```
jobboard/
├── jobboard/
│   ├── settings.py       # Project settings
│   ├── urls.py          # Main URL configuration
│   └── ...
├── jobs/
│   ├── models.py        # JobPost and Application models
│   ├── views.py         # Class-based and function-based views
│   ├── forms.py         # Job application forms
│   ├── urls.py          # Jobs app URLs
│   └── templates/       # Job-related templates
├── users/
│   ├── models.py        # CustomUser model
│   ├── views.py         # Authentication views
│   ├── forms.py         # Registration and login forms
│   ├── urls.py          # Users app URLs
│   └── templates/       # Authentication templates
├── templates/
│   └── base.html        # Base template with Bootstrap
└── manage.py
```

## Usage

### For Students:
1. Register as a student (do NOT check the "I am a company" checkbox)
2. Browse available job listings
3. Use search and filters to find opportunities
4. Click on a job to view details
5. Submit your application with a cover letter
6. Track your applications in "My Applications"

### For Companies:
1. Register as a company (check the "I am a company" checkbox)
2. Log in to your company account
3. Go to "Post Job" to create a new job posting
4. Fill in job details (title, description, requirements, location, etc.)
5. Manage applications in "My Jobs"
6. View applications received for each posted job

### For Admins:
1. Log in via `/admin/`
2. Manage users, job posts, and applications
3. Use filters and search to find specific records
4. Bulk actions available for applications (accept/reject)

## Models

- **CustomUser**: Extended Django user with `is_company` field
- **JobPost**: Job listings with title, description, requirements, location, category, type, deadline, etc.
- **Application**: Job applications linking applicants to jobs with cover letter and status

## Tech Stack

- **Django 5.x**: Web framework
- **SQLite**: Database (default)
- **Bootstrap 5**: Frontend CSS framework
- **Bootstrap Icons**: Icon library

## Development

### Running Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating a Superuser
```bash
python manage.py createsuperuser
```

### Collecting Static Files (Production)
```bash
python manage.py collectstatic
```

## License

This project is for educational purposes.

## Author

Built with Django and Bootstrap.

