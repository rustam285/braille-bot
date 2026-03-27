import pygame
import sys
import subprocess
import os

pygame.init()

WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Главное меню")

FONT = pygame.font.SysFont("arial", 24)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (100, 149, 237)
DARK_BLUE = (70, 120, 200)

# Получаем путь к директории, где находится исполняемый файл
base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

buttons = [
    {"label": "1. Матрица герконов", "action": lambda: subprocess.Popen([sys.executable, os.path.join(base_dir, "arduino.py")])},
    {"label": "2. Цифровая клавиатура", "action": lambda: subprocess.Popen([sys.executable, os.path.join(base_dir, "BrailleAppAdaptive.py")])},
    {"label": "3. Модуль диктантов", "action": lambda: subprocess.Popen([sys.executable, os.path.join(base_dir, "BrailleAppAdaptive.py"), "--mode", "dictation"])},
    {"label": "4. Прогресс учеников", "action": lambda: subprocess.Popen([sys.executable, os.path.join(base_dir, "admin.py")])}
]

BUTTON_WIDTH, BUTTON_HEIGHT = 350, 50
button_rects = []

start_y = 60
spacing = 70

for i, button in enumerate(buttons):
    x = (WIDTH - BUTTON_WIDTH) // 2
    y = start_y + i * spacing
    rect = pygame.Rect(x, y, BUTTON_WIDTH, BUTTON_HEIGHT)
    button_rects.append(rect)

running = True
while running:
    screen.fill(WHITE)

    for i, rect in enumerate(button_rects):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = rect.collidepoint(mouse_pos)
        color = DARK_BLUE if is_hovered else BLUE
        pygame.draw.rect(screen, color, rect, border_radius=12)

        text_surface = FONT.render(buttons[i]["label"], True, WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ
                for i, rect in enumerate(button_rects):
                    if rect.collidepoint(event.pos):
                        buttons[i]["action"]()

    pygame.display.flip()

pygame.quit()
sys.exit()