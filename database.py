import aiosqlite

DB_NAME = "ege_bot.db"

# Полная база всех 27 номеров ЕГЭ с описанием и темами
ALL_TASKS = [
    (1, "№1. Анализ графов и таблиц", "lessons_data/lesson_1.md", "Связи дорог, сопоставление весовых таблиц с графами."),
    (2, "№2. Таблицы истинности", "lessons_data/lesson_2.md", "Построение логических функций на Python через itertools/циклы."),
    (3, "№3. Базы данных и фильтрация", "lessons_data/lesson_3.md", "Связи таблиц, многотабличный поиск (Excel / Pandas)."),
    (4, "№4. Условие Фано и кодирование", "lessons_data/lesson_4.md", "Построение двоичных деревьев, однозначное декодирование."),
    (5, "№5. Анализ алгоритмов автоматов", "lessons_data/lesson_5.md", "Посимвольная обработка двоичных строк, перебор чисел N."),
    (6, "№6. Анализ алгоритмов Черепахи", "lessons_data/lesson_6.md", "Координатная сетка, циклы движения, подсчет точек."),
    (7, "№7. Кодирование медиаинформации", "lessons_data/lesson_7.md", "Объем звука и растровых изображений, палитры цветов."),
    (8, "№8. Комбинаторика и перебор слов", "lessons_data/lesson_8.md", "Перебор слов через itertools.product и permutations."),
    (9, "№9. Обработка таблиц чисел", "lessons_data/lesson_9.md", "Проверка геометрических и числовых условий строк."),
    (10, "№10. Поиск слова в текстовом редакторе", "lessons_data/lesson_10.md", "Регулярные выражения и поиск с учетом регистра."),
    (11, "№11. Вычисление объема памяти", "lessons_data/lesson_11.md", "Хранение паролей, посимвольное и побайтовое округление."),
    (12, "№12. Алгоритмы для Исполнителя", "lessons_data/lesson_12.md", "Замена строк через while '...' in s: s.replace(..., 1)."),
    (13, "№13. IP-адреса и маски подсетей", "lessons_data/lesson_13.md", "Работа с сетью через библиотеку ipaddress на Python."),
    (14, "№14. Системы счисления", "lessons_data/lesson_14.md", "Перевод в произвольные системы и решение уравнений."),
    (15, "№15. Истинность логических выражений", "lessons_data/lesson_15.md", "Поиск параметра А для отрезков, делителей и побитовой конъюнкции."),
    (16, "№16. Рекурсивные функции", "lessons_data/lesson_16.md", "Вычисление глубокой рекурсии, мемоизация через functools.lru_cache."),
    (17, "№17. Обработка числовых последовательностей", "lessons_data/lesson_17.md", "Чтение файлов, поиск пар и троек элементов с условиями."),
    (18, "№18. Динамика Робота в таблице", "lessons_data/lesson_18.md", "Поиск максимальных/минимальных сумм на сетке."),
    (19, "№19. Теория игр: 1 шаг", "lessons_data/lesson_19.md", "Анализ выигрышных стратегий на 1-2 кучах через рекурсию."),
    (20, "№20. Теория игр: 2 хода", "lessons_data/lesson_20.md", "Поиск победы Пети вторым ходом."),
    (21, "№21. Теория игр: 3 хода", "lessons_data/lesson_21.md", "Поиск победы Вани первым или вторым ходом."),
    (22, "№22. Многопроцессорные системы", "lessons_data/lesson_22.md", "Параллельные вычисления, времена процессов и зависимости."),
    (23, "№23. Динамическое программирование", "lessons_data/lesson_23.md", "Подсчет программ перехода от числа к числу с ограничениями."),
    (24, "№24. Текстовые файлы и строки", "lessons_data/lesson_24.md", "Поиск максимальных подстрок, метод двух указателей, split."),
    (25, "№25. Маски и делители чисел", "lessons_data/lesson_25.md", "Библиотека fnmatch, эффективный поиск делителей за O(sqrt(N))."),
    (26, "№26. Сортировка и жадные алгоритмы", "lessons_data/lesson_26.md", "Метод сканирующей прямой, упаковка грузов, парковки."),
    (27, "№27. Анализ данных и олимпиадная динамика", "lessons_data/lesson_27.md", "Префиксные суммы, остатки от деления, кластеризация.")
]

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS completed_tasks (
                user_id INTEGER,
                task_num INTEGER,
                PRIMARY KEY (user_id, task_num)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                num INTEGER PRIMARY KEY,
                title TEXT,
                theory_file TEXT,
                description TEXT
            )
        """)
        
        for task in ALL_TASKS:
            await db.execute("""
                INSERT OR REPLACE INTO tasks (num, title, theory_file, description)
                VALUES (?, ?, ?, ?)
            """, task)
            
        await db.commit()

async def add_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def get_task(num: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tasks WHERE num = ?", (num,))
        return await cursor.fetchone()

async def mark_task_completed(user_id: int, task_num: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO completed_tasks (user_id, task_num) VALUES (?, ?)", (user_id, task_num))
        await db.commit()

async def get_user_progress(user_id: int) -> set:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT task_num FROM completed_tasks WHERE user_id = ?", (user_id,))
        rows = await cursor.fetchall()
        return {r[0] for r in rows}
