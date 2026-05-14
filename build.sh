#!/usr/bin/env bash
# Render build script for DjangoChat

set -o errexit  # exit on error

pip install -r requirements.txt

python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate --no-input

# Auto-create superuser (Hardcoded details)
# IMPORTANT: Remove this after the first successful deploy for security!
export DJANGO_SUPERUSER_USERNAME="Light"
export DJANGO_SUPERUSER_PASSWORD="admin99"

# Create superuser using Python to bypass the email requirement
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email='', password=password)
    print('Superuser created successfully.')
else:
    u = User.objects.get(username=username)
    u.set_password(password)
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print('Superuser already existed, password updated to admin99.')
"
