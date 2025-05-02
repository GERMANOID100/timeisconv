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
    'Бейкер-Айленд (UTC-12)': 'Etc/GMT+12',
    'Ниуэ (UTC-11)': 'Pacific/Niue',
    'Гонолулу (UTC-10)': 'Pacific/Honolulu',
    'Анкоридж (UTC-9)': 'America/Anchorage',
    'Лос-Анджелес (UTC-8)': 'America/Los_Angeles',
    'Денвер (UTC-7)': 'America/Denver',
    'Мехико (UTC-6)': 'America/Mexico_City',
    'Нью-Йорк (UTC-5)': 'America/New_York',
    'Каракас (UTC-4)': 'America/Caracas',
    'Буэнос-Айрес (UTC-3)': 'America/Argentina/Buenos_Aires',
    'Южная Георгия (UTC-2)': 'Atlantic/South_Georgia',
    'Азорские острова (UTC-1)': 'Atlantic/Azores',
    'Лондон (UTC+0)': 'Europe/London',
    'Варшава (UTC+1)': 'Europe/Warsaw',
    'Киев (UTC+2)': 'Europe/Kyiv',
    'Москва (UTC+3)': 'Europe/Moscow',
    'Минск (UTC+3)': 'Europe/Minsk',
    'Дубай (UTC+4)': 'Asia/Dubai',
    'Исламабад (UTC+5)': 'Asia/Karachi',
    'Дакка (UTC+6)': 'Asia/Dhaka',
    'Бангкок (UTC+7)': 'Asia/Bangkok',
    'Бали (UTC+8)': 'Asia/Makassar',
    'Токио (UTC+9)': 'Asia/Tokyo',
    'Сидней (UTC+10)': 'Australia/Sydney',
    'Соломоновы острова (UTC+11)': 'Pacific/Guadalcanal',
    'Окленд (UTC+12)': 'Pacific/Auckland',
    'Тонга (UTC+13)': 'Pacific/Tongatapu',
    'Киритимати (UTC+14)': 'Pacific/Kiritimati'
}
    'Москва (UTC+3)': 'Europe/Moscow',
    'Нью-Йорк (UTC-4)': 'America/New_York',
    'Бали (UTC+8)': 'Asia/Makassar',
    'Минск (UTC+3)': 'Europe/Minsk',
    'Токио (UTC+9)': 'Asia/Tokyo',
    'Сидней (UTC+10)': 'Australia/Sydney',
}

user_selection = {}
user_format = {}

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
    rows = []
    now_local = datetime.now(timezone(tz1)).replace(minute=0, second=0, microsecond=0)
    now_for_compare1 = datetime.now(timezone(tz1)).replace(minute=0, second=0, microsecond=0)
    now_for_compare2 = datetime.now(timezone(tz2)).replace(minute=0, second=0, microsecond=0)
    fmt = '%I:%M %p' if user_format.get(callback.from_user.id, '24') == '12' else '%H:%M'

    for i in range(24):
        time_local = now_local.replace(hour=(now_local.hour + i) % 24)
        local1_time = time_local.astimezone(timezone(tz1))
        local1 = local1_time.strftime(fmt)
        local2_time = time_local.astimezone(timezone(tz2))
        local2 = local2_time.strftime(fmt)
        mark1 = "🟢" if local1_time.replace(minute=0, second=0, microsecond=0) == now_for_compare1 else " "
        mark2 = "🟢" if local2_time.replace(minute=0, second=0, microsecond=0) == now_for_compare2 else " "
        rows.append(f"{local1:<7} {mark1} | {local2:<7} {mark2}")

    table = "\n".join(rows)
    text = f"{city1:<20} | {city2}\n{'-' * 38}\n{table}"

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("Сравнить снова", callback_data="restart"),
        InlineKeyboardButton("Показать текущее время", callback_data="show_now"),
        InlineKeyboardButton("🔁 Обновить таблицу", callback_data="refresh_table")
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

@dp.callback_query_handler(lambda c: c.data == "refresh_table")
async def refresh_table(callback: types.CallbackQuery):
    data = user_selection.get(callback.from_user.id, {})
    city1 = data.get("city1")
    if not city1:
        await callback.message.answer("Сначала выберите города: /start")
        return
    kb = InlineKeyboardMarkup(row_width=2)
    for name in cities:
        if name != city1:
            kb.insert(InlineKeyboardButton(name, callback_data=f"city2|{name}"))
    await callback.message.answer(f"Выберите второй город заново для обновления таблицы:", reply_markup=kb)

@dp.message_handler(commands=["format"])
async def set_format(message: types.Message):
    arg = message.get_args().strip()
    if arg not in ["12", "24"]:
        await message.answer("Используйте /format 12 или /format 24")
        return
    user_format[message.from_user.id] = arg
    await message.answer(f"✅ Формат времени установлен: {arg}-часовой")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)