# Telegram бот (bot.py)
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . /app/bot_service/

# Настройка переменных окружения
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot_service/bot.py"]