# UAS Mock Exam System

A Django-based web application for conducting mock tests for International UAS (University of Applied Sciences) entrance examinations.

## Features

- User authentication and authorization
- Timed mock examinations with 6 sections
- Auto-save functionality
- Admin dashboard for managing questions and results
- Responsive design with minimalistic black/red theme
- Real-time timer and automatic submission

## Exam Sections

1. **Reasoning Skills** (25 minutes)
2. **English Language Skills** (20 minutes)
3. **Mathematical Skills** (25 minutes)
4. **Advanced Mathematical Skills** (30 minutes)
5. **Ethical Skills** (10 minutes)
6. **Emotional Intelligence Skills** (10 minutes)

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Run server: `python manage.py runserver`

## Usage

1. Access the application at `http://localhost:8000`
2. Register or login to access mock exams
3. Admin can access `/admin/` to manage questions and view results
4. Users can take timed mock exams with automatic saving

## Admin Features

- Upload questions with multiple choice options
- Set time duration for each section
- View user exam results and progress
- Manage user accounts

## Technical Details

- Built with Django 4.2.7
- SQLite database (can be configured for PostgreSQL/MySQL)
- Bootstrap 5 for responsive UI
- JavaScript for timer and auto-save functionality
- Session-based authentication
