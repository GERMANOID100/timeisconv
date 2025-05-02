# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    raise ValueError("API_TOKEN is not set")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    help_text = (
        "TimeCompareBot\n\n"
        "This bot compares current time between two time zones.\n\n"
        "Usage:\n"
        "/compare <TZ1> <TZ2>\n\n"
        "Example:\n"
        "/compare Europe/Moscow Asia/Tokyo\n\n"
        "List of time zones: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
    )
    await message.reply(help_text)

@dp.message_handler(commands=['compare'])
async def cmd_compare(message: types.Message):
    args = message.get_args().split()
    if len(args) != 2:
        await message.reply("Please use: /compare <TZ1> <TZ2>")
        return

    tz1_name, tz2_name = args
    try:
        tz1 = pytz.timezone(tz1_name)
        tz2 = pytz.timezone(tz2_name)
    except Exception:
        await message.reply(
            "Unknown time zone. Use IANA names like:
Europe/Moscow
Asia/Tokyo"
        )
        return

    now_utc = datetime.utcnow()
    now1 = pytz.utc.localize(now_utc).astimezone(tz1)
    now2 = pytz.utc.localize(now_utc).astimezone(tz2)

    delta_seconds = int((now2 - now1).total_seconds())
    sign = '+' if delta_seconds >= 0 else '-'
    h, remainder = divmod(abs(delta_seconds), 3600)
    m = remainder // 60

    reply = (
        f"Time in {tz1_name}: {now1.strftime('%Y-%m-%d %H:%M')}\n"
        f"Time in {tz2_name}: {now2.strftime('%Y-%m-%d %H:%M')}\n"
        f"Difference: {sign}{h}h {m}m"
    )
    await message.reply(reply)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
