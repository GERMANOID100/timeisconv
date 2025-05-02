import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from datetime import datetime
import pytz
import os

API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("❌ Ошибка: переменная API_TOKEN не задана. Проверь Railway → Variables.")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

LANGS = {
    "ru": {
        "start": "Выберите первый город:",
        "next": "Выберите второй город:",
        "again": "Сравнить другие города?",
        "result": (
            "{city1} ({tz1}): {time1_24} | {time1_12}\n"
            "{city2} ({tz2}): {time2_24} | {time2_12}\n"
            "Разница: {diff}"
        ),
        "error": "Произошла ошибка при получении времени.",
        "lang_set": "Язык переключен на русский 🇷🇺"
    },
    "en": {
        "start": "Select the first city:",
        "next": "Select the second city:",
        "again": "Compare other cities?",
        "result": (
            "{city1} ({tz1}): {time1_24} | {time1_12}\n"
            "{city2} ({tz2}): {time2_24} | {time2_12}\n"
            "Difference: {diff}"
        ),
        "error": "Error while calculating time.",
        "lang_set": "Language set to English 🇬🇧"
    }
}

# Расширенный список городов
cities = {
    "Москва": "Europe/Moscow",
    "Бали": "Asia/Makassar",
    "Минск": "Europe/Minsk",
    "Лондон": "Europe/London",
    "Берлин": "Europe/Berlin",
    "Сингапур": "Asia/Singapore",
    "Дубай": "Asia/Dubai",
    "Нью-Йорк": "America/New_York",
    "Лос-Анджелес": "America/Los_Angeles",
    "Сеул": "Asia/Seoul",
    "Токио": "Asia/Tokyo",
    "Сидней": "Australia/Sydney",
    "Париж": "Europe/Paris",
    "Киев": "Europe/Kyiv",
    "Шанхай": "Asia/Shanghai",
    "Торонто": "America/Toronto",
    "Рио-де-Жанейро": "America/Sao_Paulo",
    "Йоханнесбург": "Africa/Johannesburg",
    "Ташкент": "Asia/Tashkent",
    "Астана": "Asia/Almaty",
    "Стамбул": "Europe/Istanbul",
    "Дели": "Asia/Kolkata"
}

user_data = {}
user_lang = {}

def make_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    for city in sorted(cities):
        kb.insert(InlineKeyboardButton(city, callback_data=city))
    return kb

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    uid = message.from_user.id
    user_data[uid] = {"city1": None, "city2": None}
    lang = user_lang.get(uid, "ru")
    await message.answer(LANGS[lang]["start"], reply_markup=make_keyboard())

@dp.message_handler(commands=['lang'])
async def change_lang(message: types.Message):
    uid = message.from_user.id
    current = user_lang.get(uid, "ru")
    new_lang = "en" if current == "ru" else "ru"
    user_lang[uid] = new_lang
    await message.answer(LANGS[new_lang]["lang_set"])

@dp.callback_query_handler(lambda c: c.data in cities)
async def city_selected(callback_query: types.CallbackQuery):
    uid = callback_query.from_user.id
    lang = user_lang.get(uid, "ru")
    data = user_data.get(uid, {"city1": None, "city2": None})

    if not data["city1"]:
        data["city1"] = callback_query.data
        user_data[uid] = data
        await bot.send_message(uid, LANGS[lang]["next"], reply_markup=make_keyboard())
    elif not data["city2"]:
        data["city2"] = callback_query.data
        await show_time_comparison(uid, data["city1"], data["city2"], lang)
        user_data[uid] = {"city1": None, "city2": None}
        await bot.send_message(uid, LANGS[lang]["again"], reply_markup=make_keyboard())

async def show_time_comparison(uid, city1, city2, lang):
    try:
        tz1_name = cities[city1]
        tz2_name = cities[city2]
        tz1 = pytz.timezone(tz1_name)
        tz2 = pytz.timezone(tz2_name)
        now1 = datetime.now(tz1)
        now2 = datetime.now(tz2)
        delta = int((now2 - now1).total_seconds() / 3600)
        sign = "+" if delta >= 0 else "-"
        msg = LANGS[lang]["result"].format(
            city1=city1,
            city2=city2,
            tz1=tz1_name,
            tz2=tz2_name,
            time1_24=now1.strftime("%H:%M"),
            time2_24=now2.strftime("%H:%M"),
            time1_12=now1.strftime("%I:%M %p"),
            time2_12=now2.strftime("%I:%M %p"),
            diff=f"{sign}{abs(delta)} ч" if lang == "ru" else f"{sign}{abs(delta)} h"
        )
        await bot.send_message(uid, msg)
    except Exception as e:
        logging.exception("Ошибка при сравнении времени")
        await bot.send_message(uid, LANGS[lang]["error"])

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
