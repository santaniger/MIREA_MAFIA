FROM python:3.11-slim
WORKDIR /app

COPY bot_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY bot_service/ ./bot_service/
COPY ../resources/ ./resources/
COPY config.py ./config.py

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot_service/bot.py"]
