from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Setup static files and create default avatar'

    def handle(self, *args, **kwargs):
        # Создаем все необходимые директории
        static_dir = os.path.join(settings.BASE_DIR, 'chat', 'static', 'chat', 'images')
        os.makedirs(static_dir, exist_ok=True)
        
        # Путь к файлу аватарки
        avatar_path = os.path.join(static_dir, 'default-avatar.png')
        
        # Создаем изображение
        size = (200, 200)
        img = Image.new('RGB', size, '#4a76a8')
        draw = ImageDraw.Draw(img)
        
        # Рисуем круг
        margin = 10
        draw.ellipse([margin, margin, size[0]-margin, size[1]-margin], fill='white')
        
        # Сохраняем изображение
        img.save(avatar_path)
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created default avatar at {avatar_path}')
        ) 