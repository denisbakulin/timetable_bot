FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false

RUN poetry install --no-interaction --no-ansi --no-root

COPY . .

WORKDIR /app
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
# Запускаем из папки app
CMD ["python", "/app/app/main.py"]