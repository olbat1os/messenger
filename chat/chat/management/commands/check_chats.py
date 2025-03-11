from django.core.management.base import BaseCommand
from chat.models import Chat, Message
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Check chats and their participants'

    def handle(self, *args, **kwargs):
        # Проверяем пользователей
        users = User.objects.all()
        self.stdout.write("Users in database:")
        for user in users:
            self.stdout.write(f"- {user.username} (ID: {user.id})")

        # Проверяем чаты
        chats = Chat.objects.all()
        self.stdout.write("\nChats in database:")
        for chat in chats:
            self.stdout.write(f"\nChat: {chat.name} (ID: {chat.id})")
            self.stdout.write("Participants:")
            for participant in chat.participants.all():
                self.stdout.write(f"- {participant.username}") 