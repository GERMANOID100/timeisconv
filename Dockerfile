FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y gcc libffi-dev libssl-dev build-essential

# Работаем в директории /app
WORKDIR /app
COPY . /app

# Обновление pip и установка зависимостей
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Запуск бота
CMD ["python", "bot.py"]