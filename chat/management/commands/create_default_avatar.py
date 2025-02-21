from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Creates default avatar image'

    def handle(self, *args, **kwargs):
        # Создаем директорию если её нет
        static_dir = os.path.join(settings.BASE_DIR, 'chat', 'static', 'chat', 'images')
        os.makedirs(static_dir, exist_ok=True)
        
        # Создаем изображение
        size = (200, 200)
        img = Image.new('RGB', size, '#4a76a8')
        draw = ImageDraw.Draw(img)
        
        # Рисуем круг
        margin = 10
        draw.ellipse([margin, margin, size[0]-margin, size[1]-margin], fill='white')
        
        # Сохраняем
        img_path = os.path.join(static_dir, 'default-avatar.png')
        img.save(img_path)
        self.stdout.write(self.style.SUCCESS(f'Created default avatar at {img_path}')) 