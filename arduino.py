import pygame
import serial
from resources import letters
from dictionaries import letter_map

# --- Настройки окна и цветов ---
WIDTH, HEIGHT = 1000, 800
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CIRCLE_COLOR = (0, 0, 0)

# --- Класс для отображения точек Брайля ---
class BrailleDisplay:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.W = width
        self.H = height
        self.circle_radius = int(self.W * 0.05)
        self.circle_positions = [
            (int(self.W * 0.09), int(self.H * 0.15)),
            (int(self.W * 0.09), int(self.H * 0.5)),
            (int(self.W * 0.09), int(self.H * 0.85)),
            (int(self.W * 0.27), int(self.H * 0.15)),
            (int(self.W * 0.27), int(self.H * 0.5)),
            (int(self.W * 0.27), int(self.H * 0.85))
        ]

    def draw(self, binary_pattern):
        for i, bit in enumerate(binary_pattern):
            if bit == '1':
                x, y = self.circle_positions[i]
                pygame.draw.circle(self.screen, CIRCLE_COLOR, (x, y), self.circle_radius)


# --- Инициализация Pygame ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Интерфейс считывания карточек Брайля")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 120)

# --- Serial порт ---
ser = serial.Serial('COM3', 9600)

# --- Начальное состояние ---
last_letter_text = ""
current_pattern = "000000"

running = True
while running:
    screen.fill(WHITE)

    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Чтение из COM-порта
    try:
        line = ser.readline().decode('utf-8').strip()
        if line != '0' and len(line) >= 1 and len(line) <= 6:
            current_pattern = line[::-1]
            # Можно преобразовать к числу и воспроизвести звук, если нужно
            decimal_number = int(line)
            if decimal_number in letter_map:
                letters[decimal_number].play_sound()
                last_letter_text = f"Буква {letter_map[decimal_number]}"
        else:
            last_letter_text = ""
            current_pattern = "000000"


    except ValueError:
        last_letter_text = "Ошибка преобразования"
        current_pattern = "000000"
    except KeyboardInterrupt:
        running = False

    # Рисуем текст
    if last_letter_text:
        text_surface = font.render(last_letter_text, True, BLACK)
        text_rect = text_surface.get_rect(center=(screen.get_width() // 2 + 100, int(screen.get_height() * 0.5)))
        screen.blit(text_surface, text_rect)

    # Рисуем точки Брайля
    braille = BrailleDisplay(screen, screen.get_width(), screen.get_height())
    braille.draw(current_pattern)

    pygame.display.flip()
    clock.tick(10)

# Завершение
ser.close()
pygame.quit()
