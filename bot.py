import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from datetime import datetime
import pytz
import os

API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("❌ Переменная окружения API_TOKEN не задана.")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

LANGS = {
    "ru": {
        "start": "Выберите первый город:",
        "next": "Выберите второй город:",
        "again": "🌍 Повторить сравнение",
        "switch": "🔄 Сменить города",
        "result": (
            "{city1} ({tz1})\n🗓 {date1}\n🕐 {time1_24} | {time1_12}\n\n"
            "{city2} ({tz2})\n🗓 {date2}\n🕐 {time2_24} | {time2_12}\n\n"
            "Разница: {diff}"
        ),
        "error": "Произошла ошибка при получении времени.",
        "lang_set": "Язык переключен на русский 🇷🇺",
        "manual": "Введите название города вручную:"
    },
    "en": {
        "start": "Select the first city:",
        "next": "Select the second city:",
        "again": "🌍 Compare again",
        "switch": "🔄 Switch cities",
        "result": (
            "{city1} ({tz1})\n🗓 {date1}\n🕐 {time1_24} | {time1_12}\n\n"
            "{city2} ({tz2})\n🗓 {date2}\n🕐 {time2_24} | {time2_12}\n\n"
            "Difference: {diff}"
        ),
        "error": "Error while calculating time.",
        "lang_set": "Language set to English 🇬🇧",
        "manual": "Type city name manually:"
    }
}

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
        await show_comparison(uid, data["city1"], data["city2"], lang)

async def show_comparison(uid, city1, city2, lang):
    try:
        tz1_name = cities[city1]
        tz2_name = cities[city2]
        tz1 = pytz.timezone(tz1_name)
        tz2 = pytz.timezone(tz2_name)
        now1 = datetime.now(tz1)
        now2 = datetime.now(tz2)
        delta_seconds = abs(int((now2 - now1).total_seconds()))
        hours, remainder = divmod(delta_seconds, 3600)
        minutes = remainder // 60
        sign = "+" if (now2 - now1).total_seconds() >= 0 else "-"
        diff = f"{sign}{hours} ч {minutes} мин" if lang == "ru" else f"{sign}{hours} h {minutes} min"
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton(LANGS[lang]["again"], callback_data="again"),
            InlineKeyboardButton(LANGS[lang]["switch"], callback_data="switch")
        )
        msg = LANGS[lang]["result"].format(
            city1=city1, tz1=tz1_name, date1=now1.strftime("%d.%m.%Y (%A)"),
            time1_24=now1.strftime("%H:%M"), time1_12=now1.strftime("%I:%M %p"),
            city2=city2, tz2=tz2_name, date2=now2.strftime("%d.%m.%Y (%A)"),
            time2_24=now2.strftime("%H:%M"), time2_12=now2.strftime("%I:%M %p"),
            diff=diff
        )
        await bot.send_message(uid, msg, reply_markup=kb)

        # Генерация таблицы сравнения
        table_lines = ["\n🕓 Временная таблица:"]
        for h in range(24):
            temp1 = now1.replace(hour=h, minute=0, second=0, microsecond=0)
            temp2 = temp1.astimezone(tz2)
            mark = "✅" if h == now1.hour else "  "
            day_note = ""
            if temp2.day != now1.day:
                day_note = f" ({temp2.strftime('%A')})"
            table_lines.append(f"{mark} {temp1.strftime('%H:%M')} → {temp2.strftime('%H:%M')}{day_note}")
        await bot.send_message(uid, "\n".join(table_lines))

        user_data[uid] = {"city1": city2, "city2": city1}
    except Exception as e:
        logging.exception("Ошибка при сравнении времени")
        await bot.send_message(uid, LANGS[lang]["error"])

@dp.callback_query_handler(lambda c: c.data in ["again", "switch"])
async def handle_actions(callback_query: types.CallbackQuery):
    uid = callback_query.from_user.id
    lang = user_lang.get(uid, "ru")
    last = user_data.get(uid, {"city1": None, "city2": None})
    if callback_query.data == "again":
        await bot.send_message(uid, LANGS[lang]["start"], reply_markup=make_keyboard())
        user_data[uid] = {"city1": None, "city2": None}
    elif callback_query.data == "switch":
        if last["city1"] and last["city2"]:
            await show_comparison(uid, last["city2"], last["city1"], lang)


@dp.message_handler(commands=['table'])
async def time_table(message: types.Message):
    uid = message.from_user.id
    lang = user_lang.get(uid, "ru")
    data = user_data.get(uid, {})
    city1, city2 = data.get("city1"), data.get("city2")

    if not city1 or not city2:
        await message.reply("Пожалуйста, сначала выберите два города через /start.")
        return

    tz1 = pytz.timezone(cities[city1])
    tz2 = pytz.timezone(cities[city2])
    now1 = datetime.now(tz1)
    now_hour = now1.hour
    date1 = now1.strftime("%A")

    lines = [f"🕓 Временная таблица:",
             f"{city1} ({tz1.zone}) ↔ {city2} ({tz2.zone})"]

    for h in range(24):
        local1 = now1.replace(hour=h, minute=0, second=0, microsecond=0)
        local2 = local1.astimezone(tz2)

        mark = "✅" if h == now_hour else "  "
        day_change = ""
        if local1.day != now1.day:
            day_change = f"({local1.strftime('%A')})"
        if local2.day != now1.day:
            day_change += f" → ({local2.strftime('%A')})"

        lines.append(f"{mark} {local1.strftime('%H:%M')} → {local2.strftime('%H:%M')} {day_change}".strip())

    await message.reply("\n".join(lines))


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
