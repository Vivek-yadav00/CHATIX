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

python manage.py createsuperuser --no-input || echo "Superuser already exists, skipping."
