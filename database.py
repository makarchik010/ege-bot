import aiosqlite

DB_NAME = "ege_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                current_lesson INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                lesson_id INTEGER PRIMARY KEY,
                title TEXT,
                theory TEXT,
                task_text TEXT,
                answer TEXT
            )
        """)
        cursor = await db.execute("SELECT COUNT(*) FROM lessons")
        count = (await cursor.fetchone())[0]
        if count == 0:
            await db.execute("""
                INSERT INTO lessons (lesson_id, title, theory, task_text, answer)
                VALUES (
                    1,
                    'Комбинаторика и itertools (Задание №8)',
                    'Метод itertools.product идеален для перебора строк заданной длины с повторениями.',
                    'Сколько существует 5-буквенных слов из букв В, А, Й, Б, где буква Й встречается ровно 1 раз?',
                    '512'
                )
            """)
        await db.commit()

async def add_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def get_user_lesson_id(user_id: int) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT current_lesson FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 1

async def get_lesson(lesson_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM lessons WHERE lesson_id = ?", (lesson_id,))
        return await cursor.fetchone()

async def update_user_lesson(user_id: int, next_lesson_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET current_lesson = ? WHERE user_id = ?", (next_lesson_id, user_id))
        await db.commit()
