FROM python:3.13.5-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt ./

# Installe toutes les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Code monté via volume, donc pas de COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
