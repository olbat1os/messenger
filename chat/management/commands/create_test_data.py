from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chat.models import Chat, Message, UserProfile

class Command(BaseCommand):
    help = 'Creates test data for the chat application'

    def handle(self, *args, **kwargs):
        # Создаем тестовых пользователей
        users_data = [
            {'username': 'user1', 'password': 'testpass123', 'email': 'user1@example.com'},
            {'username': 'user2', 'password': 'testpass123', 'email': 'user2@example.com'},
            {'username': 'user3', 'password': 'testpass123', 'email': 'user3@example.com'},
        ]

        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                email=user_data['email']
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                UserProfile.objects.create(user=user)
            users.append(user)

        # Создаем тестовые чаты
        chat1 = Chat.objects.create(
            name='Личный чат',
            is_group_chat=False
        )
        chat1.participants.add(users[0], users[1])

        chat2 = Chat.objects.create(
            name='Групповой чат',
            is_group_chat=True
        )
        chat2.participants.add(*users)

        # Создаем тестовые сообщения
        Message.objects.create(
            chat=chat1,
            sender=users[0],
            content='Привет, как дела?'
        )
        Message.objects.create(
            chat=chat1,
            sender=users[1],
            content='Привет! Все хорошо, спасибо!'
        )
        Message.objects.create(
            chat=chat2,
            sender=users[0],
            content='Всем привет в групповом чате!'
        )

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы')) 