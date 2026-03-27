import pygame
import os
import sys
from dictionaries import letter_code_map, dictations

# Инициализация микшера перед загрузкой звуков
pygame.init()
pygame.mixer.init()

# Функция для получения корректного пути к ресурсам
def resource_path(relative_path):
    """Возвращает корректный путь для ресурсов, учитывая режим разработки и сборки."""
    if getattr(sys, 'frozen', False):  # Если приложение собрано в exe
        base_dir = sys._MEIPASS  # Используем временную папку, созданную PyInstaller
    else:  # Если приложение запущено как скрипт
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Используем текущую директорию
    return os.path.join(base_dir, relative_path)

# Класс для представления буквы Брайля
class BrailleLetter:
    def __init__(self, image_path, sound_path):
        # Используем resource_path для загрузки ресурсов
        self.image = pygame.image.load(resource_path(image_path)) if image_path else None
        self.sound = pygame.mixer.Sound(resource_path(sound_path))

    def play_sound(self):
        self.sound.play()

# Пути к папкам с изображениями и звуками
images_dir = 'images'
sounds_dir = 'sounds'

# Словарь для хранения данных
letters_data = {}

# Обход файлов в папке с изображениями
for image_file in os.listdir(images_dir):
    if image_file.endswith('.png'):  # Проверяем, что это PNG-файл
        # Извлекаем имя буквы из названия файла (например, "буква_а.png" -> "а")
        letter_name = image_file.split('_')[-1].split('.')[0]
        
        # Формируем путь к изображению и звуку
        image_path = os.path.join(images_dir, image_file)
        sound_path = os.path.join(sounds_dir, f'{letter_name}.ogg')
        
        # Если звук существует, добавляем в словарь
        if os.path.exists(resource_path(sound_path)):
            # Получаем код буквы
            letter_code = letter_code_map.get(letter_name, -1)
            
            # Добавляем в словарь
            letters_data[letter_code] = (image_path, sound_path)
        else:
            print(f"Ошибка: звук для буквы {letter_name} не найден: {sound_path}")

# Добавляем специальный случай для перенабора
letters_data[-1] = (None, os.path.join(sounds_dir, 'набрать букву заново.ogg'))

# Создаем словарь с объектами BrailleLetter
letters = {pin: BrailleLetter(image_path, sound_path) for pin, (image_path, sound_path) in letters_data.items()}

# Словарь с изображениями букв Брайля
images = {pin: letter.image for pin, letter in letters.items() if letter.image}

# Добавляем пробел, если его нет
if 0 not in images:
    images[0] = pygame.image.load(resource_path('images/пробел.png'))
    
# Путь к папке со звуками слов
words_sounds_dir = os.path.join(sounds_dir, 'words')

# Словарь для хранения звуков слов
words_for_dict = {}

# Создаем плоский список всех слов из dictations
all_words = []
for letter_words in dictations.values():
    all_words.extend(letter_words)

# Загружаем звуки для каждого слова
for word in all_words:
    sound_path = os.path.join(words_sounds_dir, f'{word}.ogg')
    if os.path.exists(resource_path(sound_path)):
        words_for_dict[word] = pygame.mixer.Sound(resource_path(sound_path))
    else:
        print(f"Предупреждение: звук для слова '{word}' не найден: {sound_path}")
        words_for_dict[word] = None
        
