import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    init_db, add_user, get_user, get_lesson, 
    set_user_stage, next_lesson
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
router = Router()

class BotState(StatesGroup):
    answering_warmup = State()
    answering_exam = State()

def main_menu_keyboard(lesson_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Полный разбор + Шаблон кода", callback_data=f"theory_{lesson_id}")],
        [InlineKeyboardButton(text="⚡ Разминочная задача", callback_data=f"warmup_{lesson_id}")],
        [InlineKeyboardButton(text="🎯 Боевая задача ЕГЭ", callback_data=f"exam_{lesson_id}")]
    ])

def task_action_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Взять подсказку", callback_data="get_hint")],
        [InlineKeyboardButton(text="🔙 Вернуться в меню урока", callback_data="back_to_menu")]
    ])

@router.message(Command("start"))
@router.message(Command("menu"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await add_user(message.from_user.id)
    user = await get_user(message.from_user.id)
    lesson_id = user["current_lesson"] if user else 1
    lesson = await get_lesson(lesson_id)
    
    if not lesson:
        await message.answer("🏆 Ты закрыл всю доступную программу курса!")
        return

    text = (
        f"🎓 **Твой личный ментор по информатике**\n\n"
        f"Текущий модуль: **{lesson['title']}**\n"
        f"Выбирай действие в меню:"
    )
    await message.answer(text, reply_markup=main_menu_keyboard(lesson_id), parse_mode="Markdown")

@router.callback_query(F.data.startswith("theory_"))
async def send_theory(callback: CallbackQuery):
    lesson_id = int(callback.data.split("_")[1])
    lesson = await get_lesson(lesson_id)
    
    file_path = lesson["theory_file"]
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            theory_text = f.read()
        
        # Телеграм лимитирует сообщения по 4000 символов, бьем длинный текст
        if len(theory_text) > 4000:
            parts = [theory_text[i:i+4000] for i in range(0, len(theory_text), 4000)]
            for p in parts:
                await callback.message.answer(p, parse_mode="Markdown")
        else:
            await callback.message.answer(theory_text, parse_mode="Markdown")
    else:
        await callback.message.answer("⚠️ Файл с теорией не найден.")
    
    await callback.message.answer("Готов к практике?", reply_markup=main_menu_keyboard(lesson_id))
    await callback.answer()

@router.callback_query(F.data.startswith("warmup_"))
async def start_warmup(callback: CallbackQuery, state: FSMContext):
    lesson_id = int(callback.data.split("_")[1])
    lesson = await get_lesson(lesson_id)
    
    await state.set_state(BotState.answering_warmup)
    await state.update_data(
        target_answer=lesson["warmup_answer"],
        hint=lesson["hint"],
        lesson_id=lesson_id
    )
    
    text = f"⚡ **Разминка:**\n\n{lesson['warmup_task']}\n\nВведи полученный ответ:"
    await callback.message.answer(text, reply_markup=task_action_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("exam_"))
async def start_exam(callback: CallbackQuery, state: FSMContext):
    lesson_id = int(callback.data.split("_")[1])
    lesson = await get_lesson(lesson_id)
    
    await state.set_state(BotState.answering_exam)
    await state.update_data(
        target_answer=lesson["exam_answer"],
        hint=lesson["hint"],
        lesson_id=lesson_id
    )
    
    text = f"🎯 **Боевая задача уровня ЕГЭ:**\n\n{lesson['exam_task']}\n\nВведи ответ числом:"
    await callback.message.answer(text, reply_markup=task_action_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.message(BotState.answering_warmup)
@router.message(BotState.answering_exam)
async def check_user_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    expected = str(data.get("target_answer", "")).strip().lower()
    lesson_id = data.get("lesson_id")
    current_state = await state.get_state()

    if message.text.strip().lower() == expected:
        if current_state == BotState.answering_exam.state:
            await next_lesson(message.from_user.id, lesson_id + 1)
            await message.answer(
                "🔥 **Красава! Боевая задача решена чисто.**\n"
                "Балл в кармане. Модуль официально закрыт!\n\n"
                "Жми /menu, чтобы перейти к следующему номеру ЕГЭ.",
                parse_mode="Markdown"
            )
            await state.clear()
        else:
            await message.answer(
                "✅ Разминка пройдена верно! Теперь попробуй боевую задачу ЕГЭ.",
                reply_markup=main_menu_keyboard(lesson_id)
            )
            await state.clear()
    else:
        await message.answer(
            "❌ Ответ не сошелся. Проверь логику кода или возьми подсказку.",
            reply_markup=task_action_keyboard()
        )

@router.callback_query(F.data == "get_hint")
async def give_hint(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    hint = data.get("hint", "Внимательно перечитай шаблон теории.")
    await callback.message.answer(f"💡 **Наводка по алгоритму:**\n\n{hint}", parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lesson_id = data.get("lesson_id", 1)
    await state.clear()
    await callback.message.answer("Возвращаемся в меню модуля:", reply_markup=main_menu_keyboard(lesson_id))
    await callback.answer()

async def handle_ping(request):
    return web.Response(text="EGE Bot Mentor Live!")

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
        raise ValueError("BOT_TOKEN отсутствует!")
        
    await init_db()
    await start_dummy_server()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("🚀 Репетитор успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
