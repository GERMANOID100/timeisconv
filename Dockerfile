FROM python:3.10-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y build-essential gcc libffi-dev libssl-dev

# Копируем проект
COPY . /app

# Устанавливаем зависимости
RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["python", "bot.py"]