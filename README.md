# Telegram TimeBot (Robust Version)

This Telegram bot compares current time between two selected timezones.

## Usage

1. /start - show available timezones
2. /compare <TZ1> <TZ2> - compare time between two timezones (e.g. /compare Moscow UTC+8)

## Features

- Robust error handling (global and per-command)
- ASCII-only code (no emojis)
- Hourly table in text format
- Dockerfile for reliable deployment

## Deployment on Railway

1. Push to GitHub
2. Create project on Railway (Deploy from GitHub)
3. Add environment variable:
   - API_TOKEN = <your_bot_token>
4. Railway will build and run using Dockerfile.

## Files

- bot.py
- requirements.txt
- Dockerfile
- Procfile
- runtime.txt
- README.md
