# API-сервер (server.py)
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . /app/server_service/

# Настройка переменных окружения
ENV FLASK_APP=server_service/server.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Порт для Flask
EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]