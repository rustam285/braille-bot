"""
VK-бот для отслеживания результатов диктантов учеников.
Требует: pip install vk_api

Запуск: python vk_dictation_bot.py
"""

import json
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
import os

# ─────────────────────────────────────────────
#  КОНФИГУРАЦИЯ
# ─────────────────────────────────────────────
VK_TOKEN  = os.getenv("VK_TOKEN")      # Вставьте токен сообщества VK
GROUP_ID  = int(os.getenv("GROUP_ID")) # ID вашего сообщества (число, без минуса)
DB_PATH   = "students_db.json"         # Путь к файлу с данными

# ─────────────────────────────────────────────
#  ЗАГРУЗКА БАЗЫ ДАННЫХ
# ─────────────────────────────────────────────
def load_db() -> dict:
    with open(DB_PATH, encoding="utf-8") as f:
        return json.load(f)

# ─────────────────────────────────────────────
#  ФОРМИРОВАНИЕ КЛАВИАТУР
# ─────────────────────────────────────────────
def kb_main() -> str:
    """Главное меню."""
    kb = VkKeyboard(one_time=False)
    kb.add_button("📋 Список учеников", color=VkKeyboardColor.PRIMARY)
    kb.add_button("🔍 Найти ученика",   color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button("📊 Сводка по всем",  color=VkKeyboardColor.POSITIVE)
    kb.add_button("❓ Помощь",          color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()


def kb_student_list(student_ids: list) -> str:
    """Кнопки с именами учеников (до 10 на экране)."""
    kb = VkKeyboard(one_time=True)
    for i, sid in enumerate(student_ids[:10]):   # VK ограничивает количество кнопок
        kb.add_button(sid, color=VkKeyboardColor.SECONDARY)
        if (i + 1) % 2 == 0 and i + 1 < len(student_ids[:10]):
            kb.add_line()
    kb.add_line()
    kb.add_button("🏠 Главное меню", color=VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()


def kb_back() -> str:
    """Кнопка возврата."""
    kb = VkKeyboard(one_time=True)
    kb.add_button("◀ Назад к списку", color=VkKeyboardColor.PRIMARY)
    kb.add_button("🏠 Главное меню",  color=VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()


def kb_student_dates(dates: list) -> str:
    """Кнопки с датами конкретного ученика."""
    kb = VkKeyboard(one_time=True)
    for i, date in enumerate(sorted(dates)):
        kb.add_button(f"📅 {date}", color=VkKeyboardColor.SECONDARY)
        if (i + 1) % 2 == 0 and i + 1 < len(dates):
            kb.add_line()
    kb.add_line()
    kb.add_button("📈 Все результаты", color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button("◀ Назад к списку", color=VkKeyboardColor.PRIMARY)
    kb.add_button("🏠 Главное меню",  color=VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()

# ─────────────────────────────────────────────
#  ФОРМИРОВАНИЕ ТЕКСТОВЫХ ОТВЕТОВ
# ─────────────────────────────────────────────
def format_student_summary(student_id: str, db: dict) -> str:
    """Краткая сводка по ученику: последняя дата + общая статистика."""
    data = db.get(student_id)
    if not data:
        return f"❌ Ученик «{student_id}» не найден."

    dates = sorted(data.keys())
    total_dictations = sum(len(v) for v in data.values())
    total_errors     = sum(
        info["errors"]
        for day in data.values()
        for info in day.values()
    )
    grades = [
        info["grade"]
        for day in data.values()
        for info in day.values()
    ]
    avg_grade = sum(grades) / len(grades) if grades else 0

    lines = [
        f"👤 {student_id}",
        f"📅 Сессий: {len(dates)}  |  Диктантов: {total_dictations}",
        f"⚠️  Всего ошибок: {total_errors}",
        f"⭐ Средняя оценка: {avg_grade:.1f}",
        f"🗓 Последний сеанс: {dates[-1]}",
    ]
    return "\n".join(lines)


def format_date_detail(student_id: str, date: str, db: dict) -> str:
    """Подробный отчёт по конкретной дате."""
    data = db.get(student_id, {}).get(date)
    if not data:
        return f"❌ Нет данных для {student_id} на {date}."

    lines = [f"📋 {student_id} — {date}\n"]
    for dictation_name, info in data.items():
        grade   = info.get("grade", "—")
        errors  = info.get("errors", 0)
        mistakes = info.get("mistakes", [])

        # Эмодзи по оценке
        if grade >= 9:
            mark = "🟢"
        elif grade >= 7:
            mark = "🟡"
        else:
            mark = "🔴"

        lines.append(f"{mark} {dictation_name}")
        lines.append(f"   Оценка: {grade}  |  Ошибок: {errors}")
        if mistakes:
            lines.append(f"   Ошибки: {', '.join(mistakes)}")
        lines.append("")

    return "\n".join(lines).strip()


def format_all_results(student_id: str, db: dict) -> list:
    """
    Полный отчёт по всем датам — возвращает список сообщений,
    чтобы не превышать лимит VK (4096 символов).
    """
    data = db.get(student_id)
    if not data:
        return [f"❌ Ученик «{student_id}» не найден."]

    messages = [f"📊 Полный отчёт: {student_id}\n"]
    current = messages[0]

    for date in sorted(data.keys()):
        block = format_date_detail(student_id, date, db) + "\n\n"
        if len(current) + len(block) > 3800:
            messages.append(current)
            current = block
        else:
            current += block

    if current:
        messages.append(current)

    return messages[1:]  # первый элемент — заголовок, уже вошёл в первый блок


def format_global_summary(db: dict) -> str:
    """Общая сводка по всем ученикам."""
    if not db:
        return "📭 База данных пуста."

    lines = ["📊 Сводка по всем ученикам\n"]
    for student_id in sorted(db.keys()):
        lines.append(format_student_summary(student_id, db))
        lines.append("─" * 30)

    return "\n".join(lines)

# ─────────────────────────────────────────────
#  СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЕЙ (сессия)
# ─────────────────────────────────────────────
# user_state[peer_id] = {"step": "main" | "student_selected",
#                         "student": "Ученик N"}
user_state: dict = {}

def get_state(peer_id: int) -> dict:
    if peer_id not in user_state:
        user_state[peer_id] = {"step": "main", "student": None}
    return user_state[peer_id]

# ─────────────────────────────────────────────
#  ОТПРАВКА СООБЩЕНИЙ
# ─────────────────────────────────────────────
def send(vk, peer_id: int, text: str, keyboard: str = None):
    params = dict(
        peer_id=peer_id,
        message=text,
        random_id=get_random_id(),
    )
    if keyboard:
        params["keyboard"] = keyboard
    vk.messages.send(**params)

# ─────────────────────────────────────────────
#  ОБРАБОТЧИК СООБЩЕНИЙ
# ─────────────────────────────────────────────
def handle(vk, peer_id: int, text: str):
    db    = load_db()
    state = get_state(peer_id)
    txt   = text.strip()

    # ── Главное меню ──────────────────────────
    if txt in ("🏠 Главное меню", "начало", "старт", "start", "menu", "меню"):
        state["step"]    = "main"
        state["student"] = None
        send(vk, peer_id,
             "🏠 Главное меню\nВыберите действие:",
             kb_main())
        return

    if txt == "❓ Помощь":
        help_text = (
            "ℹ️ Как пользоваться ботом:\n\n"
            "📋 Список учеников — показывает всех учеников\n"
            "🔍 Найти ученика — введите «Ученик N» вручную\n"
            "📊 Сводка по всем — статистика по всем ученикам\n\n"
            "После выбора ученика можно смотреть результаты\n"
            "по конкретной дате или все сразу."
        )
        send(vk, peer_id, help_text, kb_main())
        return

    # ── Список учеников ───────────────────────
    if txt == "📋 Список учеников":
        ids = list(db.keys())
        if not ids:
            send(vk, peer_id, "📭 База пуста.", kb_main())
        else:
            send(vk, peer_id,
                 f"👥 Учеников в базе: {len(ids)}\nВыберите ученика:",
                 kb_student_list(ids))
            state["step"] = "choosing_student"
        return

    # ── Поиск ────────────────────────────────
    if txt == "🔍 Найти ученика":
        send(vk, peer_id,
             "🔍 Введите ID ученика, например: Ученик 5")
        state["step"] = "search"
        return

    if state["step"] == "search":
        # Ищем по введённому тексту (регистронезависимо)
        match = next(
            (sid for sid in db if sid.lower() == txt.lower()), None
        )
        if match:
            state["student"] = match
            state["step"]    = "student_menu"
            dates = list(db[match].keys())
            send(vk, peer_id,
                 format_student_summary(match, db) + "\n\nВыберите дату:",
                 kb_student_dates(dates))
        else:
            send(vk, peer_id,
                 f"❌ Ученик «{txt}» не найден.\nПопробуйте ещё раз или вернитесь в меню.",
                 kb_main())
            state["step"] = "search"
        return

    # ── Глобальная сводка ────────────────────
    if txt == "📊 Сводка по всем":
        summary = format_global_summary(db)
        # Если текст длинный — разбиваем на части
        chunks = [summary[i:i+3800] for i in range(0, len(summary), 3800)]
        for i, chunk in enumerate(chunks):
            send(vk, peer_id, chunk,
                 kb_main() if i == len(chunks) - 1 else None)
        return

    # ── Выбор ученика из списка ───────────────
    if state["step"] == "choosing_student" and txt in db:
        state["student"] = txt
        state["step"]    = "student_menu"
        dates = list(db[txt].keys())
        send(vk, peer_id,
             format_student_summary(txt, db) + "\n\nВыберите дату или посмотрите всё:",
             kb_student_dates(dates))
        return

    # ── Меню ученика ─────────────────────────
    if state["step"] == "student_menu":
        student = state.get("student")

        if txt == "📈 Все результаты" and student:
            messages = format_all_results(student, db)
            for i, msg in enumerate(messages):
                send(vk, peer_id, msg,
                     kb_back() if i == len(messages) - 1 else None)
            return

        if txt == "◀ Назад к списку":
            ids = list(db.keys())
            send(vk, peer_id, "👥 Выберите ученика:", kb_student_list(ids))
            state["step"]    = "choosing_student"
            state["student"] = None
            return

        # Клик по дате (формат "📅 DD-MM-YYYY")
        if txt.startswith("📅 ") and student:
            date = txt.replace("📅 ", "").strip()
            detail = format_date_detail(student, date, db)
            send(vk, peer_id, detail, kb_student_dates(list(db[student].keys())))
            return

        # Возможно пользователь ввёл название ученика напрямую
        if txt in db:
            state["student"] = txt
            dates = list(db[txt].keys())
            send(vk, peer_id,
                 format_student_summary(txt, db) + "\n\nВыберите дату:",
                 kb_student_dates(dates))
            return

    # ── Прямой ввод ID ученика (любой шаг) ───
    if txt in db:
        state["student"] = txt
        state["step"]    = "student_menu"
        dates = list(db[txt].keys())
        send(vk, peer_id,
             format_student_summary(txt, db) + "\n\nВыберите дату:",
             kb_student_dates(dates))
        return

    # ── Неизвестная команда ───────────────────
    send(vk, peer_id,
         "🤷 Не понял команду. Воспользуйтесь меню:",
         kb_main())
    state["step"] = "main"

# ─────────────────────────────────────────────
#  ТОЧКА ВХОДА
# ─────────────────────────────────────────────
def main():
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk         = vk_session.get_api()
    longpoll   = VkBotLongPoll(vk_session, GROUP_ID)   # ← для токена сообщества

    print("✅ Бот запущен. Ожидание сообщений...")

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and event.object.message.get("from_id"):
            try:
                peer_id = event.object.message["peer_id"]
                text    = event.object.message.get("text", "")
                handle(vk, peer_id, text)
            except Exception as e:
                print(f"[ОШИБКА] peer_id={peer_id}: {e}")
                try:
                    send(vk, peer_id,
                         "⚠️ Произошла ошибка. Попробуйте ещё раз.",
                         kb_main())
                except Exception:
                    pass

if __name__ == "__main__":
    main()