import pygame
import json
import sys

# Константы
WIDTH, HEIGHT = 800, 600
LEFT_PANEL_WIDTH = 250
FONT_SIZE = 24
LINE_HEIGHT = FONT_SIZE + 15

# Цвета
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
BLUE = (173, 216, 230)

# Загрузка базы
with open("students_db.json", encoding="utf-8") as f:
    students_db = json.load(f)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Прогресс учеников")
font = pygame.font.SysFont(None, FONT_SIZE)
clock = pygame.time.Clock()

selected_student = None
scroll_offset = 0

# Получаем список ID учеников
student_ids = list(students_db.keys())

# Максимальный сдвиг зависит от количества учеников
def get_max_scroll():
    total_height = len(student_ids) * LINE_HEIGHT
    return max(0, total_height - HEIGHT)

running = True
while running:
    screen.fill(WHITE)

    # Левая панель — список ID
    pygame.draw.rect(screen, GRAY, (0, 0, LEFT_PANEL_WIDTH, HEIGHT))

    # Прокручиваем список учеников
    y = 10 - scroll_offset
    id_rects = []
    for student_id in student_ids:
        rect = pygame.Rect(10, y, LEFT_PANEL_WIDTH - 20, FONT_SIZE + 10)
        id_rects.append((rect, student_id))

        color = BLUE if student_id == selected_student else WHITE
        pygame.draw.rect(screen, color, rect)

        text = font.render(student_id, True, BLACK)
        screen.blit(text, (rect.x + 5, rect.y + 5))
        y += LINE_HEIGHT

    # Правая панель — прогресс ученика
    if selected_student:
        x = LEFT_PANEL_WIDTH + 20
        y = 20
        student_data = students_db[selected_student]
        for date, dictations in sorted(student_data.items()):
            date_text = font.render(f"{date}", True, BLACK)
            screen.blit(date_text, (x, y))
            y += FONT_SIZE + 5

            for dictation_name, info in dictations.items():
                summary = f"  {dictation_name}: Ошибок {info['errors']}, Оценка {info['grade']}"
                d_text = font.render(summary, True, BLACK)
                screen.blit(d_text, (x + 10, y))
                y += FONT_SIZE + 5

                if info['mistakes']:
                    mistakes = ", ".join(info['mistakes'])
                    m_text = font.render(f"    Ошибки: {mistakes}", True, BLACK)
                    screen.blit(m_text, (x + 20, y))
                    y += FONT_SIZE + 5

            y += 10

    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if mouse_x < LEFT_PANEL_WIDTH:
                for rect, student_id in id_rects:
                    if rect.collidepoint(mouse_x, mouse_y):
                        selected_student = student_id
                        break

        elif event.type == pygame.MOUSEWHEEL:
            scroll_offset -= event.y * LINE_HEIGHT
            scroll_offset = max(0, min(scroll_offset, get_max_scroll()))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()

vk_api = vk1.a.yVxqJhh8Orvd4Ikf0TjYEJgCrBuCISxLr8_tEYnzEn-LAy80cLZQSERqkKYuzR2On0Mx9di34CbyC6EdPOt9mj_aDMl2HtLv36F_caAA2X5KWIo-zCUbC_Y4ptrQTyoPR_O4_SzJB_x1HYPVWre61tBFeeu9QQuIN5ZnnGWaURHHVr5c_Lw7WG-Db3oo7TsbIp60anZREckxomaPaIp0mQ
