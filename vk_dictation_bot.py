"""
VK-бот для отслеживания результатов диктантов — v3
Установка: pip install vk_api psycopg2-binary python-dotenv
"""

import os
import re
import psycopg2
import psycopg2.extras
import psycopg2.pool
from dotenv import load_dotenv
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
DB_URL   = os.getenv("DATABASE_URL")

PAGE_SIZE = 9   # учеников на одной странице (9 + кнопка листания)

# ─────────────────────────────────────────────
#  ПУЛ СОЕДИНЕНИЙ — открывается один раз при старте
#  Это убирает задержку и ошибки на первом запросе
# ─────────────────────────────────────────────
_pool: psycopg2.pool.SimpleConnectionPool = None

def init_pool():
    global _pool
    _pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1, maxconn=5,
        dsn=DB_URL,
        connect_timeout=10
    )
    print("✅ Пул соединений с БД создан")

def get_conn():
    return _pool.getconn()

def put_conn(conn):
    _pool.putconn(conn)

# ─────────────────────────────────────────────
#  ЗАПРОСЫ К БД
# ─────────────────────────────────────────────
def db_query(sql: str, params=(), fetchone=False, fetchall=False):
    """Универсальный запрос: берёт соединение из пула, возвращает и освобождает."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, params)
            if fetchone:
                return cur.fetchone()
            if fetchall:
                return cur.fetchall()
        conn.commit()
    finally:
        put_conn(conn)


def db_get_all_students() -> list:
    """Возвращает список учеников, отсортированный по числовому ID."""
    rows = db_query("SELECT student_id FROM students", fetchall=True)
    ids  = [r[0] for r in rows]
    # Сортируем по числу в конце: "Ученик 2" < "Ученик 10"
    ids.sort(key=lambda s: int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 0)
    return ids


def db_get_student_dates(student_id: str) -> list:
    rows = db_query(
        "SELECT DISTINCT date FROM dictation_results WHERE student_id = %s ORDER BY date",
        (student_id,), fetchall=True
    )
    return [r[0] for r in rows]


def db_get_results_for_date(student_id: str, date: str) -> list:
    rows = db_query(
        """
        SELECT r.dictation_name, r.errors, r.grade,
               COALESCE(array_agg(m.word) FILTER (WHERE m.word IS NOT NULL), '{}') AS mistakes
        FROM dictation_results r
        LEFT JOIN dictation_mistakes m ON m.result_id = r.id
        WHERE r.student_id = %s AND r.date = %s
        GROUP BY r.id
        ORDER BY r.id
        """,
        (student_id, date), fetchall=True
    )
    return [dict(r) for r in rows]


def db_get_summary(student_id: str) -> dict:
    row = db_query(
        """
        SELECT COUNT(*), SUM(errors), ROUND(AVG(grade), 1), MAX(date), COUNT(DISTINCT date)
        FROM dictation_results WHERE student_id = %s
        """,
        (student_id,), fetchone=True
    )
    return {
        "total_dictations": row[0] or 0,
        "total_errors":     row[1] or 0,
        "avg_grade":        float(row[2]) if row[2] else 0.0,
        "last_date":        row[3] or "—",
        "total_sessions":   row[4] or 0,
    }


def db_student_exists(student_id: str) -> bool:
    row = db_query(
        "SELECT 1 FROM students WHERE student_id = %s",
        (student_id,), fetchone=True
    )
    return row is not None

# ─────────────────────────────────────────────
#  КЛАВИАТУРЫ
# ─────────────────────────────────────────────
def kb_main() -> str:
    kb = VkKeyboard(one_time=False)
    kb.add_button("📋 Список учеников", color=VkKeyboardColor.PRIMARY)
    kb.add_button("🔍 Найти ученика",   color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button("📊 Сводка по всем",  color=VkKeyboardColor.POSITIVE)
    kb.add_button("❓ Помощь",          color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()


def kb_student_list(student_ids: list, page: int = 0) -> str:
    """
    Страничный список: PAGE_SIZE учеников + стрелки навигации.
    Кнопки идут по 2 в ряд, последняя строка — навигация.
    """
    total_pages = max(1, (len(student_ids) + PAGE_SIZE - 1) // PAGE_SIZE)
    start = page * PAGE_SIZE
    chunk = student_ids[start: start + PAGE_SIZE]

    kb = VkKeyboard(one_time=True)
    for i, sid in enumerate(chunk):
        kb.add_button(sid, color=VkKeyboardColor.SECONDARY)
        # Новая строка после каждой второй кнопки (но не после последней)
        if (i + 1) % 2 == 0 and i + 1 < len(chunk):
            kb.add_line()

    # Навигационная строка
    kb.add_line()
    has_prev = page > 0
    has_next = page < total_pages - 1

    if has_prev and has_next:
        kb.add_button(f"◀ стр.{page}",   color=VkKeyboardColor.PRIMARY)
        kb.add_button(f"стр.{page+2} ▶", color=VkKeyboardColor.PRIMARY)
    elif has_prev:
        kb.add_button(f"◀ стр.{page}",   color=VkKeyboardColor.PRIMARY)
        kb.add_button("🏠 Главное меню", color=VkKeyboardColor.NEGATIVE)
    elif has_next:
        kb.add_button(f"стр.{page+2} ▶", color=VkKeyboardColor.PRIMARY)
        kb.add_button("🏠 Главное меню", color=VkKeyboardColor.NEGATIVE)
    else:
        kb.add_button("🏠 Главное меню", color=VkKeyboardColor.NEGATIVE)

    return kb.get_keyboard()


def kb_back() -> str:
    kb = VkKeyboard(one_time=True)
    kb.add_button("◀ Назад к списку", color=VkKeyboardColor.PRIMARY)
    kb.add_button("🏠 Главное меню",  color=VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()


def kb_student_dates(dates: list) -> str:
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
#  ФОРМАТИРОВАНИЕ
# ─────────────────────────────────────────────
def format_summary(student_id: str) -> str:
    s    = db_get_summary(student_id)
    mark = "🟢" if s["avg_grade"] >= 9 else ("🟡" if s["avg_grade"] >= 7 else "🔴")
    return (
        f"👤 {student_id}\n"
        f"📅 Сессий: {s['total_sessions']}  |  Диктантов: {s['total_dictations']}\n"
        f"⚠️  Всего ошибок: {s['total_errors']}\n"
        f"{mark} Средняя оценка: {s['avg_grade']}\n"
        f"🗓 Последний сеанс: {s['last_date']}"
    )


def format_date_detail(student_id: str, date: str) -> str:
    results = db_get_results_for_date(student_id, date)
    if not results:
        return f"❌ Нет данных для {student_id} на {date}."

    lines = [f"📋 {student_id} — {date}\n"]
    for r in results:
        grade = r["grade"]
        mark  = "🟢" if grade >= 9 else ("🟡" if grade >= 7 else "🔴")
        lines.append(f"{mark} {r['dictation_name']}")
        lines.append(f"   Оценка: {grade}  |  Ошибок: {r['errors']}")
        if r["mistakes"]:
            lines.append(f"   Ошибки: {', '.join(r['mistakes'])}")
        lines.append("")
    return "\n".join(lines).strip()


def format_all_results(student_id: str) -> list:
    dates = db_get_student_dates(student_id)
    if not dates:
        return [f"📭 У ученика {student_id} нет данных."]

    messages, current = [], f"📊 Полный отчёт: {student_id}\n\n"
    for date in dates:
        block = format_date_detail(student_id, date) + "\n\n"
        if len(current) + len(block) > 3800:
            messages.append(current)
            current = block
        else:
            current += block
    if current:
        messages.append(current)
    return messages


def format_global_summary() -> list:
    students = db_get_all_students()
    if not students:
        return ["📭 База данных пуста."]

    messages, current = [], "📊 Сводка по всем ученикам\n\n"
    sep = "─" * 28 + "\n"
    for sid in students:
        block = format_summary(sid) + "\n" + sep
        if len(current) + len(block) > 3800:
            messages.append(current)
            current = block
        else:
            current += block
    if current:
        messages.append(current)
    return messages

# ─────────────────────────────────────────────
#  СЕССИИ
# ─────────────────────────────────────────────
user_state: dict = {}

def get_state(peer_id: int) -> dict:
    if peer_id not in user_state:
        user_state[peer_id] = {"step": "main", "student": None, "page": 0}
    return user_state[peer_id]

# ─────────────────────────────────────────────
#  ОТПРАВКА
# ─────────────────────────────────────────────
def send(vk, peer_id: int, text: str, keyboard: str = None):
    params = dict(peer_id=peer_id, message=text, random_id=get_random_id())
    if keyboard:
        params["keyboard"] = keyboard
    vk.messages.send(**params)

# ─────────────────────────────────────────────
#  ВСПОМОГАТЕЛЬНЫЕ
# ─────────────────────────────────────────────
def show_student_list(vk, peer_id, state, page=0):
    ids = db_get_all_students()
    state["step"] = "choosing_student"
    state["page"] = page
    total_pages   = max(1, (len(ids) + PAGE_SIZE - 1) // PAGE_SIZE)
    send(vk, peer_id,
         f"👥 Учеников: {len(ids)} | Страница {page+1}/{total_pages}\nВыберите:",
         kb_student_list(ids, page))


def open_student(vk, peer_id, state, student_id):
    state.update(step="student_menu", student=student_id)
    dates = db_get_student_dates(student_id)
    send(vk, peer_id,
         format_summary(student_id) + "\n\nВыберите дату:",
         kb_student_dates(dates))

# ─────────────────────────────────────────────
#  ОБРАБОТЧИК СООБЩЕНИЙ
# ─────────────────────────────────────────────
def handle(vk, peer_id: int, text: str):
    state = get_state(peer_id)
    txt   = text.strip()

    # ── Старт / главное меню ──────────────────
    if txt.lower() in ("начало", "старт", "start", "begin", "привет", "hello"):
        state.update(step="main", student=None, page=0)
        send(vk, peer_id,
             "👋 Привет! Я бот для отслеживания результатов диктантов.\n\n"
             "📚 Здесь преподаватель может:\n"
             "• Посмотреть прогресс любого ученика\n"
             "• Узнать оценки и ошибки по каждому диктанту\n"
             "• Получить сводку по всем ученикам сразу\n\n"
             "Выберите действие в меню ниже 👇",
             kb_main())
        return

    if txt == "🏠 Главное меню":
        state.update(step="main", student=None, page=0)
        send(vk, peer_id, "🏠 Главное меню:", kb_main())
        return

    if txt == "❓ Помощь":
        send(vk, peer_id,
             "ℹ️ Как пользоваться ботом:\n\n"
             "📋 Список учеников — все ученики постранично\n"
             "   (стрелки ◀ ▶ переключают страницы)\n"
             "🔍 Найти ученика — введи «Ученик N» вручную\n"
             "📊 Сводка по всем — статистика по всем сразу\n\n"
             "После выбора ученика нажми на дату\n"
             "или «Все результаты» для полной истории.",
             kb_main())
        return

    # ── Список учеников ───────────────────────
    if txt == "📋 Список учеников":
        show_student_list(vk, peer_id, state, page=0)
        return

    # Листание страниц (кнопки "◀ стр.N" и "стр.N ▶")
    prev_match = re.match(r'^◀ стр\.(\d+)$', txt)
    next_match = re.match(r'^стр\.(\d+) ▶$', txt)
    if prev_match:
        show_student_list(vk, peer_id, state, page=int(prev_match.group(1)) - 1)
        return
    if next_match:
        show_student_list(vk, peer_id, state, page=int(next_match.group(1)) - 1)
        return

    # ── Поиск вручную ────────────────────────
    if txt == "🔍 Найти ученика":
        send(vk, peer_id, "🔍 Введите ID, например: Ученик 5")
        state["step"] = "search"
        return

    if state["step"] == "search":
        if db_student_exists(txt):
            open_student(vk, peer_id, state, txt)
        else:
            send(vk, peer_id,
                 f"❌ Ученик «{txt}» не найден.\nПопробуйте ещё раз:",
                 kb_main())
        return

    # ── Сводка по всем ───────────────────────
    if txt == "📊 Сводка по всем":
        msgs = format_global_summary()
        for i, msg in enumerate(msgs):
            send(vk, peer_id, msg, kb_main() if i == len(msgs) - 1 else None)
        return

    # ── Назад к списку ────────────────────────
    if txt == "◀ Назад к списку":
        show_student_list(vk, peer_id, state, page=state.get("page", 0))
        return

    # ── Выбор ученика из списка ───────────────
    if state["step"] == "choosing_student" and db_student_exists(txt):
        open_student(vk, peer_id, state, txt)
        return

    # ── Меню ученика ─────────────────────────
    if state["step"] == "student_menu":
        student = state.get("student")

        if txt == "📈 Все результаты" and student:
            msgs = format_all_results(student)
            for i, msg in enumerate(msgs):
                send(vk, peer_id, msg, kb_back() if i == len(msgs) - 1 else None)
            return

        if txt.startswith("📅 ") and student:
            date = txt.replace("📅 ", "").strip()
            send(vk, peer_id,
                 format_date_detail(student, date),
                 kb_student_dates(db_get_student_dates(student)))
            return

    # ── Прямой ввод ID (любой шаг) ───────────
    if db_student_exists(txt):
        open_student(vk, peer_id, state, txt)
        return

    # ── Неизвестная команда ───────────────────
    send(vk, peer_id, "🤷 Не понял. Воспользуйтесь меню:", kb_main())
    state["step"] = "main"

# ─────────────────────────────────────────────
#  ЗАПУСК
# ─────────────────────────────────────────────
def main():
    init_pool()   # ← пул соединений создаётся один раз при старте

    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk         = vk_session.get_api()
    longpoll   = VkBotLongPoll(vk_session, GROUP_ID)
    print("✅ Бот запущен (PostgreSQL + пул соединений)...")

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and event.object.message.get("from_id"):
            peer_id = event.object.message["peer_id"]
            text    = event.object.message.get("text", "")
            try:
                handle(vk, peer_id, text)
            except Exception as e:
                print(f"[ОШИБКА] peer_id={peer_id}: {e}")
                try:
                    send(vk, peer_id, "⚠️ Ошибка. Попробуйте ещё раз.", kb_main())
                except Exception:
                    pass

if __name__ == "__main__":
    main()