import os
import django
from django.core.management import call_command

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger_project.settings')
    django.setup()
    call_command('runserver', '0.0.0.0:8000') 