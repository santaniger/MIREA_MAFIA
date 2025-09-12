FROM python:3.11-slim
WORKDIR /app

COPY server_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код сервера
COPY server_service/ ./server_service/
# Копируем общий конфиг
COPY config.py ./config.py

ENV FLASK_APP=server_service.server
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
