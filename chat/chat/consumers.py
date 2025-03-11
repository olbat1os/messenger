import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from django.contrib.auth.models import User
import logging
from django.utils import timezone
from .serializers import MessageSerializer

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        logger.info(f"Attempting WebSocket connection for chat {self.chat_id}")
        
        if self.scope["user"].is_anonymous:
            logger.error("Anonymous user tried to connect")
            await self.close()
            return

        try:
            has_access = await self.has_chat_access()
            logger.info(f"Chat access check result: {has_access}")
            
            if not has_access:
                logger.error(f"User {self.scope['user']} has no access to chat {self.chat_id}")
                await self.close()
                return

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            
            # Отправляем историю сообщений после подключения
            await self.send_chat_history()
            
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
            await self.close()

    @database_sync_to_async
    def has_chat_access(self):
        try:
            chat = Chat.objects.get(id=self.chat_id)
            return (chat.name == 'World' or 
                   chat.participants.filter(id=self.scope["user"].id).exists())
        except Chat.DoesNotExist:
            return False

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected with code {close_code}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']
        
        # Сохраняем сообщение в базу данных
        chat = await database_sync_to_async(Chat.objects.get)(id=self.chat_id)
        message = await database_sync_to_async(Message.objects.create)(
            chat=chat,
            sender=self.scope["user"],
            content=message_content
        )
        
        # Преобразуем данные сообщения в словарь
        message_data = {
            'id': message.id,
            'sender': message.sender.username,  # Используем только username
            'content': message.content,
            'timestamp': message.timestamp.isoformat()
        }
        
        # Отправляем сообщение в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )

    async def chat_message(self, event):
        # Отправляем сообщение клиенту без изменений
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    @database_sync_to_async
    def get_chat_history(self):
        chat = Chat.objects.get(id=self.chat_id)
        messages = Message.objects.filter(chat=chat).order_by('timestamp')[:50]
        return [
            {
                'id': msg.id,
                'sender': msg.sender.username,  # Используем только username
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in messages
        ]

    async def send_chat_history(self):
        history = await self.get_chat_history()
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': history
        })) 