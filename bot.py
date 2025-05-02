import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from pytz import all_timezones, timezone
from datetime import datetime

API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# Отбираем города в формате "Region/City"
cities = [tz for tz in all_timezones if '/' in tz and not tz.startswith('Etc/')]

# Параметры пагинации
PAGE_SIZE = 8
user_state = {}

def get_time_info(tz_name):
    now = datetime.now(timezone(tz_name))
    utc_offset = now.utcoffset().total_seconds() / 3600
    return now.strftime('%H:%M:%S %d.%m.%Y'), int(utc_offset)

def get_city_keyboard(page, prefix):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    kb = InlineKeyboardMarkup(row_width=2)
    for city in cities[start:end]:
        kb.insert(InlineKeyboardButton(city, callback_data=f"{prefix}_{city}"))
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⏪ Назад", callback_data=f"{prefix}_page_{page-1}"))
    if end < len(cities):
        nav_buttons.append(InlineKeyboardButton("Вперёд ⏩", callback_data=f"{prefix}_page_{page+1}"))
    if nav_buttons:
        kb.row(*nav_buttons)
    return kb

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_state[message.from_user.id] = {"step": "city1", "page": 0}
    kb = get_city_keyboard(0, "city1")
    await message.answer("Выберите первый город:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("city1_page_"))
async def paginate_city1(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
    user_state[callback.from_user.id]["page"] = page
    kb = get_city_keyboard(page, "city1")
    await callback.message.edit_reply_markup(reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("city1_") and "page" not in c.data)
async def select_city1(callback: types.CallbackQuery):
    city1 = callback.data.split("_", 1)[1]
    user_state[callback.from_user.id] = {"city1": city1, "step": "city2", "page": 0}
    kb = get_city_keyboard(0, "city2")
    await callback.message.edit_text(f"Первый город: {city1}\nТеперь выберите второй город:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("city2_page_"))
async def paginate_city2(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
    user_state[callback.from_user.id]["page"] = page
    kb = get_city_keyboard(page, "city2")
    await callback.message.edit_reply_markup(reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("city2_") and "page" not in c.data)
async def select_city2(callback: types.CallbackQuery):
    city2 = callback.data.split("_", 1)[1]
    data = user_state.get(callback.from_user.id, {})
    city1 = data.get("city1")
    if not city1:
        await callback.message.answer("Ошибка. Начните сначала: /start")
        return
    time1, offset1 = get_time_info(city1)
    time2, offset2 = get_time_info(city2)
    diff = abs(offset1 - offset2)
    diff_str = f"{int(diff)} ч." if diff.is_integer() else f"{diff:.1f} ч."
    text = (
        f"🕒 {city1} (UTC{offset1:+}): {time1}\n"
        f"🕒 {city2} (UTC{offset2:+}): {time2}\n"
        f"📍Разница: {diff_str}"
    )
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Повторить сравнение", callback_data="restart"),
    )
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "restart")
async def restart(callback: types.CallbackQuery):
    await start(callback.message)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)