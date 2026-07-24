"""
Скрипт сборки базы знаний по документации Bitrix24 REST API.

Обходит сайт https://apidocs.bitrix24.ru/, извлекает текст документации
и сохраняет его в единый Markdown-файл (bitrix24_docs.md) для дальнейшего
использования в RAG-контуре Yandex Assistant.

Что исправлено по сравнению со старой версией скрипта:
    1. Кракозябра вместо кириллицы.
       requests не всегда умеет правильно определить кодировку страницы
       по заголовкам ответа и по умолчанию откатывается на ISO-8859-1.
       Из-за этого r.text возвращал битую строку. Здесь кодировка
       всегда фиксируется как UTF-8 явно.
    2. Дублирующийся мусор на каждой странице.
       Шапка, подвал, левое меню навигации и правый блок "на этой
       странице" раньше попадали в текст каждой страницы, из-за чего
       база знаний на 90% состояла из одного и того же меню,
       повторенного сотни раз. Теперь эти блоки вырезаются, а из
       оставшегося содержимого вытаскивается только основной контент.
    3. Отсутствие структуры.
       Раньше страница превращалась в один сплошной "суп" из текста
       без заголовков, кода и таблиц. Теперь HTML конвертируется в
       нормальный Markdown (заголовки, списки, таблицы, блоки кода
       с указанием языка) — это критично для методов API, где смысл
       часто зависит от таблицы параметров и примера кода.
    4. Отсутствие устойчивости к сбоям.
       Обход сотен страниц может прерваться (обрыв сети, таймаут,
       бан по частоте запросов). Скрипт теперь пишет результат
       постранично и сохраняет состояние обхода, поэтому его можно
       прервать и продолжить с помощью --resume, не начиная заново.
    5. Уважение robots.txt.
       Скрипт проверяет robots.txt и пропускает страницы, закрытые
       для роботов, вместо того чтобы вслепую их скачивать.
    6. Битые относительные ссылки внутри текста.
       Ссылки в HTML почти всегда относительные ("/api-reference/...").
       Вне контекста сайта такая ссылка никуда не ведёт. Теперь все
       href приводятся к абсолютному виду через urljoin() до конвертации
       в markdown.
    7. Задвоенный текст в подзаголовках страниц.
       Diplodoc (движок apidocs.bitrix24.ru) кладёт рядом с каждым
       заголовком скрытую самоссылку на его же якорь, из-за чего в
       markdown заголовок превращался в "## [Текст](url#anchor)Текст".
       Теперь такой дубль схлопывается в обычный "## Текст".

Запуск:
    python scripts/build_bitrix_kb.py                  # полный обход
    python scripts/build_bitrix_kb.py --limit 30        # тестовый прогон
    python scripts/build_bitrix_kb.py --resume          # продолжить обход
    python scripts/build_bitrix_kb.py --delay 0.3       # ускорить/замедлить

Зависимости (уже есть в requirements.txt проекта, кроме markdownify):
    requests, beautifulsoup4, markdownify
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import time
import urllib.robotparser as robotparser
from collections import deque
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

# ---------------------------------------------------------------------------
# Конфигурация
# ---------------------------------------------------------------------------

BASE_URL = "https://apidocs.bitrix24.ru/"
START_URL = BASE_URL

OUTPUT_FILE = Path("bitrix24_docs.md")
STATE_FILE = Path("bitrix24_docs.state.json")

MAX_PAGES = 3000
REQUEST_TIMEOUT = 20
REQUEST_DELAY = 0.5          # пауза между запросами, секунды (вежливый обход)
MAX_RETRIES = 3
USER_AGENT = (
    "Bitrix24-KB-Builder/2.0 "
    "(+https://github.com/your-username/telegram-bitrix-assistant; "
    "educational project, telegram bot knowledge base crawler)"
)

# Разделы сайта, которые не являются документацией и не нужны в базе знаний
EXCLUDED_PATH_PREFIXES = (
    "/_images/",
    "/_assets/",
    "/_bundles/",
    "/search/",
)

# Расширения файлов, которые точно не HTML-страницы
EXCLUDED_EXTENSIONS = (
    ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
    ".pdf", ".zip", ".rar", ".css", ".js", ".json", ".xml",
    ".woff", ".woff2", ".ttf", ".mp4",
)

# Внешние хосты, которые попадаются в ссылках, но не относятся к документации
EXCLUDED_HOST_KEYWORDS = ("t.me", "github.com", "vibecode.bitrix24")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("build_bitrix_kb")


# ---------------------------------------------------------------------------
# Markdown-конвертер
# ---------------------------------------------------------------------------

class DocsMarkdownConverter(MarkdownConverter):
    """
    Конвертер HTML -> Markdown, настроенный под доки Bitrix24.

    - не экранирует спецсимволы (текст читают люди и модель, а не
      рендерят обратно в HTML, лишние \\* и \\_ только мешают);
    - сохраняет язык программирования в блоках кода, если он указан
      через class="language-xxx" (обычная разметка для примеров кода
      на PHP/JS/cURL/C# в документации Bitrix24);
    - не сохраняет изображения как base64/ссылки — для текстовой базы
      знаний они бесполезны и только раздувают файл.
    """

    class Options(MarkdownConverter.DefaultOptions):
        heading_style = "ATX"
        bullets = "-"
        escape_asterisks = False
        escape_underscores = False
        strip = ["img"]

    def convert_pre(self, el, text, parent_tags):
        code_el = el.find("code")
        lang = ""
        if code_el and code_el.get("class"):
            for cls in code_el.get("class"):
                if cls.startswith("language-"):
                    lang = cls.removeprefix("language-")
                    break
        code_text = code_el.get_text() if code_el else el.get_text()
        code_text = code_text.strip("\n")
        return f"\n```{lang}\n{code_text}\n```\n"


def html_to_markdown(html_fragment) -> str:
    return DocsMarkdownConverter().convert_soup(html_fragment)


# ---------------------------------------------------------------------------
# Извлечение содержимого страницы
# ---------------------------------------------------------------------------

# Именно в таком порядке пробуем найти основной блок с содержимым статьи.
# Сайт построен на Diplodoc, у него нет единого стабильного идентификатора
# для всех типов страниц, поэтому перебираем несколько правдоподобных
# вариантов и берём первый непустой результат.
CONTENT_SELECTORS = (
    "article",
    "main",
    "[class*='yfm']",
    "[class*='dc-doc-page']",
    "[class*='DocPage']",
    "[role='main']",
    ".content",
    "#main-content",
)

# Блоки, которые всегда выбрасываем, даже если они оказались внутри
# найденного контейнера с контентом
STRIP_TAGS = (
    "script", "style", "noscript", "header", "footer", "nav", "aside",
    "svg", "iframe", "form", "button",
)
STRIP_CLASS_KEYWORDS = (
    "breadcrumb", "toc", "sidebar", "pagination", "feedback",
    "on-this-page", "edit-page", "cookie",
)


def extract_title(soup: BeautifulSoup, url: str) -> str:
    if soup.title and soup.title.text.strip():
        raw = soup.title.text.strip()
        # заголовки вида "Название метода | REST API Битрикс24 и ..."
        # общий хвост после "|" одинаковый на всех страницах и не нужен
        return raw.split("|")[0].strip()
    return url


def extract_content(soup: BeautifulSoup, page_url: str) -> str:
    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    for tag in soup.find_all(class_=True):
        if tag.decomposed:
            continue
        classes = " ".join(tag.get("class", [])).lower()
        if any(kw in classes for kw in STRIP_CLASS_KEYWORDS):
            tag.decompose()

    container = None
    for selector in CONTENT_SELECTORS:
        found = soup.select(selector)
        # берём самый крупный по объёму текста контейнер из найденных,
        # чтобы не зацепить какой-нибудь маленький служебный <main>
        found = [f for f in found if len(f.get_text(strip=True)) > 100]
        if found:
            container = max(found, key=lambda f: len(f.get_text(strip=True)))
            break

    if container is None:
        container = soup.body or soup

    # ссылки в исходном HTML почти всегда относительные (например,
    # "/api-reference/crm/index.html" или "files/how-to-upload-files.html").
    # Вне контекста сайта такая ссылка ведёт в никуда, поэтому здесь мы
    # приводим все href к абсолютному виду относительно текущей страницы.
    for a in container.find_all("a", href=True):
        a["href"] = urljoin(page_url, a["href"])

    markdown = html_to_markdown(container)
    return clean_markdown(markdown)


def clean_markdown(text: str) -> str:
    text = text.replace("\xa0", " ")
    # Diplodoc (движок apidocs.bitrix24.ru) рядом с каждым заголовком
    # рендерит скрытую для скринридеров самоссылку на якорь этого же
    # заголовка. При конвертации в markdown это превращается в
    # "## [Текст](url#anchor)Текст" — заголовок дублируется целиком.
    # Схлопываем такую пару в обычный заголовок "## Текст".
    text = re.sub(
        r"^(#{1,6}) \[([^\]]+)\]\([^)]*#[^)]*\)\s*\2",
        r"\1 \2",
        text,
        flags=re.MULTILINE,
    )
    # убираем более двух пустых строк подряд
    text = re.sub(r"\n{3,}", "\n\n", text)
    # убираем пробелы в конце строк
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.strip()


# ---------------------------------------------------------------------------
# Обход сайта
# ---------------------------------------------------------------------------

def normalize_url(url: str) -> str | None:
    url, _ = urldefrag(url)  # убираем #якорь
    url = url.split("?")[0]  # убираем query-параметры (дубли контента)

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    if "apidocs.bitrix24.ru" not in parsed.netloc:
        return None
    if any(kw in parsed.netloc for kw in EXCLUDED_HOST_KEYWORDS):
        return None
    if any(parsed.path.startswith(p) for p in EXCLUDED_PATH_PREFIXES):
        return None
    if parsed.path.lower().endswith(EXCLUDED_EXTENSIONS):
        return None

    if not url.endswith("/"):
        pass  # страницы вида .../index.html или .../method-name.html — ок

    return url


def extract_links(soup: BeautifulSoup, page_url: str) -> set[str]:
    links = set()
    for a in soup.find_all("a", href=True):
        full = urljoin(page_url, a["href"])
        normalized = normalize_url(full)
        if normalized:
            links.add(normalized)
    return links


def fetch(session: requests.Session, url: str) -> requests.Response | None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            # ключевой момент: явно фиксируем UTF-8, а не гадаем по
            # заголовкам, которые сервер может не прислать корректно
            response.encoding = "utf-8"
            if response.status_code == 200:
                return response
            if response.status_code == 404:
                logger.warning("404: %s", url)
                return None
            logger.warning(
                "HTTP %s на попытке %d/%d: %s",
                response.status_code, attempt, MAX_RETRIES, url,
            )
        except requests.RequestException as exc:
            logger.warning(
                "Ошибка сети на попытке %d/%d (%s): %s",
                attempt, MAX_RETRIES, url, exc,
            )
        time.sleep(1.5 * attempt)
    logger.error("Не удалось загрузить страницу после %d попыток: %s", MAX_RETRIES, url)
    return None


# ---------------------------------------------------------------------------
# Состояние обхода (для --resume)
# ---------------------------------------------------------------------------

def load_state() -> tuple[set[str], deque[str]]:
    if not STATE_FILE.exists():
        return set(), deque([START_URL])
    data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return set(data["visited"]), deque(data["queue"])


def save_state(visited: set[str], queue: deque[str]) -> None:
    STATE_FILE.write_text(
        json.dumps(
            {"visited": sorted(visited), "queue": list(queue)},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Основной цикл
# ---------------------------------------------------------------------------

def build_knowledge_base(
    limit: int = MAX_PAGES,
    delay: float = REQUEST_DELAY,
    resume: bool = False,
) -> None:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    robots = robotparser.RobotFileParser()
    robots.set_url(urljoin(BASE_URL, "/robots.txt"))
    try:
        robots.read()
    except Exception:
        logger.warning("Не удалось прочитать robots.txt, продолжаю без него")
        robots = None

    if resume and STATE_FILE.exists():
        visited, queue = load_state()
        logger.info(
            "Продолжаю обход: уже посещено %d страниц, в очереди %d",
            len(visited), len(queue),
        )
        out_mode = "a"
    else:
        visited, queue = set(), deque([START_URL])
        out_mode = "w"
        if OUTPUT_FILE.exists():
            OUTPUT_FILE.unlink()

    saved_count = 0
    skipped_count = 0

    with OUTPUT_FILE.open(out_mode, encoding="utf-8") as out:
        while queue and len(visited) < limit:
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)

            if robots is not None and not robots.can_fetch(USER_AGENT, url):
                logger.info("Пропуск (запрещено robots.txt): %s", url)
                skipped_count += 1
                continue

            logger.info("[%d/%d] %s", len(visited), limit, url)

            response = fetch(session, url)
            if response is None:
                skipped_count += 1
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # ссылки собираем до того, как вырежем nav/footer из супа
            for link in extract_links(soup, url):
                if link not in visited:
                    queue.append(link)

            title = extract_title(soup, url)
            content = extract_content(soup, url)

            if len(content) < 30:
                logger.info("Пропуск (пустая страница): %s", url)
                skipped_count += 1
                continue

            out.write(f"## {title}\n")
            out.write(f"Источник: {url}\n\n")
            out.write(content)
            out.write("\n\n---\n\n")
            out.flush()
            saved_count += 1

            if saved_count % 25 == 0:
                save_state(visited, queue)

            time.sleep(delay)

    save_state(visited, queue)

    logger.info("=" * 60)
    logger.info("Готово")
    logger.info("Страниц сохранено: %d", saved_count)
    logger.info("Страниц пропущено: %d", skipped_count)
    logger.info("Всего посещено: %d", len(visited))
    logger.info("Файл: %s", OUTPUT_FILE.resolve())
    logger.info("=" * 60)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit", type=int, default=MAX_PAGES,
        help="максимальное число страниц для обхода (по умолчанию без ограничения на практике)",
    )
    parser.add_argument(
        "--delay", type=float, default=REQUEST_DELAY,
        help="пауза между запросами в секундах (вежливость к серверу)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="продолжить прерванный обход вместо того, чтобы начинать заново",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_knowledge_base(limit=args.limit, delay=args.delay, resume=args.resume)
