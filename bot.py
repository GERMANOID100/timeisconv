
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from datetime import datetime, timedelta
import pytz
import os

API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("❌ Переменная окружения API_TOKEN не задана")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Пользовательские данные
user_data = {}
user_lang = {}

# Города и их таймзоны
cities = {
    "Москва": "Europe/Moscow",
    "Лондон": "Europe/London",
    "Берлин": "Europe/Berlin",
    "Бали": "Asia/Makassar",
    "Минск": "Europe/Minsk",
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
    "Рио": "America/Sao_Paulo",
    "Йоханнесбург": "Africa/Johannesburg",
    "Ташкент": "Asia/Tashkent",
    "Астана": "Asia/Almaty",
    "Стамбул": "Europe/Istanbul",
    "Дели": "Asia/Kolkata"
}

# UTC пояса с временем
def generate_utc_options():
    now_utc = datetime.utcnow().replace(second=0, microsecond=0)
    buttons = []
    for offset in range(-12, 15):
        tz = pytz.FixedOffset(offset * 60)
        current = now_utc.astimezone(tz).strftime("%H:%M")
        label = f"UTC{offset:+} ({current})"
        buttons.append((label, f"UTC{offset:+}"))
    return buttons

def get_timezone(city_or_utc):
    if city_or_utc.startswith("UTC"):
        offset = int(city_or_utc.replace("UTC", ""))
        return pytz.FixedOffset(offset * 60)
    return pytz.timezone(cities[city_or_utc])

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    uid = message.from_user.id
    user_data[uid] = {"step": "mode"}
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🌆 Город", callback_data="mode_city"),
        InlineKeyboardButton("🌐 Часовой пояс", callback_data="mode_utc")
    )
    await message.answer("Выберите способ сравнения:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("mode_"))
async def mode_selected(callback: types.CallbackQuery):
    uid = callback.from_user.id
    mode = callback.data.split("_")[1]
    user_data[uid]["mode"] = mode
    user_data[uid]["city1"] = None
    user_data[uid]["city2"] = None
    user_data[uid]["page"] = 0
    await show_page(callback, uid, page=0)

async def show_page(callback, uid, page):
    mode = user_data[uid]["mode"]
    items_per_page = 6
    if mode == "city":
        items = list(cities.keys())
    else:
        items = [label for label, _ in generate_utc_options()]
    start = page * items_per_page
    end = start + items_per_page
    paginated = items[start:end]
    kb = InlineKeyboardMarkup(row_width=2)
    for label in paginated:
        kb.insert(InlineKeyboardButton(label, callback_data=label))
    nav = []
    if start > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data="prev"))
    if end < len(items):
        nav.append(InlineKeyboardButton("➡️", callback_data="next"))
    if nav:
        kb.row(*nav)
    user_data[uid]["page"] = page
    await callback.message.edit_text("Выберите первый город/пояс:" if user_data[uid]["city1"] is None else "Выберите второй:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data in list(cities.keys()) + [label for label, _ in generate_utc_options()] + ["prev", "next"])
async def handle_selection(callback: types.CallbackQuery):
    uid = callback.from_user.id
    data = user_data[uid]
    mode = data["mode"]
    items = list(cities.keys()) if mode == "city" else [label for label, _ in generate_utc_options()]
    label = callback.data

    if label == "next":
        await show_page(callback, uid, user_data[uid]["page"] + 1)
        return
    elif label == "prev":
        await show_page(callback, uid, user_data[uid]["page"] - 1)
        return

    tz_label = label.split(" ")[0] if mode == "utc" else label
    if not data["city1"]:
        data["city1"] = tz_label
        await show_page(callback, uid, 0)
    else:
        data["city2"] = tz_label
        await compare_time(callback, data["city1"], data["city2"])
        user_data[uid] = {"step": "mode"}  # сброс

async def compare_time(callback, city1, city2):
    uid = callback.from_user.id
    tz1 = get_timezone(city1)
    tz2 = get_timezone(city2)
    now = datetime.utcnow()
    now1 = pytz.utc.localize(now).astimezone(tz1)
    now2 = pytz.utc.localize(now).astimezone(tz2)

    diff_sec = int((now2 - now1).total_seconds())
    sign = "+" if diff_sec >= 0 else "-"
    h, m = divmod(abs(diff_sec), 3600)
    m = m // 60
    diff = f"{sign}{h} ч {m} мин"

    text = (
        f"🌍 Сравнение:

"
        f"{city1} — {now1.strftime('%H:%M')} ({now1.strftime('%d.%m.%Y')})
"
        f"{city2} — {now2.strftime('%H:%M')} ({now2.strftime('%d.%m.%Y')})
"
        f"Разница: {diff}

"
        f"🕓 Временная таблица:
"
    )
    for i in range(24):
        h1 = now1.replace(hour=i, minute=0)
        h2 = h1.astimezone(tz2)
        mark = "✅" if i == now1.hour else "  "
        text += f"{mark} {h1.strftime('%H:%M')} → {h2.strftime('%H:%M')}
"

    await bot.send_message(uid, text)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)



import matplotlib.pyplot as plt
import pandas as pd
import io

def generate_time_table_png(tz1, tz2, label1="Зона 1", label2="Зона 2"):
    base_time = datetime.now(tz=tz1).replace(minute=0, second=0, microsecond=0)
    current_hour = base_time.hour
    times = []

    for h in range(24):
        t1 = base_time.replace(hour=h)
        t2 = t1.astimezone(tz2)
        highlight = "✅" if h == current_hour else ""
        times.append({
            label1: t1.strftime("%H:%M"),
            label2: t2.strftime("%H:%M"),
            "": highlight
        })

    df = pd.DataFrame(times)

    fig, ax = plt.subplots(figsize=(6, 10))
    ax.axis("off")
    tbl = ax.table(cellText=df.values,
                   colLabels=df.columns,
                   cellLoc='center',
                   loc='center')
    tbl.scale(1, 1.5)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=200)
    buf.seek(0)
    return buf



from aiogram.dispatcher import filters
from aiogram.types import ParseMode
from asyncio import create_task, sleep

reminders = {}  # uid -> [(datetime, text, tz)]

@dp.message_handler(commands=['remind'])
async def set_reminder(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply("Формат: /remind 09:00 текст напоминания")
        return
    time_str, note = parts[1], parts[2]
    try:
        uid = message.from_user.id
        city = user_data.get(uid, {}).get("city1")
        if not city:
            await message.reply("Сначала выберите хотя бы один город.")
            return
        tz = get_timezone(city)
        now = datetime.now(tz)
        target_time = datetime.strptime(time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day,
            tzinfo=tz
        )
        if target_time < now:
            target_time += timedelta(days=1)
        delta = (target_time - now).total_seconds()
        await message.reply(f"⏰ Напоминание установлено на {target_time.strftime('%H:%M')} ({city})")
        create_task(schedule_reminder(uid, delta, note))
    except Exception as e:
        await message.reply("Ошибка в формате. Пример: /remind 09:00 Встреча")

async def schedule_reminder(uid, delay, note):
    await sleep(delay)
    await bot.send_message(uid, f"🔔 Напоминание: {note}")
