import aiosqlite

DB_NAME = "ege_bot.db"

TASKS_DATA = [
    {
        "lesson_id": 1,
        "title": "№8. Комбинаторика и перебор (itertools)",
        "theory_file": "lessons_data/lesson_1.md",
        "warmup_task": "Определи количество 4-буквенных слов из букв А, Б, В, если буква А встречается ровно 1 раз.",
        "warmup_answer": "32",
        "exam_task": "Сколько существует 5-значных восьмеричных чисел, которые не начинаются с 0, содержат ровно одну цифру 7, и после 7 не идет четная цифра?",
        "exam_answer": "4320",
        "hint": "1. Перебирай product('01234567', repeat=5).\n2. Отсекай s[0] == '0'.\n3. Проверяй s.count('7') == 1.\n4. Проверяй пары '7' + e для e in '0246'."
    }
]

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Сбрасываем старую таблицу уроков при запуске и создаем новую
        await db.execute("DROP TABLE IF EXISTS lessons")
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                current_lesson INTEGER DEFAULT 1,
                stage TEXT DEFAULT 'menu'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                lesson_id INTEGER PRIMARY KEY,
                title TEXT,
                theory_file TEXT,
                warmup_task TEXT,
                warmup_answer TEXT,
                exam_task TEXT,
                exam_answer TEXT,
                hint TEXT
            )
        """)
        
        for task in TASKS_DATA:
            await db.execute("""
                INSERT INTO lessons (
                    lesson_id, title, theory_file, warmup_task, 
                    warmup_answer, exam_task, exam_answer, hint
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task["lesson_id"], task["title"], task["theory_file"],
                task["warmup_task"], task["warmup_answer"],
                task["exam_task"], task["exam_answer"], task["hint"]
            ))
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

async def add_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def set_user_stage(user_id: int, stage: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET stage = ? WHERE user_id = ?", (stage, user_id))
        await db.commit()

async def next_lesson(user_id: int, next_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET current_lesson = ?, stage = 'menu' WHERE user_id = ?", (next_id, user_id))
        await db.commit()

async def get_lesson(lesson_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM lessons WHERE lesson_id = ?", (lesson_id,))
        return await cursor.fetchone()
