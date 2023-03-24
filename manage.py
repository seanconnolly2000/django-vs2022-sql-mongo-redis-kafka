#!/usr/bin/env python
"""
Command-line utility for administrative tasks.

# For more information about this file, visit
# https://docs.djangoproject.com/en/2.1/ref/django-admin/
"""

import os
import sys

if __name__ == '__main__':
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        'django_vs2022_sql_mongo_redis_kafka.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

    # This project uses Visual Studio 2022 Community Edition.
    # If you get an error "Dependency on app with no migration, please follow 
    # readme.html to:
    #       1) create a migration
    #       2) migrate (create database objects) 
    # This will obviously depend upon properly setting up an SQL Server (or database),
    # creating the connection string that works (having a database, and a user/password
    # that can access the database).
