FROM python:3.12-slim

WORKDIR /app

# Gereksinimler
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodu
COPY ./app ./app

# FastAPI + Uvicorn başlat
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
