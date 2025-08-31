# Система рассылок сообщений

Веб-приложение Django для управления рассылками сообщений клиентам.

## Функциональность

- **Управление клиентами**: создание, редактирование, удаление клиентов
- **Управление пользователями**: регистрация, аутентификация, управление профилями
- **Управление рассылками**: создание, редактирование, удаление рассылок
- **Планирование**: настройка времени начала и окончания рассылок
- **Частота отправки**: однократно, ежедневно, еженедельно, ежемесячно
- **Статусы рассылок**: черновик, активна, приостановлена, завершена
- **Отслеживание**: логирование всех отправленных сообщений
- **Асинхронная отправка**: использование Celery для фоновых задач
- **Веб-интерфейс**: современный UI на Bootstrap 5.

## Технологии

- **Backend**: Django 4.2.7
- **Frontend**: Bootstrap 5, Bootstrap Icons
- **База данных**: SQLite (для разработки), PostgreSQL (для продакшена)
- **Очереди задач**: Celery + Redis
- **Формы**: Django Crispy Forms

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd web-app
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Настройки email (для разработки используется консольный бэкенд)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Настройки Celery (Redis)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 5. Установка и настройка Redis

**Windows:**
Скачайте Redis для Windows с [GitHub](https://github.com/microsoftarchive/redis/releases)

**Linux:**
```bash
sudo apt-get install redis-server
```

**Mac:**
```bash
brew install redis
```

### 6. Применение миграций

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Создание суперпользователя

```bash
python manage.py createsuperuser
```

### 8. Запуск серверов

**Терминал 1 - Django сервер:**
```bash
python manage.py runserver
```

**Терминал 2 - Redis:**
```bash
redis-server
```

**Терминал 3 - Celery worker:**
```bash
celery -A mailing_system worker -l info
```

**Терминал 4 - Celery beat (для планировщика):**
```bash
celery -A mailing_system beat -l info
```

### 9. Доступ к приложению

- **Веб-интерфейс**: http://127.0.0.1:8000/
- **Админ-панель**: http://127.0.0.1:8000/admin/

## Структура проекта

```
web-app/
├── mailing_system/          # Основной проект Django
│   ├── __init__.py
│   ├── settings.py         # Настройки проекта
│   ├── urls.py             # Главные URL-маршруты
│   ├── wsgi.py             # WSGI конфигурация
│   ├── asgi.py             # ASGI конфигурация
│   └── celery.py           # Конфигурация Celery
├── mailings/               # Приложение рассылок
│   ├── __init__.py
│   ├── admin.py            # Админ-панель
│   ├── apps.py             # Конфигурация приложения
│   ├── forms.py            # Формы
│   ├── models.py           # Модели данных
│   ├── tasks.py            # Задачи Celery
│   ├── urls.py             # URL-маршруты приложения
│   └── views.py            # Представления
├── templates/              # Шаблоны
│   ├── base.html           # Базовый шаблон
│   └── mailings/           # Шаблоны приложения
├── manage.py               # Управление Django
├── requirements.txt        # Зависимости
└── README.md              # Документация
```

## Модели данных

### Client (Клиент)
- `email` - Email адрес
- `full_name` - Полное имя
- `phone` - Номер телефона
- `comment` - Комментарий
- `created_at` - Дата создания
- `updated_at` - Дата обновления

### Mailing (Рассылка)
- `title` - Название рассылки
- `subject` - Тема письма
- `message` - Текст сообщения
- `clients` - Связанные клиенты (ManyToMany)
- `start_time` - Время начала
- `end_time` - Время окончания
- `frequency` - Частота (once, daily, weekly, monthly)
- `status` - Статус (draft, active, paused, completed)
- `created_by` - Создатель (ForeignKey к User)
- `created_at` - Дата создания
- `updated_at` - Дата обновления

### Message (Сообщение)
- `mailing` - Связанная рассылка
- `client` - Связанный клиент
- `status` - Статус (pending, sent, failed)
- `sent_at` - Время отправки
- `error_message` - Сообщение об ошибке
- `created_at` - Дата создания

### MailingLog (Лог рассылки)
- `mailing` - Связанная рассылка
- `message` - Текст сообщения
- `level` - Уровень (INFO, ERROR, WARNING)
- `created_at` - Дата создания

## Использование

### 1. Регистрация и вход
- Зарегистрируйтесь на странице `/register/`
- Войдите в систему

### 2. Добавление клиентов
- Перейдите в раздел "Клиенты"
- Нажмите "Добавить клиента"
- Заполните форму и сохраните

### 3. Создание рассылки
- Перейдите в раздел "Рассылки"
- Нажмите "Создать рассылку"
- Заполните все поля:
  - Название и тема
  - Текст сообщения
  - Выберите клиентов
  - Установите время начала и окончания
  - Выберите частоту и статус

### 4. Управление рассылками
- Просматривайте список рассылок
- Фильтруйте по статусу и частоте
- Редактируйте или удаляйте рассылки
- Просматривайте детальную информацию

### 5. Отслеживание
- Просматривайте отправленные сообщения
- Изучайте логи рассылок
- Анализируйте статистику на дашборде

## Настройка email

Для продакшена настройте SMTP сервер в `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

## Развертывание

### Docker (рекомендуется)

Создайте `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### Docker Compose

Создайте `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - db
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/mailings
      - REDIS_URL=redis://redis:6379/0

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=mailings
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Лицензия

MIT License

## Поддержка

При возникновении проблем создайте issue в репозитории проекта. 