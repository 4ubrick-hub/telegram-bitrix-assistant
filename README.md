# Telegram-Bitrix Assistant 🤖

Интеллектуальный Telegram чат-бот на основе Yandex AI Studio Assistant для поиска информации в документации API Bitrix24.

## Описание

Проект представляет собой умного помощника, который:
- 💬 Принимает вопросы в Telegram
- 📚 Использует локально собранную базу знаний по документации Bitrix24 API (`bitrix24_docs.md`)
- 🧠 Обрабатывает запросы через Yandex AI Studio Assistant (RAG поверх YandexGPT)
- 🕷️ Умеет самостоятельно обновлять базу знаний, обходя `apidocs.bitrix24.ru`
- 💾 Сохраняет историю диалогов в PostgreSQL

## Технологический стек

|     Компонент    |             Инструмент            |
|------------------|-----------------------------------|
| **Python**       | 3.10+                             |
| **Telegram**     | python-telegram-bot >= 22.0       |
| **LLM / RAG**    | Yandex AI Studio Assistant (YandexGPT), доступ через OpenAI-совместимый SDK |
| **Database**     | PostgreSQL 16 + SQLAlchemy 2.0    |
| **Web Scraping** | Selenium, requests + BeautifulSoup4 + markdownify |
| **Scheduler**    | APScheduler                       |
| **Container**    | Docker + Docker Compose (PostgreSQL, Redis, PgAdmin) |

## Требования

### Минимальные требования
- Python 3.10+
- PostgreSQL 12+ (либо Docker для запуска контейнера)
- Git

### Учётные данные
- Telegram Bot Token (получить у [@BotFather](https://t.me/botfather))
- Telegram Admin ID (ваш личный ID)
- Yandex Cloud API Key
- Yandex Cloud Folder ID
- ID Assistant, созданного в Yandex AI Studio
- ID Thread (диалоговой сессии) в Yandex AI Studio

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

> ⚠️ Модуль `app/assistant/client.py` работает через пакет `openai` (используется как OpenAI-совместимый клиент для Yandex AI Studio). Убедитесь, что пакет `openai` установлен — при необходимости добавьте `pip install openai` или впишите его в `requirements.txt`.

### 4. Настройка окружения

```bash
# Скопируйте .env.example в .env
cp .env.example .env

# Заполните .env своими данными
nano .env
```

#### Опционально: PostgreSQL, Redis и PgAdmin через Docker Compose

```bash
docker-compose up -d
```

Поднимет:
- PostgreSQL 16 на `localhost:5432`
- Redis на `localhost:6379`
- PgAdmin (веб-интерфейс) на `localhost:5050`

> Проверьте, что значения `POSTGRES_*` в `.env` совпадают с переменными окружения сервиса `postgres` в `docker-compose.yml` (по умолчанию в файле заданы `assistant_user` / `secure_password_123` / `bitrix_assistant`).

### 5. Инициализация базы данных

Отдельного шага с миграциями не требуется — таблицы создаются автоматически при первом запуске приложения (см. `app/database/session.py: init_db()`), который вызывается из `app/main.py`.

## Переменные окружения (.env)

| Переменная | Описание | Пример |
|------------|---------|--------|
| `TELEGRAM_BOT_TOKEN` | Token Telegram бота | `123456:ABCdefGHIjklmno` |
| `TELEGRAM_ADMIN_ID` | Ваш Telegram ID | `123456789` |
| `YANDEX_API_KEY` | API ключ Yandex Cloud | `AQVNzXr...` |
| `YANDEX_FOLDER_ID` | ID папки Yandex Cloud | `b1g4...` |
| `YANDEX_ASSISTANT_ID` | ID Assistant в Yandex AI Studio | `fvt...` |
| `YANDEX_THREAD_ID` | ID диалогового потока (thread) | `fvt...` |
| `POSTGRES_HOST` | Хост PostgreSQL | `localhost` |
| `POSTGRES_PORT` | Порт PostgreSQL | `5432` |
| `POSTGRES_DB` | Имя базы данных | `telegram_assistant` |
| `POSTGRES_USER` | Пользователь БД | `postgres` |
| `POSTGRES_PASSWORD` | Пароль БД | `password` |
| `ENABLE_PARSER` | Включить парсинг документации | `false` |
| `PARSER_INTERVAL_HOURS` | Интервал парсинга (часы) | `24` |
| `BITRIX24_DOCS_URL` | URL документации Bitrix24 | `https://apidocs.bitrix24.ru/` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `DEBUG` | Режим отладки | `false` |

## Структура проекта

```
telegram-bitrix-assistant/
├── app/
│   ├── assistant/              # Интеграция с Yandex AI Studio Assistant
│   │   ├── __init__.py
│   │   ├── client.py           # OpenAI-совместимый клиент для Yandex AI Studio
│   │   └── exceptions.py       # Исключения ассистента
│   │
│   ├── bot/                    # Telegram бот
│   │   ├── __init__.py
│   │   ├── bot.py              # Основной класс бота (TelegramBot)
│   │   ├── commands.py         # Команды бота (/start, /help, /history, /clear, /stats)
│   │   ├── handlers.py         # Обработчики входящих сообщений
│   │   └── middlewares.py      # Middleware для обработки апдейтов
│   │
│   ├── config/                 # Конфигурация приложения
│   │   ├── __init__.py
│   │   ├── logging_config.py   # Настройка логирования (консоль + logs/bot.log)
│   │   └── settings.py         # Настройки на Pydantic Settings (.env)
│   │
│   ├── core/                   # Ядро приложения
│   │   ├── __init__.py
│   │   ├── constants.py        # Константы
│   │   ├── enums.py            # Enum классы
│   │   └── exceptions.py       # Общие исключения
│   │
│   ├── database/                # Работа с БД
│   │   ├── __init__.py
│   │   ├── base.py             # Базовый declarative класс
│   │   ├── models.py           # SQLAlchemy модели (User, Message)
│   │   ├── repositories.py     # Репозитории для работы с БД
│   │   └── session.py          # Engine, сессии, init_db()
│   │
│   ├── parser/                  # Парсинг документации
│   │   ├── __init__.py
│   │   ├── crawler.py          # Краулер на Selenium (динамический контент)
│   │   ├── parser.py           # Парсинг HTML в структурированные данные
│   │   └── scheduler.py        # Планировщик периодического парсинга (APScheduler)
│   │
│   ├── services/                # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── assistant_service.py  # Обработка сообщений, история диалога
│   │   ├── parser_service.py     # Обновление базы знаний
│   │   └── user_service.py       # Статистика и данные пользователей
│   │
│   ├── utils/                   # Утилиты
│   │   ├── __init__.py
│   │   ├── helpers.py          # Вспомогательные функции
│   │   └── validators.py       # Валидаторы
│   │
│   └── main.py                  # Точка входа (Application: startup/run/shutdown)
│
├── scripts/
│   └── build_bitrix_kb.py       # Автономный сборщик базы знаний с apidocs.bitrix24.ru
│                                 # (requests + BeautifulSoup4 + markdownify → bitrix24_docs.md)
│
├── tests/
│   └── test_services_complete.py  # Unit-тесты сервисного слоя (UserService, AssistantService)
│
├── bitrix24_docs.md             # Собранная база знаний по API Bitrix24 (Markdown)
├── bitrix24_docs.state.json     # Состояние обхода для scripts/build_bitrix_kb.py --resume
│
├── logs/                        # Логи (создаётся автоматически)
├── .env.example                 # Пример переменных окружения
├── .gitignore                   # Git ignore
├── docker-compose.yml           # PostgreSQL + Redis + PgAdmin
├── requirements.txt             # Зависимости Python
└── README.md                    # Этот файл
```

## Сборка базы знаний

База знаний хранится в файле `bitrix24_docs.md` и собирается скриптом `scripts/build_bitrix_kb.py`, который обходит `https://apidocs.bitrix24.ru/`, вырезает служебную разметку (шапку, меню, футер) и конвертирует содержимое страниц в чистый Markdown (с сохранением заголовков, таблиц параметров и блоков кода).

```bash
# Полный обход документации
python scripts/build_bitrix_kb.py

# Тестовый прогон на ограниченном числе страниц
python scripts/build_bitrix_kb.py --limit 30

# Продолжить прерванный обход (используя bitrix24_docs.state.json)
python scripts/build_bitrix_kb.py --resume

# Изменить паузу между запросами
python scripts/build_bitrix_kb.py --delay 0.3
```

Готовый `bitrix24_docs.md` затем нужно загрузить в базу знаний Assistant в Yandex AI Studio (через консоль или API) — программное обновление базы знаний из `app/assistant/client.py: update_knowledge_base()` в текущей версии является заглушкой.

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

### Вариант 2: С инфраструктурой в Docker

```bash
# Поднять PostgreSQL, Redis и PgAdmin
docker-compose up -d

# Запустить приложение (таблицы создадутся автоматически)
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

## Разработка

### Запуск тестов

Зависимости для тестов (`pytest`, `pytest-asyncio`, `pytest-mock`) указаны в `requirements.txt` как опциональные — при необходимости установите их отдельно:

```bash
pip install pytest pytest-asyncio pytest-mock
```

```bash
# Все тесты
pytest

# С покрытием кода
pytest --cov=app --cov-report=html

# Конкретный файл
pytest tests/test_services_complete.py
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

## Конфигурация Yandex AI Studio Assistant

### 1. Создайте проект в Yandex Cloud

1. Перейдите на [console.yandex.cloud](https://console.yandex.cloud)
2. Создайте новый проект / каталог (folder)
3. Включите сервис Yandex AI Studio (Yandex GPT / Assistants)

### 2. Создайте API-ключ

```bash
# Через Yandex Cloud CLI
yc iam service-accounts create my-assistant-bot
yc iam keys create --service-account-name my-assistant-bot
```

### 3. Создайте Assistant и Thread

Создайте Assistant в Yandex AI Studio и загрузите в него базу знаний (`bitrix24_docs.md`), а также создайте Thread для диалоговой сессии. Полученные `YANDEX_ASSISTANT_ID` и `YANDEX_THREAD_ID` укажите в `.env`.

Взаимодействие с Assistant в проекте реализовано через OpenAI-совместимый SDK (`AsyncOpenAI` с `base_url="https://ai.api.cloud.yandex.net/v1"`), см. `app/assistant/client.py`.

## Логирование

Логи сохраняются в файл `logs/bot.log` (с ротацией по размеру, до 5 файлов по 5 МБ) и выводятся в консоль.

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

# Проверить POSTGRES_HOST / POSTGRES_PORT / POSTGRES_DB /
# POSTGRES_USER / POSTGRES_PASSWORD в .env
```

### Ошибка API Yandex

```bash
# Убедитесь, что:
# 1. YANDEX_API_KEY корректный
# 2. YANDEX_FOLDER_ID указан верно
# 3. YANDEX_ASSISTANT_ID и YANDEX_THREAD_ID существуют в Yandex AI Studio
# 4. У сервис-аккаунта есть права на использование API
# 5. Пакет openai установлен (см. раздел "Установка")
```

### Telegram бот не отвечает

```bash
# 1. Проверить TELEGRAM_BOT_TOKEN в .env
# 2. Убедиться, что приложение запущено
# 3. Посмотреть логи: tail -f logs/bot.log
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

# 6. Запустить приложение (таблицы БД создадутся автоматически)
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
