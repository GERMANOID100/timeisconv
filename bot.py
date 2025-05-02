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
    'Москва': 'Europe/Moscow',
    'Бали': 'Asia/Makassar',
    'Нью-Йорк': 'America/New_York',
    'Лондон': 'Europe/London',
    'Токио': 'Asia/Tokyo',
    'Сидней': 'Australia/Sydney',
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
    city1 = callback.data.split('_')[1]
    user_selection[callback.from_user.id] = {'city1': city1}
    kb = InlineKeyboardMarkup(row_width=2)
    for name in cities:
        if name != city1:
            kb.insert(InlineKeyboardButton(name, callback_data=f"city2_{name}"))
    await callback.message.edit_text("Теперь выберите второй город:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('city2_'))
async def select_city2(callback: types.CallbackQuery):
    city2 = callback.data.split('_')[1]
    data = user_selection.get(callback.from_user.id, {})
    city1 = data.get('city1')
    if not city1:
        await callback.message.answer("Произошла ошибка. Попробуйте сначала: /start")
        return
    tz1 = cities[city1]
    tz2 = cities[city2]
    time1, offset1 = get_time_info(tz1)
    time2, offset2 = get_time_info(tz2)
    diff_hours = abs(offset1 - offset2)
    diff_str = f"{int(diff_hours)} ч." if diff_hours.is_integer() else f"{diff_hours:.1f} ч."
    text = (
        f"🕒 {city1} (UTC{offset1:+}): {time1}\n"
        f"🕒 {city2} (UTC{offset2:+}): {time2}\n"
        f"📍Разница: {diff_str}"
    )
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Повторить сравнение", callback_data="repeat"),
        InlineKeyboardButton("Сменить города", callback_data="restart"),
    )
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'repeat')
async def repeat(callback: types.CallbackQuery):
    data = user_selection.get(callback.from_user.id)
    if data:
        city1 = data.get('city1')
        for city2 in cities:
            if city2 != city1:
                data['city2'] = city2
                break
        await select_city2(callback)

@dp.callback_query_handler(lambda c: c.data == 'restart')
async def restart(callback: types.CallbackQuery):
    await start(callback.message)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)