from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views
from .auth import token_auth

router = DefaultRouter()
router.register(r'chats', views.ChatViewSet, basename='chat')
router.register(r'users', views.UserViewSet)

chat_router = routers.NestedDefaultRouter(router, r'chats', lookup='chat')
chat_router.register(r'messages', views.MessageViewSet, basename='chat-messages')

urlpatterns = [
    path('', views.home, name='home'),
    path('', include(router.urls)),
    path('', include(chat_router.urls)),
    path('messages/', views.messages_list, name='messages'),
    path('messages/world/', views.world_chat, name='world_chat'),
    path('messages/create/', views.create_chat, name='create_chat'),
    path('chat/<int:chat_id>/', views.chat_detail, name='chat-detail'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('friends/', views.friends_list, name='friends'),
    path('friends/search/', views.search_users, name='search_users'),
    path('friends/add/<int:user_id>/', views.add_friend, name='add_friend'),
    path('friends/accept/<int:user_id>/', views.accept_friend, name='accept_friend'),
    path('friends/reject/<int:user_id>/', views.reject_friend, name='reject_friend'),
    path('friends/remove/<int:user_id>/', views.remove_friend, name='remove_friend'),
    path('logout/', views.logout_view, name='logout'),
    path('chat/create/<int:user_id>/', views.create_private_chat, name='create_private_chat'),
    path('chat/<int:chat_id>/leave/', views.leave_chat, name='leave_chat'),
    path('chat/<int:chat_id>/delete/', views.delete_chat, name='delete_chat'),
    path('chat/<int:chat_id>/invite/', views.invite_to_chat, name='invite_to_chat'),
    path('profile/<int:user_id>/', views.view_profile, name='view_profile'),
    path('register/', views.register, name='register'),
] 