# -*- coding: utf-8 -*-
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from datetime import datetime, timedelta
import pytz

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка токена
API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    logger.error('Environment variable API_TOKEN is not set.')
    raise ValueError('API_TOKEN is not set.')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Словарь городов и их таймзон
CITIES = {
    'Moscow': 'Europe/Moscow',
    'London': 'Europe/London',
    'New_York': 'America/New_York',
    'Tokyo': 'Asia/Tokyo',
    'Sydney': 'Australia/Sydney',
    'UTC+0': 'UTC',
    'UTC+1': 'UTC+1',
    'UTC+2': 'UTC+2',
    'UTC+3': 'UTC+3',
    'UTC+4': 'UTC+4',
    'UTC+5': 'UTC+5',
    'UTC+6': 'UTC+6',
    'UTC+7': 'UTC+7',
    'UTC+8': 'UTC+8',
    'UTC+9': 'UTC+9',
    'UTC+10': 'UTC+10',
    'UTC+11': 'UTC+11',
    'UTC+12': 'UTC+12',
}

user_data = {}

# Глобальный обработчик ошибок
@dp.errors_handler()
async def global_error_handler(update, exception):
    logger.exception('Unhandled exception: %s', exception)
    return True

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    try:
        user_data[message.from_user.id] = {}
        reply = 'Available timezones: ' + ', '.join(CITIES.keys())
        await message.reply(reply)
    except Exception as e:
        logger.exception('Error in /start')
        await message.reply('Internal error, please try again later.')

@dp.message_handler(commands=['compare'])
async def cmd_compare(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.reply('Usage: /compare TZ1 TZ2')
            return
        tz1_key, tz2_key = parts[1], parts[2]
        if tz1_key not in CITIES or tz2_key not in CITIES:
            await message.reply('Unknown timezone. Use /start to see list.')
            return
        tz1 = pytz.timezone(CITIES[tz1_key])
        tz2 = pytz.timezone(CITIES[tz2_key])
        now = datetime.utcnow()
        now1 = pytz.utc.localize(now).astimezone(tz1)
        now2 = pytz.utc.localize(now).astimezone(tz2)
        diff_sec = int((now2 - now1).total_seconds())
        sign = '+' if diff_sec >= 0 else '-'
        h, m = divmod(abs(diff_sec), 3600)
        m = m // 60
        text = ('Time in {}: {}\n'
                'Time in {}: {}\n'
                'Difference: {}{}h {}m').format(
            tz1_key, now1.strftime('%H:%M'),
            tz2_key, now2.strftime('%H:%M'),
            sign, h, m
        )
        # Добавляем таблицу
        table_lines = ['\nHourly table:']
        for hour in range(24):
            t1 = now1.replace(hour=hour, minute=0, second=0)
            t2 = t1.astimezone(tz2)
            mark = '*' if hour == now1.hour else ' '
            line = '{} {:02d}:00 -> {:02d}:00'.format(mark, hour, t2.hour)
            table_lines.append(line)
        text += '\n'.join(table_lines)
        await message.reply(text)
    except Exception as e:
        logger.exception('Error in /compare')
        await message.reply('Internal error, please try again later.')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
