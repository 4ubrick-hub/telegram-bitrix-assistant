# Telegram-Bitrix Assistant 🤖

Интеллектуальный Telegram чат-бот на основе Yandex Assistant для поиска информации в документации API Bitrix24.

## Описание

Проект представляет собой умного помощника, который:
- 💬 Принимает вопросы в Telegram
- 🔍 Парсит документацию Bitrix24 API
- 🧠 Использует Yandex Assistant для обработки запросов
- 📚 Выдаёт точные ответы на основе базы знаний
- 💾 Сохраняет историю диалогов в PostgreSQL

## Технологический стек

|     Компонент    |             Инструмент            |
|------------------|-----------------------------------|
| **Python**       | 3.10+                             |
| **Telegram**     | python-telegram-bot 21.7          |
| **LLM**          | Yandex Assistant (Yandex GPT 3.5) |
| **Database**     | PostgreSQL 16 + SQLAlchemy        |
| **Web Scraping** | Selenium + BeautifulSoup4         |
| **Scheduler**    | APScheduler                       |
| **Container**    | Docker + Docker Compose           |

## Требования

### Минимальные требования
- Python 3.10+
- PostgreSQL 12+
- Git

### Учётные данные
- Telegram Bot Token (получить у [@BotFather](https://t.me/botfather))
- Yandex Cloud API Key (для доступа к Yandex Assistant)
- Telegram Admin ID (ваш личный ID)

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/telegram-bitrix-assistant.git
cd telegram-bitrix-assistant
```

### 2. Создание виртуального окружения

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка окружения

#### Вариант A: Локальная PostgreSQL

```bash
# Скопируйте .env.example в .env
cp .env.example .env

# Отредактируйте .env с вашими данными
nano .env
```

#### Вариант B: Docker Compose

```bash
# Просто запустите контейнеры
docker-compose up -d

# Убедитесь, что DATABASE_URL в .env:
# postgresql+asyncpg://assistant_user:secure_password_123@localhost:5432/bitrix_assistant
```

### 5. Инициализация базы данных

```bash
# Создание миграций Alembic
alembic upgrade head
```

## Переменные окружения (.env)

| Переменная | Описание | Пример |
|------------|---------|--------|
| `TELEGRAM_BOT_TOKEN` | Token Telegram бота | `123456:ABCdefGHIjklmno` |
| `TELEGRAM_ADMIN_ID` | Ваш Telegram ID | `123456789` |
| `DATABASE_URL` | URL подключения к БД | `postgresql+asyncpg://user:pass@localhost/db` |
| `YANDEX_API_KEY` | API ключ Yandex Cloud | `AQVNzXr...` |
| `YANDEX_FOLDER_ID` | ID папки Yandex Cloud | `b1g4...` |
| `ENABLE_PARSER` | Включить парсинг документации | `True` |
| `PARSER_INTERVAL_HOURS` | Интервал парсинга (часы) | `24` |
| `BITRIX24_DOCS_URL` | URL документации Bitrix24 | `https://apidocs.bitrix24.ru/` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `DEBUG` | Режим отладки | `False` |

## Структура проекта

```
telegram-bitrix-assistant/
├── app/
│   ├── assistant/           # Интеграция с Yandex Assistant
│   │   ├── __init__.py
│   │   ├── client.py        # Клиент для работы с ассистентом
│   │   └── exceptions.py    # Исключения ассистента
│   │
│   ├── bot/                 # Telegram бот
│   │   ├── __init__.py
│   │   ├── bot.py           # Основной класс бота
│   │   ├── commands.py      # Команды бота
│   │   ├── handlers.py      # Обработчики сообщений
│   │   └── middlewares.py   # Middleware для обработки
│   │
│   ├── config/              # Конфигурация приложения
│   │   ├── __init__.py
│   │   ├── logging_config.py # Настройка логирования
│   │   └── settings.py      # Основные настройки
│   │
│   ├── core/                # Ядро приложения
│   │   ├── __init__.py
│   │   ├── constants.py     # Константы
│   │   ├── enums.py         # Enum классы
│   │   └── exceptions.py    # Общие исключения
│   │
│   ├── database/            # Работа с БД
│   │   ├── __init__.py
│   │   ├── base.py          # Базовые классы
│   │   ├── crud.py          # CRUD операции
│   │   ├── models.py        # SQLAlchemy модели
│   │   ├── repositories.py  # Репозитории
│   │   └── session.py       # Управление сессиями
│   │
│   ├── parser/              # Парсинг документации
│   │   ├── __init__.py
│   │   ├── crawler.py       # Краулер для Selenium
│   │   ├── parser.py        # Парсер HTML
│   │   └── scheduler.py     # Планировщик парсинга
│   │
│   ├── services/            # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── assistant_service.py
│   │   ├── parser_service.py
│   │   └── user_service.py
│   │
│   ├── utils/               # Утилиты
│   │   ├── __init__.py
│   │   ├── helpers.py       # Вспомогательные функции
│   │   └── validators.py    # Валидаторы
│   │
│   └── main.py              # Точка входа
│
├── alembic/                 # Миграции БД
│   ├── versions/
│   ├── env.py
│   ├── script.py.mako
│   └── alembic.ini
│
├── tests/                   # Тесты
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_assistant_service.py
│   ├── test_parser_service.py
│   ├── test_user_service.py
│   ├── test_validators.py
│   └── test_handlers.py
│
├── logs/                    # Логи (создаётся автоматически)
├── .env.example             # Пример переменных окружения
├── .gitignore               # Git ignore
├── docker-compose.yml       # Docker Compose конфиг
├── requirements.txt         # Зависимости Python
└── README.md               # Этот файл
```

## Запуск приложения

### Вариант 1: Локальный запуск

```bash
# Активировать виртуальное окружение
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows

# Запустить приложение
python -m app.main
```

### Вариант 2: Docker Compose

```bash
# Запустить все контейнеры (PostgreSQL, Redis, PgAdmin)
docker-compose up -d

# Убедиться, что БД инициализирована
# Применить миграции
alembic upgrade head

# Запустить приложение
python -m app.main
```

## Использование бота

### Основные команды

| Команда | Описание |
|---------|---------|
| `/start` | Начать работу с ботом |
| `/help` | Помощь и список команд |
| `/history` | Показать историю диалога |
| `/clear` | Очистить историю |
| `/stats` | Статистика использования |

### Пример диалога

```
👤 Вы: Как создать контакт через API?

🤖 Ассистент: Для создания контакта используйте метод crm.contact.add.
Пример запроса:
POST /rest/1/crm.contact.add

{
  "fields": {
    "NAME": "Иван",
    "LAST_NAME": "Иванов",
    "PHONE": [{"VALUE": "+79991234567"}]
  }
}

Больше информации: https://apidocs.bitrix24.ru/api-reference/crm/contacts/...
```

## API Endpoints

### Telegram Bot API

Бот работает через Telegram Bot API и Webhook/Polling.

**Поддерживаемые сообщения:**
- Текстовые сообщения
- Команды (`/command`)
- Inline queries (для встроенного поиска)

## Разработка

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием кода
pytest --cov=app --cov-report=html

# Конкретный тест
pytest tests/test_validators.py::test_validate_telegram_id
```

### Форматирование кода

```bash
# Black
black app/ tests/

# isort
isort app/ tests/

# Flake8
flake8 app/ tests/

# MyPy
mypy app/
```

### Создание миграций БД

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Add new column"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1
```

## Конфигурация Yandex Assistant

### 1. Создайте проект в Yandex Cloud

1. Перейдите на [console.yandex.cloud](https://console.yandex.cloud)
2. Создайте новый проект
3. Включите API "Yandex GPT" и "Assistants"

### 2. Создайте API ключ

```bash
# Через Yandex Cloud CLI
yc iam service-accounts create my-assistant-bot
yc iam keys create --service-account-name my-assistant-bot
```

### 3. Создайте Assistant

API для создания assistant можно найти в документации Yandex Cloud.

## Логирование

Логи сохраняются в файл `logs/app.log` и выводятся в консоль.

### Уровни логирования

| Уровень | Описание |
|---------|---------|
| `DEBUG` | Детальная информация для диагностики |
| `INFO` | Общая информация о ходе работы |
| `WARNING` | Предупреждения (потенциальные проблемы) |
| `ERROR` | Ошибки |
| `CRITICAL` | Критические ошибки |

Пример логов:
```
[2026-07-08 10:30:45] INFO     🚀 Запуск приложения...
[2026-07-08 10:30:46] INFO     Инициализация базы данных...
[2026-07-08 10:30:47] INFO     ✅ База данных инициализирована
[2026-07-08 10:30:48] INFO     Инициализация Telegram бота...
```

## Решение проблем

### Ошибка подключения к БД

```bash
# Проверить, запущена ли PostgreSQL
# Windows
pg_isready -h localhost -p 5432

# Linux
sudo systemctl status postgresql

# Проверить DATABASE_URL в .env
```

### Ошибка API Yandex

```bash
# Убедитесь, что:
# 1. API ключ корректный
# 2. Folder ID правильный
# 3. У сервис-аккаунта есть права на использование API
```

### Telegram бот не отвечает

```bash
# 1. Проверить token в .env
# 2. Убедиться, что приложение запущено
# 3. Посмотреть логи: tail -f logs/app.log
```

## Развёртывание

### На VPS (Ubuntu 22.04)

```bash
# 1. Установить зависимости
sudo apt update
sudo apt install python3.10 python3.10-venv postgresql postgresql-contrib git

# 2. Клонировать репозиторий
git clone <repository-url>
cd telegram-bitrix-assistant

# 3. Создать виртуальное окружение
python3.10 -m venv venv
source venv/bin/activate

# 4. Установить зависимости
pip install -r requirements.txt

# 5. Создать .env файл
cp .env.example .env
# Отредактировать .env

# 6. Инициализировать БД
alembic upgrade head

# 7. Запустить как service (или использовать systemd)
nohup python -m app.main > logs/app.log 2>&1 &
```

### С использованием systemd

Создайте файл `/etc/systemd/system/bitrix-assistant.service`:

```ini
[Unit]
Description=Telegram Bitrix Assistant Bot
After=network.target postgresql.service

[Service]
Type=simple
User=assistant
WorkingDirectory=/home/assistant/telegram-bitrix-assistant
Environment="PATH=/home/assistant/telegram-bitrix-assistant/venv/bin"
ExecStart=/home/assistant/telegram-bitrix-assistant/venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bitrix-assistant
sudo systemctl start bitrix-assistant
```
