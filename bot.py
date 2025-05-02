import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from datetime import datetime
import pytz
import os

API_TOKEN = os.getenv('API_TOKEN')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

cities = {
    "Москва": "Europe/Moscow",
    "Бали": "Asia/Makassar",
    "Лондон": "Europe/London",
    "Нью-Йорк": "America/New_York",
    "Токио": "Asia/Tokyo",
    "Берлин": "Europe/Berlin",
    "Сингапур": "Asia/Singapore",
    "Дубай": "Asia/Dubai",
    "Лос-Анджелес": "America/Los_Angeles",
    "Сеул": "Asia/Seoul",
    "Минск": "Europe/Minsk"
}

user_data = {}

def make_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(city, callback_data=city) for city in cities]
    kb.add(*buttons)
    return kb

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_data[message.from_user.id] = {"city1": None, "city2": None}
    await message.answer("Выберите первый город:", reply_markup=make_keyboard())

@dp.callback_query_handler(lambda c: c.data in cities)
async def process_city(callback_query: types.CallbackQuery):
    uid = callback_query.from_user.id
    data = user_data.get(uid, {"city1": None, "city2": None})

    if not data["city1"]:
        data["city1"] = callback_query.data
        user_data[uid] = data
        await bot.send_message(uid, "Выберите второй город:", reply_markup=make_keyboard())
    elif not data["city2"]:
        data["city2"] = callback_query.data
        await send_time_comparison(uid, data["city1"], data["city2"])
        user_data[uid] = {"city1": None, "city2": None}
        await bot.send_message(uid, "Хотите сравнить другие города? Выберите первый:", reply_markup=make_keyboard())

async def send_time_comparison(uid, city1, city2):
    tz1 = pytz.timezone(cities[city1])
    tz2 = pytz.timezone(cities[city2])
    now1 = datetime.now(tz1)
    now2 = datetime.now(tz2)
    delta = (now2 - now1).total_seconds() / 3600
    sign = "+" if delta >= 0 else "-"
    await bot.send_message(
        uid,
        f"{city1}: {now1.strftime('%H:%M')}
"
        f"{city2}: {now2.strftime('%H:%M')}
"
        f"Разница: {sign}{abs(int(delta))} ч"
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
