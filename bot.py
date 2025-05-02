import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from pytz import timezone
from datetime import datetime

API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

cities = {
    'Бейкер-Айленд (UTC-12)': 'Etc/GMT+12',
    'Ниуэ (UTC-11)': 'Pacific/Niue',
    'Гонолулу (UTC-10)': 'Pacific/Honolulu',
    'Анкоридж (UTC-8)': 'America/Anchorage',
    'Лос-Анджелес (UTC-7)': 'America/Los_Angeles',
    'Денвер (UTC-6)': 'America/Denver',
    'Мехико (UTC-6)': 'America/Mexico_City',
    'Нью-Йорк (UTC-4)': 'America/New_York',
    'Сантьяго (UTC-4)': 'America/Santiago',
    'Буэнос-Айрес (UTC-3)': 'America/Argentina/Buenos_Aires',
    'Южная Георгия (UTC-2)': 'Atlantic/South_Georgia',
    'Азорские острова (UTC+0)': 'Atlantic/Azores',
    'Лондон (UTC+1)': 'Europe/London',
    'Берлин (UTC+2)': 'Europe/Berlin',
    'Киев (UTC+3)': 'Europe/Kyiv',
    'Москва (UTC+3)': 'Europe/Moscow',
    'Дубай (UTC+4)': 'Asia/Dubai',
    'Исламабад (UTC+5)': 'Asia/Karachi',
    'Дакка (UTC+6)': 'Asia/Dhaka',
    'Бангкок (UTC+7)': 'Asia/Bangkok',
    'Сингапур (UTC+8)': 'Asia/Singapore',
    'Токио (UTC+9)': 'Asia/Tokyo',
    'Сидней (UTC+10)': 'Australia/Sydney',
    'Соломоновы острова (UTC+11)': 'Pacific/Guadalcanal',
    'Окленд (UTC+12)': 'Pacific/Auckland',
    'Тонга (UTC+13)': 'Pacific/Tongatapu',
    'Острова Лайн (UTC+14)': 'Pacific/Kiritimati',
}

user_selection = {}

def get_time_info(tz_name):
    now = datetime.now(timezone(tz_name))
    utc_offset = now.utcoffset().total_seconds() / 3600
    return now.strftime('%H:%M:%S %d.%m.%Y'), int(utc_offset)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    for name in cities:
        kb.insert(InlineKeyboardButton(name, callback_data=f"city1_{name}"))
    await message.answer("Выберите первый город:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('city1_'))
async def select_city1(callback: types.CallbackQuery):
    city1 = callback.data.split('_', 1)[1]
    user_selection[callback.from_user.id] = {'city1': city1}
    kb = InlineKeyboardMarkup(row_width=2)
    for name in cities:
        if name != city1:
            kb.insert(InlineKeyboardButton(name, callback_data=f"city2_{name}"))
    await callback.message.edit_text(f"Первый город: {city1}\nТеперь выберите второй город:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('city2_'))
async def select_city2(callback: types.CallbackQuery):
    city2 = callback.data.split('_', 1)[1]
    data = user_selection.get(callback.from_user.id, {})
    city1 = data.get('city1')
    if not city1:
        await callback.message.answer("Ошибка. Начните сначала: /start")
        return
    tz1 = cities[city1]
    tz2 = cities[city2]
    time1, offset1 = get_time_info(tz1)
    time2, offset2 = get_time_info(tz2)
    diff_hours = abs(offset1 - offset2)
    diff_str = f"{int(diff_hours)} ч." if diff_hours.is_integer() else f"{diff_hours:.1f} ч."
    text = (
        f"🕒 {city1}: {time1}\n"
        f"🕒 {city2}: {time2}\n"
        f"📍Разница: {diff_str}"
    )
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Сравнить снова", callback_data="restart"))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'restart')
async def restart(callback: types.CallbackQuery):
    await start(callback.message)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)