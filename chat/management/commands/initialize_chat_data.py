from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chat.models import UserProfile, Chat

class Command(BaseCommand):
    help = 'Initialize chat data'

    def handle(self, *args, **kwargs):
        # Создаем профили для всех пользователей
        for user in User.objects.all():
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                self.stdout.write(f'Created profile for user: {user.username}')

        # Создаем World чат
        world_chat, created = Chat.objects.get_or_create(
            name='World',
            defaults={'is_group_chat': True}
        )
        if created:
            self.stdout.write('Created World chat')
            # Добавляем всех пользователей в World чат
            for user in User.objects.all():
                world_chat.participants.add(user)
            self.stdout.write('Added all users to World chat') 