from django.urls import path, include

urlpatterns = [
    # ... другие URL-паттерны ...
    path('api/', include('chat.urls')),  # Убедимся, что этот путь существует
] 