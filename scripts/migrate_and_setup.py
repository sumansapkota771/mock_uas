#!/usr/bin/env python
"""
Complete setup script for the UAS Exam system
Run this script to set up the database and initial data
"""

import os
import sys
import django
import subprocess

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uas_exam.settings')
django.setup()

def run_migrations():
    """Run Django migrations"""
    print("Running database migrations...")
    try:
        subprocess.run([sys.executable, 'manage.py', 'makemigrations'], check=True)
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        print("✓ Migrations completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Migration failed: {e}")
        return False
    return True

def create_superuser():
    """Create superuser if it doesn't exist"""
    from django.contrib.auth.models import User
    
    if not User.objects.filter(is_superuser=True).exists():
        print("\nCreating superuser account...")
        print("Please enter superuser details:")
        
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        
        if username:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password='admin123'  # Default password - should be changed
            )
            print(f"✓ Superuser '{username}' created successfully")
            print("  Default password: admin123 (Please change this after first login)")
        else:
            print("✗ Username cannot be empty")
    else:
        print("✓ Superuser already exists")

def setup_initial_data():
    """Setup initial exam data"""
    print("\nSetting up initial exam data...")
    try:
        # Import and run the initial data creation
        from scripts.create_initial_data import main as create_data
        create_data()
        print("✓ Initial data setup completed")
    except Exception as e:
        print(f"✗ Initial data setup failed: {e}")

def main():
    """Main setup function"""
    print("=== UAS Mock Exam System Setup ===\n")
    
    # Run migrations
    if not run_migrations():
        return
    
    # Create superuser
    create_superuser()
    
    # Setup initial data
    setup_initial_data()
    
    print("\n=== Setup Complete ===")
    print("You can now:")
    print("1. Run the server: python manage.py runserver")
    print("2. Access admin at: http://localhost:8000/admin/")
    print("3. Access the site at: http://localhost:8000/")
    print("\nAdmin credentials:")
    print("- Username: [as entered above]")
    print("- Password: admin123 (change this!)")

if __name__ == '__main__':
    main()
