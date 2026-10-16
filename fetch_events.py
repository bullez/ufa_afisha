# -*- coding: utf-8 -*-
"""
Ufa Afisha — финальная версия с улучшенным парсером
"""

import os, re, json, time, logging, hashlib
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

import pytz, requests
from bs4 import BeautifulSoup

CITY = "Уфа"
TZ = pytz.timezone("Asia/Yekaterinburg")
FRESH_DAYS = int(os.getenv("FRESH_DAYS", "90"))

DATA_DIR = Path("data")
IMAGES_DIR = DATA_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CHANNELS = [
    "enter_ufa","gorod347","ufa_arteria","prostranstvoera",
    "gallerymiras","zamamuseum","vintaq_spot","kuda_go_ufa",
    "ppuummkkaaufa","ufamesto","clubmechti","lutufa",
    "kiske","dinaraveselovaa","smotrimstaroe","youlmedia",
    "asiya_arslanova","mamavaritcoffee","promoluch",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124 Safari/537.36"
}

EVENT_KEYWORDS = [
    "кино","фильм","кинопоказ","концерт","джаз","оркестр","джем","dj","вечеринк","рейв",
    "лектор","лекци","семинар","мастер-класс","воркшоп","театр","спектакл","перформанс",
    "выставк","галере","музей","арт","экскурс","киноклуб","фестиваль","маркет","стендап",
    "квиз","игра","показ","премьера","открытие","тренинг","встреча","концерт"
]
EVENT_RE = re.compile("|".join(EVENT_KEYWORDS), re.I)

URL_RE = re.compile(r"https?://[^\s)>\]]+", re.I)
DATE_TOKENS = r"(?:\b\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?|\b\d{1,2}\s+(?:янв|фев|мар|апр|мая|июн|июл|авг|сен|окт|ноя|дек|января|февраля|марта|апреля|июня|июля|августа|сентября|октября|ноября|декабря)\b)"
TIME_TOKENS = r"(?:\b[01]?\d|2[0-3])[:.]\d{2}"

MONTHS = {
    "янв":1,"января":1,"фев":2,"февраля":2,"мар":3,"марта":3,"апр":4,"апреля":4,
    "мая":5,"май":5,"июн":6,"июня":6,"июл":7,"июля":7,"авг":8,"августа":8,
    "сен":9,"сентября":9,"окт":10,"октября":10,"ноя":11,"ноября":11,"дек":12,"декабря":12
}

# Известные места Уфы
VENUE_HINTS = [
    "Арт-Квадрат", "Арт Квадрат", "Арт-КВАДРАТ", "Zaman", "Мирас", "Клуб Мечты",
    "Мама варит кофе", "Стерх", "Джаз-клуб", "Бар Муви", "Movie", "Vinoteka", "Даско",
    "Огни Уфы", "Гостиный двор", "Конгресс-холл", "Торатау", "Башкирия", "Neft",
    "Особняк", "Артерия", "Юкси Парк", "Мегаполис", "Пятница", "Правда",
    "Уфа-Арена", "Синема Парк", "Галерея Арт", "ЦКиНТ", "ДК Ядкарь",
]

def load_rules() -> dict:
    path = Path("rules.json")
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return {"title_prefixes_remove": [], "hard_exclude_words": []}

def should_exclude(text: str, rules: dict) -> bool:
    low = (text or "").lower()
    return any(w.lower() in low for w in rules.get("hard_exclude_words", []))

def clean_title(title: str, rules: dict) -> str:
    for prefix in rules.get("title_prefixes_remove", []):
        title = re.sub(rf"^{re.escape(prefix)}\s*[:,—-]?\s*", "", title, flags=re.I)
    return title.strip()

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

def sentence_case(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s

def _smart_cut(s: str, limit: int = 90) -> str:
    s = s.strip()
    if len(s) <= limit: return s
    s = s[:limit]
    s = re.sub(r"\s+\S*$", "", s)
    return s.rstrip(" ,—:;.") + "…"

def extract_datetime(text: str) -> Tuple[Optional[datetime], Optional[str], Optional[str]]:
    t = (text or "").lower()
    now = datetime.now(TZ)
    dt = None; date_str = None

    if "сегодня" in t:
        dt = now; date_str = now.strftime("%d.%m.%Y")
    elif "завтра" in t:
        dt = now + timedelta(days=1); date_str = dt.strftime("%d.%m.%Y")
    elif "послезавтра" in t:
        dt = now + timedelta(days=2); date_str = dt.strftime("%d.%m.%Y")
    elif "в эти выходные" in t or "на выходных" in t:
        # Ближайшая суббота
        days_ahead = (5 - now.weekday()) % 7
        if days_ahead == 0: days_ahead = 7
        dt = now + timedelta(days=days_ahead); date_str = dt.strftime("%d.%m.%Y")
    elif "в эту субботу" in t:
        days_ahead = (5 - now.weekday()) % 7
        if days_ahead == 0: days_ahead = 7
        dt = now + timedelta(days=days_ahead); date_str = dt.strftime("%d.%m.%Y")
    elif "в это воскресенье" in t:
        days_ahead = (6 - now.weekday()) % 7
        if days_ahead == 0: days_ahead = 7
        dt = now + timedelta(days=days_ahead); date_str = dt.strftime("%d.%m.%Y")

    if not dt:
        m = re.search(r"\b(\d{1,2})[./-](\d{1,2})(?:[./-](\d{2,4}))?\b", t)
        if m:
            d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
            y = int(y) if y else now.year
            if y < 100: y += 2000
            try:
                dt = TZ.localize(datetime(y, mo, d))
                date_str = f"{d:02d}.{mo:02d}.{y}"
            except: pass

    if not dt:
        m2 = re.search(r"\b(\d{1,2})\s+([а-яё]+)\b", t, flags=re.I)
        if m2 and m2.group(2) in MONTHS:
            d, mo = int(m2.group(1)), MONTHS[m2.group(2)]
            y = now.year
            try:
                dt = TZ.localize(datetime(y, mo, d))
                date_str = f"{d:02d}.{mo:02d}.{y}"
            except: pass

    time_str = None
    tm = re.search(r"\b([01]?\d|2[0-3])[:.](\d{2})\b", t)
    if tm:
        hh, mm = int(tm.group(1)), int(tm.group(2))
        time_str = f"{hh:02d}:{mm:02d}"
        if dt: dt = dt.replace(hour=hh, minute=mm)

    return dt, date_str, time_str

def extract_venue(text: str) -> Optional[str]:
    """
    Улучшенный парсер места:
    1) Известные места (VENUE_HINTS)
    2) Паттерн «в клубе/баре/галерее/центре/пространстве X»
    3) Адрес: «ул. X, Y», «пр. X, Y», «X, Y»
    """
    # 1. Известные
    for venue in VENUE_HINTS:
        if re.search(rf"\b{re.escape(venue)}\b", text, re.I):
            return venue

    # 2. «в клубе X», «в баре X», «в галерее X», «на площадке X»
    m = re.search(
        r"\b(?:в|на)\s+(?:клуб[еи]|бар[еи]|галере[еи]|музе[еи]|театр[еи]|центр[еи]|пространств[еи]|площадк[еи]|арен[еи]|холл[еи])\s+[«\"]?([А-ЯЁA-Z][^»\".,\n]{2,40})",
        text
    )
    if m:
        return m.group(1).strip().strip('«»"\'')

    # 3. Адрес: «ул. Ленина, 10», «пр. Октября, 67/2»
    m = re.search(
        r"\b(?:ул\.|улица|пр\.|проспект|пер\.|переулок|шоссе|бульвар)\s+[А-ЯЁA-Z][^,.\n]{2,40}(?:,\s*\d+[А-Яа-я]?)?",
        text
    )
    if m:
        return m.group(0).strip()

    # 4. Просто «X, Y» где X — название на кириллице, Y — число
    m = re.search(r"\b([А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?)\s*,\s*(\d+[А-Яа-я]?)", text)
    if m:
        return f"{m.group(1)}, {m.group(2)}"

    return None

def title_from_text(text: str) -> str:
    t = re.sub(r"@\w+", "", norm(re.sub(r"https?://\S+|#\S+", "", text or "")))
    t = re.sub(r"^(и|а|ну|вот|так)\s+", "", t, flags=re.I).strip()
    t = re.sub(r"^\W+", "", t)
    for kw in EVENT_KEYWORDS:
        m = re.search(rf"\b{kw}[^.!?\n]*", t, flags=re.I)
        if m:
            cand = m.group(0).strip(" -—.:,")
            if len(cand) >= 8:
                return sentence_case(_smart_cut(cand))
    first = re.split(r"[.!?\n]\s*", t, maxsplit=1)[0].strip(" -—.:,")
    return sentence_case(_smart_cut(first or "Событие"))

def make_desc(text: str) -> str:
    t = re.sub(r"@\w+", "", norm(re.sub(r"https?://\S+|#\S+", "", text or "")))
    parts = re.split(r"(?<=[.!?])\s+", t)
    parts = [p for p in parts if 25 <= len(p) <= 220][:2]
    out = " ".join(parts) if parts else t[:200]
    return sentence_case(out)

def price_from_text(text: str) -> Optional[str]:
    """
    Улучшенный парсер цены:
    1) Бесплатно/свободно
    2) «Стоимость: X», «Вход: X», «Билеты: X»
    3) «от X ₽», «X ₽», «X-Y ₽», «X руб»
    """
    low = (text or "").lower()

    # 1. Бесплатно
    if any(x in low for x in [
        "вход свобод", "вход бесплат", "бесплатно", "free",
        "по донату", "donation", "0₽", "0 ₽", "0 руб"
    ]):
        return "Вход свободный"

    # 2. «Стоимость: X», «Вход: X», «Билеты: X»
    m = re.search(r"(?:стоимость|вход|билет[ыа]?|цена)\s*[:\-—]?\s*([^\n.,;]{2,40})", low)
    if m:
        val = m.group(1).strip()
        # Если внутри числа с ₽/руб
        m2 = re.search(r"(\d{2,6})\s*(?:₽|р|руб)", val)
        if m2:
            return f"{m2.group(1)} ₽"
        if "бесплат" in val or "свобод" in val:
            return "Вход свободный"
        # Если есть какое-то описание — вернём как есть
        if len(val) <= 40 and not val.startswith("http"):
            return val.capitalize()

    # 3. Диапазон «X–Y ₽»
    m = re.search(r"\b(\d{2,6})\s*[-–]\s*(\d{2,6})\s*(?:₽|р|руб)\b", low)
    if m:
        return f"{m.group(1)}–{m.group(2)} ₽"

    # 4. «от X ₽»
    m = re.search(r"\bот\s*(\d{2,6})\s*(?:₽|р|руб)\b", low)
    if m:
        return f"от {m.group(1)} ₽"

    # 5. Просто «X ₽»
    m = re.search(r"\b(\d{2,6})\s*(?:₽|р|руб)\b", low)
    if m:
        return f"{m.group(1)} ₽"

    return None

def download_image(url: str, channel: str) -> Optional[str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
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
        logging.warning(f"Image download failed: {e}")
        return None

def harvest_preview(channels: List[str], rules: dict) -> List[Event]:
    out: List[Event] = []
    for ch in channels:
        count = 0
        try:
            url = f"https://t.me/s/{ch}"
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.select("div.tgme_widget_message_wrap")
            for it in items[:250]:
                tnode = it.select_one(".tgme_widget_message_text")
                text = norm(tnode.get_text("\n", strip=True) if tnode else "")
                if not text:
                    continue
                if should_exclude(text, rules):
                    continue

                dt, date_str, time_str = extract_datetime(text)
                link_node = it.select_one("a.tgme_widget_message_date")
                link = link_node.get("href") if link_node else f"https://t.me/{ch}"

                img = None
                ph = it.select_one("a.tgme_widget_message_photo_wrap") or it.select_one("a.tgme_widget_message_video_thumb")
                if ph and ph.has_attr("style"):
                    mm = re.search(r"url\(['\"]?(.*?)['\"]?\)", ph["style"])
                    if mm:
                        img = download_image(mm.group(1), ch)

                low = text.lower()
                if not (EVENT_RE.search(low) or re.search(DATE_TOKENS, low) or re.search(TIME_TOKENS, low)):
                    continue

                title = clean_title(title_from_text(text), rules)
                desc = make_desc(text)
                price = price_from_text(text)
                venue = extract_venue(text)

                ev = Event(
                    title=title, desc=desc,
                    start=dt.isoformat() if dt else None,
                    date_text=date_str, time_text=time_str,
                    city=CITY, venue=venue, price=price,
                    source=ch, source_link=link, posted_at=None,
                    raw=text, image=img, kind="event"
                )
                out.append(ev); count += 1

            logging.info(f"{ch}: +{count} items")
        except Exception as e:
            logging.warning(f"Preview failed for {ch}: {e}")
    return out

def dedupe(events: List[Event]) -> List[Event]:
    out = []; seen = set()
    for e in events:
        key = (e.title.lower()[:60], e.date_text or "", e.source)
        if key in seen: continue
        seen.add(key); out.append(e)
    return out

def save_outputs(events: List[Event]):
    DATA_DIR.mkdir(exist_ok=True)
    payload = [asdict(e) for e in events]
    (DATA_DIR / "events.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    Path("events.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    logging.info(f"Saved {len(events)} events")

def run_once():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    rules = load_rules()
    logging.info(f"Harvest. Channels: {len(DEFAULT_CHANNELS)}")
    items = harvest_preview(DEFAULT_CHANNELS, rules)
    items = dedupe(items)
    save_outputs(items)

if __name__ == "__main__":
    run_once()
