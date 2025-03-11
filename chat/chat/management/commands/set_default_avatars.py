from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files import File
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Set default avatars for users without avatars'

    def handle(self, *args, **kwargs):
        default_avatar_path = os.path.join(settings.STATIC_ROOT, 'images', 'default-avatar.png')
        
        if not os.path.exists(default_avatar_path):
            self.stdout.write(self.style.ERROR('Default avatar file not found'))
            return
            
        for user in User.objects.all():
            if not user.profile.avatar:
                with open(default_avatar_path, 'rb') as f:
                    user.profile.avatar.save('default-avatar.png', File(f), save=True)
                self.stdout.write(self.style.SUCCESS(f'Set default avatar for {user.username}')) 