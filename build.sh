#!/usr/bin/env bash
# Render build script for DjangoChat

set -o errexit  # exit on error

pip install -r requirements.txt

python manage.py collectstatic --no-input

# Run migrations - don't fail the build if DB is temporarily unavailable
python manage.py migrate --no-input || echo "WARNING: Migration failed. Database may be unavailable."
