import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from pytz import timezone
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN не задан")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

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
    'Минск (UTC+3)': 'Europe/Minsk',
    'Киев (UTC+3)': 'Europe/Kyiv',
    'Москва (UTC+3)': 'Europe/Moscow',
    'Дубай (UTC+4)': 'Asia/Dubai',
    'Исламабад (UTC+5)': 'Asia/Karachi',
    'Дакка (UTC+6)': 'Asia/Dhaka',
    'Бангкок (UTC+7)': 'Asia/Bangkok',
    'Бали (UTC+8)': 'Asia/Makassar',
    'Сингапур (UTC+8)': 'Asia/Singapore',
    'Токио (UTC+9)': 'Asia/Tokyo',
    'Сидней (UTC+10)': 'Australia/Sydney',
    'Соломоновы острова (UTC+11)': 'Pacific/Guadalcanal',
    'Окленд (UTC+12)': 'Pacific/Auckland',
    'Тонга (UTC+13)': 'Pacific/Tongatapu',
    'Острова Лайн (UTC+14)': 'Pacific/Kiritimati',
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
    try:
        city2 = callback.data.split("|", 1)[1]
        data = user_selection.get(callback.from_user.id, {})
        city1 = data.get("city1")
        if not city1 or city1 not in cities or city2 not in cities:
            await callback.message.answer("Ошибка. Выбор города некорректен.")
            return

        tz1 = cities[city1]
        tz2 = cities[city2]

        logger.info(f"Сравнение: {city1} ({tz1}) vs {city2} ({tz2})")

        # Текущий день
        today = datetime.now(timezone(tz1)).strftime('%A')

        # Заголовки
        header = f"{today}\n\n{city1:<20} | {city2}"
        separator = "-" * (len(header))

        # Таблица по 24 часам
        rows = []
        now_utc = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        current_hour = datetime.now().astimezone(timezone(tz1)).hour

        for hour in range(24):
            time_utc = now_utc.replace(hour=hour)
            local1 = time_utc.astimezone(timezone(tz1)).strftime('%H:%M')
            local2 = time_utc.astimezone(timezone(tz2)).strftime('%H:%M')
            marker = "←" if hour == current_hour else "  "
            rows.append(f"{local1:<7} | {local2:<7} {marker}")

        table = "\n".join(rows)
        text = f"{header}\n{separator}\n{table}"

        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Сравнить снова", callback_data="restart")
        )

        await callback.message.edit_text(text, reply_markup=kb)
    except Exception as e:
        logger.exception("Ошибка при сравнении городов")
        await callback.message.answer("Произошла ошибка при сравнении. Попробуйте ещё раз.")

@dp.callback_query_handler(lambda c: c.data == "restart")
async def restart(callback: types.CallbackQuery):
    await start(callback.message)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
