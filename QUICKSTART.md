# Quick Start Guide - Campus Job Board

## 🚀 Getting Started

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 3: Create a Superuser (Admin Account)
```bash
python manage.py createsuperuser
```
Follow the prompts to create an admin account.

### Step 4: Run the Development Server
```bash
python manage.py runserver
```

### Step 5: Access the Application
- **Main Application**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## 📝 Creating Test Accounts

### Test as a Student:
1. Go to http://127.0.0.1:8000/users/register/
2. Enter username, email, password
3. **DO NOT** check "I am a company"
4. Click Register
5. You can now browse and apply for jobs

### Test as a Company:
1. Go to http://127.0.0.1:8000/users/register/
2. Enter username, email, password
3. **CHECK** "I am a company"
4. Click Register
5. You can now post jobs and manage applications

## 🎯 Key Features Implemented

✅ Custom User Model with `is_company` flag  
✅ JobPost model with categories and job types  
✅ Application model with status tracking  
✅ Class-based view: `JobListView` for listing jobs  
✅ Function-based views: `apply_job()`, `create_job_post()`, `my_applications()`  
✅ Bootstrap templates with responsive design  
✅ Search and filtering functionality  
✅ Admin panel customizations  
✅ Authentication system (register, login, logout)  
✅ Role-based access control  

## 📁 Project Structure

```
jobboard/
├── manage.py
├── requirements.txt
├── README.md
├── jobboard/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── jobs/
│   ├── models.py       # JobPost, Application
│   ├── views.py        # Class-based & function-based views
│   ├── forms.py        # JobPostForm, ApplicationForm
│   ├── urls.py
│   ├── admin.py        # Custom admin
│   └── templates/jobs/ # Job templates
├── users/
│   ├── models.py       # CustomUser
│   ├── views.py        # Auth views
│   ├── forms.py        # RegistrationForm, LoginForm
│   ├── urls.py
│   └── templates/users/ # Auth templates
└── templates/
    └── base.html       # Base template
```

## 🎨 Features to Try

1. **Browse Jobs**: View all available job postings
2. **Search & Filter**: Use the search bar and filters to find jobs
3. **Apply for Jobs**: Submit applications as a student
4. **Post Jobs**: Create job listings as a company
5. **Track Applications**: Monitor application status
6. **Admin Panel**: Manage everything via `/admin/`

Enjoy your Campus Job Board! 🎓

