from django.core.management.base import BaseCommand
from chat.models import Chat
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Creates a test chat with ID 1'

    def handle(self, *args, **kwargs):
        # Получаем или создаем пользователя
        user1, created = User.objects.get_or_create(
            username='user1',
            defaults={'email': 'user1@example.com'}
        )
        if created:
            user1.set_password('testpass123')
            user1.save()
            self.stdout.write(f"Created user: {user1.username}")
        
        # Создаем чат с ID 1 или получаем существующий
        chat, created = Chat.objects.get_or_create(
            id=1,
            defaults={
                'name': 'Test Chat',
                'is_group_chat': False
            }
        )
        
        # Добавляем пользователя в чат
        chat.participants.add(user1)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully {"created" if created else "updated"} chat with ID 1\n'
                f'Participants: {", ".join([u.username for u in chat.participants.all()])}'
            )
        ) 