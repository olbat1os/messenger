from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from django.contrib import messages
from .models import Chat, Message, UserProfile, MessageDelete
from .serializers import ChatSerializer, MessageSerializer, UserSerializer
from django.contrib.auth.models import User
from django.db.models import Q
from .forms import SignUpForm
from django.db.transaction import atomic
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from rest_framework.exceptions import PermissionDenied

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(
            Q(participants=self.request.user) | Q(name='World')
        ).distinct()

    def perform_create(self, serializer):
        chat = serializer.save()
        chat.participants.add(self.request.user)
        
        # Добавляем других участников для группового чата
        participant_ids = self.request.data.get('participant_ids', [])
        for user_id in participant_ids:
            user = get_object_or_404(User, id=user_id)
            chat.participants.add(user)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        chat = self.get_object()
        user_id = request.data.get('user_id')
        if user_id:
            user = get_object_or_404(User, id=user_id)
            chat.participants.add(user)
            return Response({'status': 'participant added'})
        return Response({'error': 'user_id required'}, status=400)

    @action(detail=False, methods=['get'])
    def world(self, request):
        chat, created = Chat.objects.get_or_create(
            name='World',
            defaults={'is_group_chat': True}
        )
        if request.user not in chat.participants.all():
            chat.participants.add(request.user)
        serializer = self.get_serializer(chat)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        chat = self.get_object()
        messages = Message.objects.filter(chat=chat).order_by('-timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs.get('chat_pk')
        return Message.objects.filter(chat_id=chat_id).order_by('-timestamp')

    def perform_create(self, serializer):
        chat_id = self.kwargs.get('chat_pk')
        chat = get_object_or_404(Chat, id=chat_id)
        if request.user not in chat.participants.all() and chat.name != 'World':
            raise PermissionDenied("You are not a participant of this chat")
        serializer.save(sender=self.request.user, chat=chat)

    @action(detail=False, methods=['get'])
    def history(self, request, chat_pk=None):
        chat = get_object_or_404(Chat, id=chat_pk)
        if request.user not in chat.participants.all() and chat.name != 'World':
            raise PermissionDenied("You are not a participant of this chat")
        messages = self.get_queryset()
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_profile(self, request, pk=None):
        if str(request.user.id) != pk:
            return Response({'error': 'Not allowed'}, status=403)
        
        user = request.user
        profile = user.profile
        
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
            profile.save()
        
        return Response(UserSerializer(user).data)

def chat_test_page(request):
    return render(request, 'chat/test_websocket.html')

@login_required
def home(request):
    return redirect('messages')

@login_required
def profile(request):
    return render(request, 'chat/profile.html', {
        'profile': request.user.profile
    })

@login_required
def profile_edit(request):
    if request.method == 'POST':
        try:
            profile = request.user.profile
            
            # Обновляем основные поля
            profile.first_name = request.POST.get('first_name', '')
            profile.last_name = request.POST.get('last_name', '')
            profile.bio = request.POST.get('bio', '')
            profile.gender = request.POST.get('gender', '')
            
            # Обработка даты рождения
            birth_date = request.POST.get('birth_date')
            if birth_date:
                from datetime import datetime
                try:
                    profile.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'Неверный формат даты')
                    return redirect('profile_edit')
            
            # Обработка аватара
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
            
            # Сохраняем изменения
            profile.save()
            
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('profile')
            
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении профиля: {str(e)}')
            return redirect('profile_edit')
    
    return render(request, 'chat/profile_edit.html', {
        'profile': request.user.profile
    })

@login_required
def messages_list(request):
    # Получаем все чаты пользователя, включая World чат
    chats = Chat.objects.filter(
        Q(participants=request.user) | Q(name='World')
    ).prefetch_related('messages').distinct()

    # Получаем последние сообщения для каждого чата
    chats_with_last_message = []
    for chat in chats:
        last_message = chat.messages.order_by('-timestamp').first()
        chats_with_last_message.append({
            'chat': chat,
            'last_message': last_message,
            'unread_count': chat.messages.filter(
                timestamp__gt=request.user.last_login
            ).count() if request.user.last_login else 0
        })

    return render(request, 'chat/messages_list.html', {
        'chats': chats_with_last_message
    })

@login_required
def world_chat(request):
    # Получаем или создаем World чат
    chat, created = Chat.objects.get_or_create(
        name='World',
        defaults={
            'is_group_chat': True
        }
    )
    
    # Добавляем текущего пользователя в участники, если его там нет
    if request.user not in chat.participants.all():
        chat.participants.add(request.user)
    
    return render(request, 'chat/chat.html', {
        'chat': chat,
        'is_world_chat': True
    })

@login_required
def create_chat(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        participant_ids = request.POST.getlist('participants')
        
        # Проверяем, что все участники являются друзьями
        friends_ids = request.user.profile.friends.values_list('user_id', flat=True)
        if not all(int(pid) in friends_ids for pid in participant_ids):
            messages.error(request, 'Можно добавлять только друзей')
            return redirect('create_chat')
        
        chat = Chat.objects.create(
            name=name,
            is_group_chat=len(participant_ids) > 1
        )
        chat.participants.add(request.user)
        
        for user_id in participant_ids:
            chat.participants.add(user_id)
        
        return redirect('messages')
    
    # Получаем список друзей для выбора участников
    friends = request.user.profile.friends.all()
    return render(request, 'chat/create_chat.html', {
        'friends': friends
    })

@login_required
def friends_list(request):
    friends = request.user.profile.friends.all()
    return render(request, 'chat/friends_list.html', {
        'friends': friends
    })

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(profile__first_name__icontains=query) |
            Q(profile__last_name__icontains=query)
        ).exclude(id=request.user.id)
    else:
        users = []
    
    return render(request, 'chat/search_users.html', {
        'users': users,
        'query': query
    })

@login_required
@csrf_protect
def add_friend(request, user_id):
    if request.method == 'POST':
        friend = get_object_or_404(User, id=user_id)
        
        # Добавим отладочные сообщения
        print(f"Adding friend request from {request.user.username} to {friend.username}")
        
        try:
            # Проверяем, не являются ли пользователи уже друзьями
            if friend.profile in request.user.profile.friends.all():
                messages.info(request, f'Вы уже являетесь друзьями с {friend.username}')
                return redirect('view_profile', user_id=user_id)
            
            # Проверяем, нет ли уже входящей заявки от этого пользователя
            if request.user.profile.has_friend_request_from(friend):
                messages.info(request, f'У вас есть входящая заявка от {friend.username}')
                return redirect('view_profile', user_id=user_id)
            
            # Проверяем, не отправили ли мы уже заявку
            if request.user.profile.has_sent_friend_request_to(friend):
                messages.info(request, f'Вы уже отправили заявку пользователю {friend.username}')
                return redirect('view_profile', user_id=user_id)
            
            # Отправляем заявку в друзья
            friend.profile.friend_requests.add(request.user.profile)
            messages.success(request, f'Заявка в друзья отправлена пользователю {friend.username}')
            
            # Добавим отладочное сообщение
            print(f"Friend request sent successfully")
            
        except Exception as e:
            print(f"Error sending friend request: {str(e)}")
            messages.error(request, f'Ошибка при отправке заявки: {str(e)}')
        
        return redirect('view_profile', user_id=user_id)
    return redirect('search_users')

@login_required
def accept_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    
    # Проверяем наличие заявки
    if friend.profile in request.user.profile.friend_requests.all():
        # Удаляем заявку
        request.user.profile.friend_requests.remove(friend.profile)
        
        # Добавляем друг друга в друзья
        request.user.profile.friends.add(friend.profile)
        friend.profile.friends.add(request.user.profile)
        
        messages.success(request, f'{friend.username} добавлен в друзья')
    else:
        messages.error(request, 'Заявка в друзья не найдена')
        
    return redirect('friends')

@login_required
def reject_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    request.user.profile.friend_requests.remove(friend.profile)
    messages.success(request, f'Заявка в друзья от {friend.username} отклонена')
    return redirect('friends')

@login_required
@csrf_protect
def remove_friend(request, user_id):
    if request.method == 'POST':
        friend = get_object_or_404(User, id=user_id)
        request.user.profile.friends.remove(friend.profile)
        friend.profile.friends.remove(request.user.profile)
        messages.success(request, f'{friend.username} удален из друзей')
        return redirect('view_profile', user_id=user_id)
    return redirect('friends')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    
    # Получаем список друзей, которых можно пригласить
    if chat.is_group_chat:
        available_friends = request.user.profile.friends.exclude(
            user__in=chat.participants.all()
        )
    else:
        available_friends = []
    
    return render(request, 'chat/chat.html', {
        'chat': chat,
        'available_friends': available_friends
    })

def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                with atomic():
                    # Создаем пользователя
                    user = form.save()
                    
                    # Проверяем, существует ли уже профиль
                    profile, created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'first_name': form.cleaned_data.get('first_name', ''),
                            'last_name': form.cleaned_data.get('last_name', '')
                        }
                    )
                    
                    # Автоматически входим в систему
                    login(request, user)
                    messages.success(request, 'Регистрация успешна!')
                    return redirect('home')
            except Exception as e:
                # Если произошла ошибка, удаляем пользователя
                if 'user' in locals():
                    user.delete()
                messages.error(request, f'Ошибка при регистрации: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Ошибка в поле {field}: {error}')
    else:
        form = SignUpForm()
    
    return render(request, 'chat/register.html', {
        'form': form
    })

@login_required
def create_private_chat(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    
    # Проверяем, существует ли уже чат между пользователями
    existing_chat = Chat.objects.filter(
        is_group_chat=False,
        participants=request.user
    ).filter(
        participants=friend
    ).first()
    
    if existing_chat:
        return redirect('chat-detail', chat_id=existing_chat.id)
    
    # Создаем новый чат
    chat = Chat.objects.create(
        name=f"Чат с {friend.get_full_name() or friend.username}",
        is_group_chat=False
    )
    chat.participants.add(request.user, friend)
    
    return redirect('chat-detail', chat_id=chat.id)

@login_required
def leave_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if chat.name == 'World':
        messages.error(request, 'Нельзя покинуть общий чат')
        return redirect('chat-detail', chat_id=chat_id)
    
    if request.user in chat.participants.all():
        chat.participants.remove(request.user)
        messages.success(request, 'Вы покинули чат')
    return redirect('messages')

@login_required
def delete_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if chat.name == 'World':
        messages.error(request, 'Нельзя удалить общий чат')
        return redirect('chat-detail', chat_id=chat_id)
    
    if request.user in chat.participants.all():
        chat.participants.remove(request.user)
        messages.success(request, 'Чат удален')
    return redirect('messages')

@login_required
def invite_to_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    
    # Проверяем, можно ли приглашать в этот чат
    if chat.name == 'World':
        messages.error(request, 'Нельзя приглашать в общий чат')
        return redirect('chat-detail', chat_id=chat_id)
    
    if not chat.is_group_chat or chat.participants.count() <= 2:
        messages.error(request, 'В этот чат нельзя приглашать участников')
        return redirect('chat-detail', chat_id=chat_id)
    
    if request.method == 'POST':
        friend_ids = request.POST.getlist('friends')
        for friend_id in friend_ids:
            friend = get_object_or_404(User, id=friend_id)
            if friend not in chat.participants.all():
                chat.participants.add(friend)
        messages.success(request, 'Участники добавлены в чат')
    
    return redirect('chat-detail', chat_id=chat_id)

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    MessageDelete.objects.get_or_create(message=message, user=request.user)
    return JsonResponse({'status': 'success'})

@login_required
def view_profile(request, user_id):
    viewed_user = get_object_or_404(User, id=user_id)
    
    # Добавим отладочные сообщения
    has_friend_request = request.user.profile.has_friend_request_from(viewed_user)
    has_sent_request = request.user.profile.has_sent_friend_request_to(viewed_user)
    
    if has_friend_request:
        messages.info(request, 'У вас есть входящая заявка от этого пользователя')
    if has_sent_request:
        messages.info(request, 'Вы отправили заявку этому пользователю')
    
    context = {
        'viewed_user': viewed_user,
        'is_friend': request.user.profile.friends.filter(user=viewed_user).exists(),
        'friend_request_sent': has_sent_request,
        'friend_request_received': has_friend_request,
        'mutual_friends': request.user.profile.friends.filter(friends__user=viewed_user).count()
    }
    
    return render(request, 'chat/view_profile.html', context) 