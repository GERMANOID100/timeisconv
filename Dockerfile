FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y libglib2.0-0 libsm6 libxrender1 libxext6 \
 && pip install --upgrade pip \
 && pip install -r requirements.txt

CMD ["python", "bot.py"]