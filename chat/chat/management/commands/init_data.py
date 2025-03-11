from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chat.models import Chat, UserProfile

class Command(BaseCommand):
    help = 'Initialize application data'

    def handle(self, *args, **kwargs):
        # Создаем World чат
        world_chat, created = Chat.objects.get_or_create(
            name='World',
            defaults={'is_group_chat': True}
        )
        if created:
            self.stdout.write('Created World chat')

        # Проверяем профили пользователей
        for user in User.objects.all():
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            )
            if created:
                self.stdout.write(f'Created profile for {user.username}')

            # Добавляем пользователя в World чат
            world_chat.participants.add(user)

        self.stdout.write(self.style.SUCCESS('Data initialization completed')) 