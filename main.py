import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from database import (
    init_db,
    add_user,
    get_task,
    mark_task_completed,
    get_user_progress
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
router = Router()

def build_catalog_keyboard(progress: set):
    buttons = []
    row = []
    for num in range(1, 28):
        icon = "✅" if num in progress else str(num)
        row.append(InlineKeyboardButton(text=icon, callback_data=f"open_task_{num}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([
        InlineKeyboardButton(text="📊 Мой профиль и статистика", callback_data="show_stats")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def task_action_keyboard(task_num: int, is_done: bool):
    done_text = "❌ Сбросить отметку" if is_done else "✅ Отметить как решенное"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Открыть разбор и код-шаблон", callback_data=f"read_theory_{task_num}")],
        [InlineKeyboardButton(text=done_text, callback_data=f"toggle_done_{task_num}")],
        [InlineKeyboardButton(text="◀️ Назад к списку заданий", callback_data="back_to_catalog")]
    ])

@router.message(Command("start"))
@router.message(Command("menu"))
async def cmd_start(message: Message):
    await add_user(message.from_user.id)
    progress = await get_user_progress(message.from_user.id)
    
    total_done = len(progress)
    text = (
        "💻 **Интерактивный тренажер ЕГЭ по информатике**\n\n"
        f"Твой прогресс: **{total_done} из 27 заданий закрыто**.\n\n"
        "Выбирай нужный номер из сетки КИМ ниже для изучения теории, скриптов и отработки:"
    )
    await message.answer(text, reply_markup=build_catalog_keyboard(progress), parse_mode="Markdown")

@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    progress = await get_user_progress(callback.from_user.id)
    text = "Выбери номер задания из экзаменационной сетки:"
    await callback.message.edit_text(text, reply_markup=build_catalog_keyboard(progress))
    await callback.answer()

@router.callback_query(F.data.startswith("open_task_"))
async def open_task(callback: CallbackQuery):
    task_num = int(callback.data.split("_")[2])
    task = await get_task(task_num)
    progress = await get_user_progress(callback.from_user.id)
    is_done = task_num in progress
    
    status_icon = "✅ Изучено" if is_done else "⏳ В процессе"
    
    text = (
        f"🎯 **{task['title']}**\n"
        f"Статус: {status_icon}\n\n"
        f"**Суть номера:**\n{task['description']}\n\n"
        "Изучи методику решения или отметь номер после сдачи:"
    )
    await callback.message.edit_text(
        text, 
        reply_markup=task_action_keyboard(task_num, is_done),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("read_theory_"))
async def read_theory(callback: CallbackQuery):
    task_num = int(callback.data.split("_")[2])
    task = await get_task(task_num)
    
    file_path = task["theory_file"]
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            theory_text = f.read()
        
        if len(theory_text) > 4000:
            parts = [theory_text[i:i+4000] for i in range(0, len(theory_text), 4000)]
            for p in parts:
                await callback.message.answer(p)
        else:
            await callback.message.answer(theory_text)
    else:
        await callback.message.answer(f"📌 Разбор для задания №{task_num} находится на оформлении в актуальной версии КИМ.")
        
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_done_"))
async def toggle_done(callback: CallbackQuery):
    task_num = int(callback.data.split("_")[2])
    progress = await get_user_progress(callback.from_user.id)
    
    if task_num not in progress:
        await mark_task_completed(callback.from_user.id, task_num)
        await callback.answer("Номер отмечен как сданный! 🎯", show_alert=False)
    
    task = await get_task(task_num)
    new_progress = await get_user_progress(callback.from_user.id)
    is_done = task_num in new_progress
    status_icon = "✅ Изучено" if is_done else "⏳ В процессе"
    
    text = (
        f"🎯 **{task['title']}**\n"
        f"Статус: {status_icon}\n\n"
        f"**Суть номера:**\n{task['description']}\n\n"
        "Изучи методику решения или отметь номер после сдачи:"
    )
    await callback.message.edit_text(
        text, 
        reply_markup=task_action_keyboard(task_num, is_done),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "show_stats")
async def show_stats(callback: CallbackQuery):
    progress = await get_user_progress(callback.from_user.id)
    primary_score = len(progress)
    
    estimated_secondary = min(100, int((primary_score / 27) * 100))
    
    text = (
        "📈 **Аналитика твоей подготовки**\n\n"
        f"• Закрыто номеров: **{primary_score} / 27**\n"
        f"• Примерный вторичный балл: **~{estimated_secondary} / 100**\n\n"
        "Продолжай закрывать номера по списку, чтобы выйти на стабильные 90+."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к сетке", callback_data="back_to_catalog")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

async def handle_ping(request):
    return web.Response(text="EGE Trainer Online")

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
    
    print("🚀 Тренажер успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
