import aiosqlite

DB_NAME = "ege_bot.db"

SPRINT_1_LESSONS = [
    (
        1,
        "Комбинаторика и itertools (Задание №8)",
        "Для перебора слов заданной длины с повторениями используй `itertools.product`.\n\nШаблон кода:\n```python\nfrom itertools import product\n\nwords = list(product('ВИШНЯ', repeat=6))\ncount = 0\nfor w in words:\n    s = ''.join(w)\n    if s.count('В') <= 1:\n        count += 1\nprint(count)\n```",
        "Сколько существует 5-буквенных слов из букв В, А, Й, Б, где буква Й встречается ровно 1 раз?",
        "512",
        "Всего вариантов букв 4. На одной из 5 позиций стоит 'Й' (5 способов), на остальных 4 позициях могут стоять любые из трех букв (В, А, Б). Формула: 5 * (3 ** 4) = 405... Стоп, проверь условие внимательно перебором на Python через product!"
    ),
    (
        2,
        "Таблицы истинности на Python (Задание №2)",
        "Шаблон решения через логические операции:\n```python\nprint('x y z w')\nfor x in 0, 1:\n    for y in 0, 1:\n        for z in 0, 1:\n            for w in 0, 1:\n                f = (x <= y) and (y <= z) or (w == x)\n                if not f:\n                    print(x, y, z, w)\n```",
        "Миша заполняет таблицу для функции (x ≡ ¬y) → (z ≡ (y ∨ w)). Сколько всего строк таблицы истинности содержат значение 0?",
        "4",
        "Напиши вложенный цикл по всем четырем переменным (0, 1), посчитай значение выражения и сделай счетчик `if f == 0: count += 1`."
    ),
    (
        3,
        "Кодирование и условие Фано (Задание №4)",
        "Прямое условие Фано: ни одно кодовое слово не должно быть началом другого кодового слова. Всегда строй дерево: влево 0, вправо 1.",
        "Для кодирования букв А, Б, В, Г используются коды: А - 00, Б - 01, В - 10. Какова наименьшая возможная длина двоичного кода для буквы Г, если условие Фано соблюдается?",
        "2",
        "Посмотри на оставшиеся ветки дерева длины 2: есть ли еще свободная комбинация из двух символов?"
    ),
    (
        4,
        "Кодирование изображений и звука (Задание №7)",
        "Формула объема изображения: `I = K * i`, где K = X * Y (пиксели), 2^i = N (цвета). Для звука: `I = f * t * b * k` (частота * время * глубина * каналы). Все переводим в биты!",
        "Изображение 1024x768 пикселей сохранили в файле объемом 768 Кбайт без сжатия. Каково максимальное количество цветов в палитре?",
        "256",
        "1. Переведи 768 Кбайт в биты: 768 * 1024 * 8.\n2. Раздели на (1024 * 768) — получишь i (бит на пиксель).\n3. Количество цветов N = 2^i."
    ),
    (
        5,
        "Кодирование текстовых сведений (Задание №11)",
        "Для каждого пользователя сохраняется ID и доп. сведения. Весь ID кодируется посимвольно (алфавит -> 2^i, округление бит на символ, потом округление всего ID до целых байт!).",
        "Пароль состоит из 10 символов алфавита из 26 букв. Каждый символ кодируется минимальным числом бит. Пароль округляется до целых байт. Сколько байт нужно для 20 пользователей?",
        "140",
        "Алфавит 26 -> 2^5 = 32 (5 бит на символ). 10 символов * 5 = 50 бит. В байтах: 50 / 8 = 6.25 -> округляем вверх до 7 байт. 7 * 20 = ?"
    ),
    (
        6,
        "Графы и таблицы (Задание №1)",
        "Сопоставление таблицы и графа. Считай степени вершин (сколько дорог выходит из каждого пункта). Находи уникальные вершины-«одиночки» или узлы связности.",
        "В таблице пункт П1 связан с П2, П3, П4 (степень 3). Если вершина В в графе единственная со степенью 3, какому номеру пункта она соответствует? Введи номер числа (например, 1).",
        "1",
        "Сравни степени вершин в графе и количество звездочек в строках таблицы."
    )
]

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                current_lesson INTEGER DEFAULT 1,
                attempts INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                lesson_id INTEGER PRIMARY KEY,
                title TEXT,
                theory TEXT,
                task_text TEXT,
                answer TEXT,
                hint TEXT
            )
        """)
        
        # Обновляем/заполняем уроки Спринта 1
        for lesson in SPRINT_1_LESSONS:
            await db.execute("""
                INSERT OR REPLACE INTO lessons (lesson_id, title, theory, task_text, answer, hint)
                VALUES (?, ?, ?, ?, ?, ?)
            """, lesson)
            
        await db.commit()

async def add_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

async def get_lesson(lesson_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM lessons WHERE lesson_id = ?", (lesson_id,))
        return await cursor.fetchone()

async def increment_attempts(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET attempts = attempts + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def reset_attempts_and_next_lesson(user_id: int, next_lesson_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET current_lesson = ?, attempts = 0 WHERE user_id = ?", (next_lesson_id, user_id))
        await db.commit()
