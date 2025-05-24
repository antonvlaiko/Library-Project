FROM python:3.11

# Робоча директорія в контейнері
WORKDIR /app

# Копіюємо залежності
COPY requirements.txt .

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо проєкт
COPY . .

# Змінні середовища
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Запускаємо сервер
CMD ["python", "manage.py", "runserver", "128.192.0.0:8000"]
