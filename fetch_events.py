# -*- coding: utf-8 -*-
"""
Ufa Afisha — Улучшенная версия с умной очисткой и дедупликацией
"""
import os, re, json, logging, hashlib
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import pytz, requests
from bs4 import BeautifulSoup

CITY = "Уфа"
TZ = pytz.timezone("Asia/Yekaterinburg")
DATA_DIR = Path("data")
IMAGES_DIR = DATA_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
}

# Ключевые слова для поиска событий
EVENT_KEYWORDS = [
    "кино", "фильм", "кинопоказ", "концерт", "джаз", "оркестр", "джем", "dj", "вечеринк", "рейв",
    "лектор", "лекци", "семинар", "мастер-класс", "воркшоп", "театр", "спектакл", "перформанс",
    "выставк", "галере", "музей", "арт", "экскурс", "киноклуб", "фестиваль", "маркет", "стендап",
    "квиз", "игра", "показ", "премьера", "открытие", "тренинг", "встреча"
]

# Категории событий и их ключевые слова
CATEGORIES = {
    "concert": ["концерт", "джаз", "оркестр", "джем", "dj", "выступлен", "группа", "певец", "певица", "бэнд"],
    "party": ["вечеринк", "рейв", "дискотек", "пати", "afterparty", "афтепати"],
    "cinema": ["кино", "фильм", "кинопоказ", "премьера", "киноклуб", "кинофестиваль"],
    "theater": ["театр", "спектакл", "перформанс", "драма", "комедия", "мюзикл"],
    "lecture": ["лекци", "семинар", "воркшоп", "мастер-класс", "тренинг", "встреча с", "дискуссия"],
    "exhibition": ["выставк", "галере", "музей", "экспозиц", "экскурс", "вернисаж"],
    "market": ["маркет", "ярмарк", "фуд-маркет", "фудмаркет"],
    "festival": ["фестиваль", "фест"],
    "standup": ["стендап", "комик", "юмор"],
    "quiz": ["квиз", "викторин", "интеллектуальн"]
}

def detect_category(text: str) -> str:
    """Определяет категорию события по ключевым словам"""
    low = (text or "").lower()
    scores = {}
    for cat, keywords in CATEGORIES.items():
        score = sum(1 for kw in keywords if kw in low)
        if score > 0:
            scores[cat] = score
    
    if not scores:
        return "other"
    
    # Возвращаем категорию с наибольшим количеством совпадений
    return max(scores, key=scores.get)
EVENT_RE = re.compile("|".join(EVENT_KEYWORDS), re.I)
DATE_TOKENS = r"(?:\b\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?|\b\d{1,2}\s+(?:янв|фев|мар|апр|мая|июн|июл|авг|сен|окт|ноя|дек|января|февраля|марта|апреля|июня|июля|августа|сентября|октября|ноября|декабря)\b)"
TIME_TOKENS = r"(?:\b[01]?\d|2[0-3])[:.]\d{2}"
MONTHS = {
    "янв": 1, "января": 1, "фев": 2, "февраля": 2, "мар": 3, "марта": 3, "апр": 4, "апреля": 4,
    "мая": 5, "май": 5, "июн": 6, "июня": 6, "июл": 7, "июля": 7, "авг": 8, "августа": 8,
    "сен": 9, "сентября": 9, "окт": 10, "октября": 10, "ноя": 11, "ноября": 11, "дек": 12, "декабря": 12
}

VENUE_HINTS = [
    "Арт-Квадрат", "Zaman", "Мирас", "Клуб Мечты", "Мама варит кофе", "Стерх", "Джаз-клуб", 
    "Бар Муви", "Movie", "Vinoteka", "Даско", "Огни Уфы", "Гостиный двор", "Конгресс-холл", 
    "Торатау", "Башкирия", "Neft", "Особняк", "Артерия", "Юкси Парк", "Мегаполис", "Пятница", 
    "Правда", "Уфа-Арена", "Синема Парк", "Галерея Арт", "ЦКиНТ", "ДК Ядкарь"
]

def load_json_file(filename: str, default):
    """Универсальная функция для чтения JSON файлов"""
    path = Path(filename)
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return default

def should_exclude(text: str, rules: dict) -> bool:
    low = (text or "").lower()
    return any(w.lower() in low for w in rules.get("hard_exclude_words", []))

def normalize_venue(venue: Optional[str], rules: dict) -> Optional[str]:
    """Приводит названия мест к единому красивому виду"""
    if not venue: return None
    low_venue = venue.lower().strip()
    # Проверяем синонимы из rules.json
    for bad_name, good_name in rules.get("venue_synonyms", {}).items():
        if bad_name in low_venue:
            return good_name
    return venue

@dataclass
class Event:
    title: str
    desc: Optional[str]
    start: Optional[str]
    date_text: Optional[str]
    time_text: Optional[str]
    city: str
    venue: Optional[str]
    price: Optional[str]
    source: str
    source_link: str
    posted_at: Optional[str]
    raw: str
    image: Optional[str] = None
    kind: str = "event"

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()

def extract_datetime(text: str) -> Tuple[Optional[datetime], Optional[str], Optional[str]]:
    t = (text or "").lower()
    now = datetime.now(TZ)
    dt = None; date_str = None
    
    if "сегодня" in t:
        dt = now; date_str = now.strftime("%d.%m.%Y")
    elif "завтра" in t:
        dt = now + timedelta(days=1); date_str = dt.strftime("%d.%m.%Y")
    
    # Упрощенный, но надежный поиск дат вида "20 декабря" или "20.12"
    if not dt:
        m2 = re.search(r"\b(\d{1,2})\s+([а-яё]+)\b", t, flags=re.I)
        if m2 and m2.group(2) in MONTHS:
            d, mo = int(m2.group(1)), MONTHS[m2.group(2)]
            try:
                dt = TZ.localize(datetime(now.year, mo, d))
                date_str = f"{d:02d}.{mo:02d}.{now.year}"
            except: pass
            
    time_str = None
    tm = re.search(r"\b([01]?\d|2[0-3])[:.](\d{2})\b", t)
    if tm:
        hh, mm = int(tm.group(1)), int(tm.group(2))
        time_str = f"{hh:02d}:{mm:02d}"
        if dt: dt = dt.replace(hour=hh, minute=mm)
        
    return dt, date_str, time_str

def extract_venue(text: str, rules: dict) -> Optional[str]:
    for venue in VENUE_HINTS:
        if re.search(rf"\b{re.escape(venue)}\b", text, re.I):
            return normalize_venue(venue, rules)
    
    m = re.search(r"\b(?:ул\.|улица|пр\.|проспект|пер\.|переулок)\s+[А-ЯЁA-Z][^,.n]{2,40}", text)
    if m:
        return m.group(0).strip()
    return None

def price_from_text(text: str) -> Optional[str]:
    low = (text or "").lower()
    if any(x in low for x in ["вход свобод", "вход бесплат", "бесплатно", "free", "0₽", "0 руб"]):
        return "Вход свободный"
    
    m = re.search(r"\b(\d{2,6})\s*(?:₽|р|руб)\b", low)
    if m:
        return f"{m.group(1)} ₽"
    return None

def download_image(url: str, channel: str) -> Optional[str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        ext = ".jpg"
        for e in (".png", ".webp", ".jpeg", ".jpg"):
            if e in url.lower(): ext = e; break
        h = hashlib.md5(url.encode()).hexdigest()[:10]
        fname = f"{channel}_{h}{ext}"
        path = IMAGES_DIR / fname
        path.write_bytes(r.content)
        return f"data/images/{fname}"
    except Exception as e:
        return None

def harvest_preview(channels: List[str], rules: dict) -> List[Event]:
    out: List[Event] = []
    for ch in channels:
        try:
            url = f"https://t.me/s/{ch}"
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.select("div.tgme_widget_message_wrap")
            
            for it in items[:100]: # Берем последние 100 постов канала
                tnode = it.select_one(".tgme_widget_message_text")
                text = norm(tnode.get_text("\n", strip=True) if tnode else "")
                if not text or should_exclude(text, rules):
                    continue
                
                dt, date_str, time_str = extract_datetime(text)
                link_node = it.select_one("a.tgme_widget_message_date")
                link = link_node.get("href") if link_node else f"https://t.me/{ch}"
                
                # Проверка на наличие ключевых слов события
                low = text.lower()
                if not (EVENT_RE.search(low) or re.search(DATE_TOKENS, low)):
                    continue
                
                img = None
                ph = it.select_one("a.tgme_widget_message_photo_wrap")
                if ph and ph.has_attr("style"):
                    mm = re.search(r"url\(['\"]?(.*?)['\"]?\)", ph["style"])
                    if mm:
                        img = download_image(mm.group(1), ch)
                
                venue = extract_venue(text, rules)
                
                # Простая очистка заголовка
                title = text.split('\n')[0].strip()
                if len(title) > 80: title = title[:77] + "..."
                
                ev = Event(
                    title=title, desc=text[:200],
                    start=dt.isoformat() if dt else None,
                    date_text=date_str, time_text=time_str,
                    city=CITY, venue=venue, price=price_from_text(text),
                    source=ch, source_link=link, posted_at=None,
                    raw=text, image=img, kind=detect_category(text)
                )
                out.append(ev)
        except Exception as e:
            logging.warning(f"Ошибка канала {ch}: {e}")
    return out

def smart_deduplicate(events: List[Event]) -> List[Event]:
    """Умное удаление дубликатов: объединяет одинаковые события из разных каналов"""
    unique_events = {}
    
    for ev in events:
        # Создаем "отпечаток" события: нормализованное название + дата + место
        fingerprint = (
            re.sub(r'[^\w\s]', '', ev.title.lower())[:40], 
            ev.date_text or "", 
            ev.venue or "unknown"
        )
        
        # Если такого события еще нет, или у текущего источника более длинное (полезное) описание
        if fingerprint not in unique_events:
            unique_events[fingerprint] = ev
        else:
            existing = unique_events[fingerprint]
            # Объединяем источники, чтобы видеть, кто еще писал об этом
            if ev.source not in existing.source:
                existing.source += f", {ev.source}"
            # Если у нового события есть картинка, а у старого нет - заменяем картинку
            if ev.image and not existing.image:
                existing.image = ev.image
                
    return list(unique_events.values())

def cleanup_unused_images(events: List[Event]):
    """Удаляет старые картинки, которые больше не нужны, чтобы не раздувать репозиторий"""
    existing_images = set(p.name for p in IMAGES_DIR.glob("*") if p.is_file())
    used_images = set(ev.image.replace("data/images/", "") for ev in events if ev.image)
    
    to_delete = existing_images - used_images
    for img_name in to_delete:
        try:
            (IMAGES_DIR / img_name).unlink()
        except Exception:
            pass

def save_outputs(events: List[Event]):
    DATA_DIR.mkdir(exist_ok=True)
    payload = [asdict(e) for e in events]
    
    # Сохраняем в двух местах для совместимости
    (DATA_DIR / "events.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    Path("events.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    logging.info(f"Успешно сохранено {len(events)} уникальных событий.")

def run_once():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    
    # 1. Загружаем настройки из простых файлов
    channels = load_json_file("channels.json", [])
    rules = load_json_file("rules.json", {"hard_exclude_words": [], "venue_synonyms": {}})
    
    if not channels:
        logging.error("Файл channels.json пуст или не найден!")
        return

    logging.info(f"Начинаем сбор данных из {len(channels)} каналов...")
    
    # 2. Собираем данные
    items = harvest_preview(channels, rules)
    logging.info(f"Собрано сырых событий: {len(items)}")
    
    # 3. Удаляем дубликаты
    items = smart_deduplicate(items)
    logging.info(f"После удаления дубликатов осталось: {len(items)}")
    
    # 4. Чистим старые картинки
    cleanup_unused_images(items)
    
    # 5. Сохраняем результат
    save_outputs(items)

if __name__ == "__main__":
    run_once()
