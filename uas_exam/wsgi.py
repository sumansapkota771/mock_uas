"""
WSGI config for uas_exam project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uas_exam.settings')

application = get_wsgi_application()
