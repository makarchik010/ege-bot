import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import init_db, add_user, get_user_lesson_id, get_lesson, update_user_lesson

BOT_TOKEN = os.getenv("BOT_TOKEN")

router = Router()

class TaskState(StatesGroup):
    waiting_for_answer = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await add_user(message.from_user.id)
    await message.answer(
        "👋 Бот готов к работе!\n\n"
        "Жми /lesson, чтобы открыть первый урок."
    )

@router.message(Command("lesson"))
async def cmd_lesson(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lesson_id = await get_user_lesson_id(user_id)
    lesson = await get_lesson(lesson_id)
    
    if not lesson:
        await message.answer("🎉 Все доступные уроки пройдены!")
        return

    text = (
        f"📖 **Урок {lesson['lesson_id']}: {lesson['title']}**\n\n"
        f"💡 **Теория:**\n{lesson['theory']}\n\n"
        f"🎯 **Задача:**\n{lesson['task_text']}"
    )
    
    await message.answer(text, parse_mode="Markdown")
    await message.answer("Напиши ответ числом:")
    
    await state.set_state(TaskState.waiting_for_answer)
    await state.update_data(correct_answer=lesson["answer"], current_lesson=lesson["lesson_id"])

@router.message(TaskState.waiting_for_answer)
async def check_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    correct_answer = data.get("correct_answer")
    current_lesson = data.get("current_lesson")
    
    if message.text.strip().lower() == correct_answer.strip().lower():
        await update_user_lesson(message.from_user.id, current_lesson + 1)
        await message.answer("✅ Ответ верный! Урок зачтен.\nЖми /lesson для следующего.")
        await state.clear()
    else:
        await message.answer("❌ Ответ неверный. Попробуй еще раз.")

# Сервер-заглушка для бесплатного тарифа Render
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан в Environment Variables!")
        
    await init_db()
    await start_dummy_server()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("🚀 Бот успешно стартовал!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
