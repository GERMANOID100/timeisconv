import os
from datetime import datetime
from pytz import timezone
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor

API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN not set")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

cities = {
    'Москва (UTC+3)': 'Europe/Moscow',
    'Нью-Йорк (UTC-4)': 'America/New_York',
    'Бали (UTC+8)': 'Asia/Makassar',
}

user_selection = {}

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    for name in cities:
        kb.insert(InlineKeyboardButton(name, callback_data=f"city1|{name}"))
    await message.answer("Выберите первый город:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("city1|"))
async def city1_selected(callback: types.CallbackQuery):
    city1 = callback.data.split("|", 1)[1]
    user_selection[callback.from_user.id] = {"city1": city1}
    kb = InlineKeyboardMarkup(row_width=2)
    for name in cities:
        if name != city1:
            kb.insert(InlineKeyboardButton(name, callback_data=f"city2|{name}"))
    await callback.message.edit_text(f"Первый город: {city1}\nТеперь выберите второй город:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("city2|"))
async def city2_selected(callback: types.CallbackQuery):
    city2 = callback.data.split("|", 1)[1]
    data = user_selection.get(callback.from_user.id, {})
    city1 = data.get("city1")
    if not city1 or city1 not in cities or city2 not in cities:
        await callback.message.answer("Ошибка. Выбор города некорректен.")
        return

    tz1 = cities[city1]
    tz2 = cities[city2]
    now_utc = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    current_hour = datetime.now().astimezone(timezone(tz1)).hour

    rows = []
    for hour in range(24):
        time_utc = now_utc.replace(hour=hour)
        local1 = time_utc.astimezone(timezone(tz1)).strftime('%H:%M')
        local2 = time_utc.astimezone(timezone(tz2)).strftime('%H:%M')
        marker = "←" if hour == current_hour else "  "
        rows.append(f"{local1:<7} | {local2:<7} {marker}")

    table = "\n".join(rows)
    text = f"{city1:<20} | {city2}\n{'-' * 38}\n{table}"

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("Сравнить снова", callback_data="restart"),
        InlineKeyboardButton("Показать текущее время", callback_data="show_now")
    )

    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "show_now")
async def show_now(callback: types.CallbackQuery):
    data = user_selection.get(callback.from_user.id, {})
    city1 = data.get("city1")
    if not city1 or city1 not in cities:
        await callback.message.answer("Сначала выберите города: /start")
        return
    tz1 = cities[city1]
    now = datetime.now(timezone(tz1))
    await callback.message.answer(f"Текущее время в {city1}: {now.strftime('%H:%M:%S %d.%m.%Y')}")

@dp.callback_query_handler(lambda c: c.data == "restart")
async def restart(callback: types.CallbackQuery):
    await start(callback.message)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)