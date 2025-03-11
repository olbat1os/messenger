from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Chat(models.Model):
    name = models.CharField(max_length=100)
    participants = models.ManyToManyField(User, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    is_group_chat = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.sender.username}: {self.content[:50]}'

class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Мужской'),
        ('F', 'Женский'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    friends = models.ManyToManyField('self', blank=True, symmetrical=True)
    friend_requests = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='friend_requests_sent')
    
    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/chat/images/default-avatar.png'

    def has_friend_request_from(self, user):
        """Проверяет, есть ли входящая заявка в друзья от указанного пользователя"""
        return self.friend_requests.filter(id=user.profile.id).exists()

    def has_sent_friend_request_to(self, user):
        """Проверяет, отправлена ли заявка в друзья указанному пользователю"""
        return self.friend_requests_sent.filter(id=user.profile.id).exists()

    def get_friend_requests(self):
        """Получает все входящие заявки в друзья"""
        return self.friend_requests.all()

    def get_friend_requests_sent(self):
        """Получает все исходящие заявки в друзья"""
        return self.friend_requests_sent.all()

    class Meta:
        db_table = 'chat_userprofile'

class MessageDelete(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    deleted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')

# Удалим или закомментируем старый сигнал, если он есть
"""
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
""" 