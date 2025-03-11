from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Chat
import os
from django.core.files import File
from django.conf import settings

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    try:
        profile = instance.profile
        if not created:
            profile.first_name = instance.first_name
            profile.last_name = instance.last_name
            profile.save()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=instance,
            first_name=instance.first_name,
            last_name=instance.last_name
        )
        
        # Установка дефолтной аватарки
        default_avatar_path = os.path.join(settings.STATIC_ROOT, 'images', 'default-avatar.png')
        if os.path.exists(default_avatar_path):
            with open(default_avatar_path, 'rb') as f:
                profile.avatar.save('default-avatar.png', File(f), save=True) 