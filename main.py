import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    init_db,
    add_user,
    get_user,
    get_lesson,
    increment_attempts,
    reset_attempts_and_next_lesson
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

router = Router()

class TaskState(StatesGroup):
    waiting_for_answer = State()

def get_hint_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Получить подсказку", callback_data="get_hint")]
    ])

@router.message(Command("start"))
async def cmd_start(message: Message):
    await add_user(message.from_user.id)
    await message.answer(
        "👋 Привет! Ты на курсе подготовки к ЕГЭ по информатике.\n\n"
        "Спринт 1: Базовая логика, комбинаторика и кодирование.\n"
        "Жми /lesson, чтобы открыть текущий урок."
    )

@router.message(Command("lesson"))
async def cmd_lesson(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    lesson_id = user["current_lesson"] if user else 1
    lesson = await get_lesson(lesson_id)
    
    if not lesson:
        await message.answer("🏆 Красава! Ты полностью закрыл текущий спринт уроков!")
        return

    text = (
        f"📖 **Урок {lesson['lesson_id']}: {lesson['title']}**\n\n"
        f"💡 **Теория и шаблон:**\n{lesson['theory']}\n\n"
        f"🎯 **Практика:**\n{lesson['task_text']}"
    )
    
    await message.answer(text, parse_mode="Markdown")
    await message.answer("Введи ответ числом или строкой:")
    
    await state.set_state(TaskState.waiting_for_answer)
    await state.update_data(
        correct_answer=lesson["answer"],
        current_lesson=lesson["lesson_id"],
        hint=lesson["hint"]
    )

@router.message(TaskState.waiting_for_answer)
async def check_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    correct_answer = data.get("correct_answer")
    current_lesson = data.get("current_lesson")
    
    if message.text.strip().lower() == str(correct_answer).strip().lower():
        await reset_attempts_and_next_lesson(message.from_user.id, current_lesson + 1)
        await message.answer("✅ Ответ верный! Урок зачтен.\n\nЖми /lesson, чтобы перейти к следующему.")
        await state.clear()
    else:
        await increment_attempts(message.from_user.id)
        await message.answer(
            "❌ Не сошлось. Проверь код или пересчитай.\n\nНужна подсказка — жми кнопку:",
            reply_markup=get_hint_keyboard()
        )

@router.callback_query(F.data == "get_hint")
async def show_hint(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    hint = data.get("hint", "Подсказка отсутствует.")
    await callback.message.answer(f"🔍 **Подсказка:**\n{hint}", parse_mode="Markdown")
    await callback.answer()

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
        raise ValueError("BOT_TOKEN не задан!")
        
    await init_db()
    await start_dummy_server()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("🚀 Бот успешно стартовал!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
