from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def token_auth(request):
    logger.info(f"Получен запрос на аутентификацию")
    logger.info(f"Данные запроса: {request.data}")
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    logger.info(f"Попытка входа пользователя: {username}")
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        login(request, user)
        logger.info(f"Успешный вход пользователя: {username}")
        return Response({'detail': 'Successfully logged in', 'username': username})
    else:
        logger.error(f"Неудачная попытка входа пользователя: {username}")
        return Response({'detail': 'Invalid credentials'}, status=400) 