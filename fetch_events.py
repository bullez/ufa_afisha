# -*- coding: utf-8 -*-
"""
Ufa Afisha v3 — сбор из Telegram + LLM-экстракция + Supabase.

Работает в трёх режимах автоматически:
  - Есть все ключи  -> LLM + база Supabase (полный режим)
  - Только Supabase -> регэкспы + база
  - Нет ключей      -> как раньше: регэкспы + локальный events.json
"""
import os, re, json, time, hashlib, logging
from dataclasses import dataclass, asdict, fields
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple
import pytz, requests
from bs4 import BeautifulSoup

# ───────────────────────── Настройки ─────────────────────────
CITY = "Уфа"
TZ = pytz.timezone("Asia/Yekaterinburg")
DATA_DIR = Path("data")
IMAGES_DIR = DATA_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

ROLLOVER_DAYS = 14      # дата «ушла» в прошлое дальше N дней = следующий год
CHANNEL_PAUSE = 1.5     # пауза между каналами, сек
LLM_MAX_POSTS = int(os.environ.get("LLM_MAX_POSTS") or 40)  # лимит LLM-запросов за запуск

SUPABASE_URL = os.environ.get("SUPABASE_URL") or ""
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or ""
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY") or ""
LLM_BASE_URL = os.environ.get("LLM_BASE_URL") or "https://openrouter.ai/api/v1"
LLM_MODEL = os.environ.get("LLM_MODEL") or "deepseek/deepseek-chat-v3.1:free"

sb = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logging.warning(f"Supabase не подключился: {e}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124 Safari/537.36"
}
EVENT_KEYWORDS = [
    "кино","фильм","кинопоказ","концерт","джаз","оркестр","джем","dj","вечеринк","рейв",
    "лектор","лекци","семинар","мастер-класс","воркшоп","театр","спектакл","перформанс",
    "выставк","галере","музей","арт","экскурс","киноклуб","фестиваль","маркет","стендап",
    "квиз","премьера","открытие","тренинг"
]
EVENT_RE = re.compile("|".join(EVENT_KEYWORDS), re.I)
CATEGORIES = {
    "concert": ["концерт","джаз","оркестр","джем","dj","выступлен","группа","певец","певица","бэнд"],
    "party": ["вечеринк","рейв","дискотек","пати","afterparty","афтепати"],
    "cinema": ["кино","фильм","кинопоказ","премьера","киноклуб","кинофестиваль"],
    "theater": ["театр","спектакл","перформанс","драма","комедия","мюзикл"],
    "lecture": ["лекци","семинар","воркшоп","мастер-класс","тренинг","встреча с","дискуссия"],
    "exhibition": ["выставк","галере","музей","экспозиц","экскурс","вернисаж"],
    "market": ["маркет","ярмарк","фуд-маркет","фудмаркет"],
    "festival": ["фестиваль","фест"],
    "standup": ["стендап","комик","юмор"],
    "quiz": ["квиз","викторин","интеллектуальн"]
}
DATE_TOKENS = r"(?:\b\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?|\b\d{1,2}\s+(?:янв|фев|мар|апр|мая|июн|июл|авг|сен|окт|ноя|дек|января|февраля|марта|апреля|июня|июля|августа|сентября|октября|ноября|декабря)\b)"
TIME_TOKENS = r"(?:\b[01]?\d|2[0-3])[:.]\d{2}"
MONTHS = {
    "янв":1,"января":1,"фев":2,"февраля":2,"мар":3,"марта":3,"апр":4,"апреля":4,
    "мая":5,"май":5,"июн":6,"июня":6,"июл":7,"июля":7,"авг":8,"августа":8,
    "сен":9,"сентября":9,"окт":10,"октября":10,"ноя":11,"ноября":11,"дек":12,"декабря":12
}
VENUE_HINTS = [
    "Арт-Квадрат", "Арт Квадрат", "Арт-КВАДРАТ", "Zaman", "Мирас", "Клуб Мечты",
    "Мама варит кофе", "Стерх", "Джаз-клуб", "Бар Муви", "Movie", "Vinoteka", "Даско",
    "Огни Уфы", "Гостиный двор", "Конгресс-холл", "Торатау", "Башкирия", "Neft",
    "Особняк", "Артерия", "Юкси Парк", "Мегаполис", "Пятница", "Правда",
    "Уфа-Арена", "Синема Парк", "Галерея Арт", "ЦКиНТ", "ДК Ядкарь",
    "Биатлонка", "Соты", "Тинькофф", "Сбер", "Амадеус", "Гастробар", "Лофт",
    "Кэмп", "Camp", "Кэмп", "Monkey Grinder", "Шкапских", "Мира", "Монумент",
]
NON_EVENT_MARKERS = [
    "реклама", "erid", "ооо", "инн", "подпишись", "подписывайтесь",
    "розыгрыш", "конкурс", "приз", "giveaway",
    "итоги", "результаты", "запись эфира", "смотрите на",
    "фотоотчёт", "фотоотчет", "как это было",
    "спасибо всем", "благодарим",
]

LLM_SYSTEM_PROMPT = """Ты извлекаешь информацию о событиях города Уфа из постов Telegram-каналов.
Тебе дают текст поста и сегодняшнюю дату. Верни СТРОГО JSON без каких-либо пояснений, по схеме:
{
  "is_event": true или false,
  "title": "короткое название события, до 80 символов",
  "date": "YYYY-MM-DD" или null,
  "time": "HH:MM" или null,
  "venue": "название площадки" или null,
  "price": "цена ('Вход свободный', 'от 500 ₽', '300–500 ₽')" или null,
  "category": "concert|party|cinema|theater|lecture|exhibition|market|festival|standup|quiz|other",
  "confidence": число от 0 до 1 — насколько ты уверен, что это анонс события
}
Правила:
- НЕ выдумывай ничего. Нет данных в тексте — ставь null.
- Реклама, итоги, фотоотчёты, розыгрыши, подписки -> is_event=false
- Относительные даты («сегодня», «завтра», «в субботу», «на выходных») считай от сегодняшней даты.
- Если даты нет вообще, но событие явно анонсируется — is_event=true, date=null.
"""

# ───────────────────────── Утилиты ─────────────────────────
def load_json_file(filename: str, default):
    path = Path(filename)
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return default

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

def fetch_with_retry(url: str, retries: int = 3, timeout: int = 20) -> requests.Response:
    """Повторы с паузами при ошибках сети и 429."""
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code in (429, 502, 503):
                wait = 5 * (attempt + 1)
                logging.warning(f"HTTP {r.status_code} от {url}, ждём {wait}с")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last_exc = e
            time.sleep(3 * (attempt + 1))
    raise last_exc if last_exc else RuntimeError(f"fetch failed: {url}")

# ───────────────────────── LLM-экстракция ─────────────────────────
def llm_extract(text: str, today: str) -> Optional[dict]:
    """Отправляет пост в LLM, получает структурированный JSON."""
    if not OPENROUTER_KEY:
        return None
    try:
        r = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Сегодня: {today}\n\nПост:\n{text[:3000]}"},
                ],
                "temperature": 0.1,
                "max_tokens": 400,
            },
            timeout=40,
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^```(json)?\s*|\s*```$", "", content, flags=re.M).strip()
        data = json.loads(content)
        if not data.get("is_event"):
            return None
        return data
    except Exception as e:
        logging.warning(f"LLM extract failed: {e}")
        return None
    finally:
        time.sleep(0.4)  # не душим бесплатный тариф

def event_from_llm(d: dict, text: str, ch: str, link: str, img: Optional[str]) -> Optional[Event]:
    try:
        date_iso = d.get("date")
        time_s = d.get("time")
        start = None; date_text = None
        if date_iso:
            y, m, dd = (int(x) for x in str(date_iso).split("-"))
            hh, mm = 0, 0
            if time_s and ":" in str(time_s):
                pp = str(time_s).split(":"); hh, mm = int(pp[0]), int(pp[1])
            start = TZ.localize(datetime(y, m, dd, hh, mm)).isoformat()
            date_text = f"{dd:02d}.{m:02d}.{y}"
        cat = d.get("category") or "other"
        if cat not in CATEGORIES: cat = "other"
        return Event(
            title=(d.get("title") or "Событие")[:90],
            desc=make_desc(text),
            start=start, date_text=date_text,
            time_text=(str(time_s) if time_s else None),
            city=CITY, venue=d.get("venue"), price=d.get("price"),
            source=ch, source_link=link, posted_at=None,
            raw=text, image=img, kind=cat, category=cat,
            confidence=float(d.get("confidence") or 0.8),
        )
    except Exception as e:
        logging.warning(f"event_from_llm failed: {e}")
        return None

# ───────────────────────── Регэксп-фолбэк (старая логика) ─────────────────────────
def detect_category(text: str) -> str:
    low = (text or "").lower()
    scores = {}
    for cat, keywords in CATEGORIES.items():
        score = sum(1 for kw in keywords if kw in low)
        if score > 0:
            scores[cat] = score
    if not scores:
        return "other"
    return max(scores, key=scores.get)

def should_exclude(text: str, rules: dict) -> bool:
    low = (text or "").lower()
    if any(w.lower() in low for w in rules.get("hard_exclude_words", [])):
        return True
    if any(w.lower() in low for w in NON_EVENT_MARKERS):
        return True
    return False

def clean_title(title: str, rules: dict) -> str:
    for prefix in rules.get("title_prefixes_remove", []):
        title = re.sub(rf"^{re.escape(prefix)}\s*[:,—-]?\s*", "", title, flags=re.I)
    return title.strip()

def normalize_venue(venue: Optional[str], rules: dict) -> Optional[str]:
    if not venue: return None
    low_venue = venue.lower().strip()
    for bad_name, good_name in rules.get("venue_synonyms", {}).items():
        if bad_name.lower() in low_venue:
            return good_name
    return venue

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
            year_explicit = y is not None
            y = int(y) if y else now.year
            if y < 100: y += 2000
            try:
                dt = TZ.localize(datetime(y, mo, d))
                if not year_explicit and dt < now - timedelta(days=ROLLOVER_DAYS):
                    dt = TZ.localize(datetime(y + 1, mo, d))
                date_str = dt.strftime("%d.%m.%Y")
            except ValueError:
                pass
    if not dt:
        m2 = re.search(r"\b(\d{1,2})\s+([а-яё]+)\b", t, flags=re.I)
        if m2 and m2.group(2) in MONTHS:
            d, mo = int(m2.group(1)), MONTHS[m2.group(2)]
            y = now.year
            try:
                dt = TZ.localize(datetime(y, mo, d))
                if dt < now - timedelta(days=ROLLOVER_DAYS):
                    dt = TZ.localize(datetime(y + 1, mo, d))
                date_str = dt.strftime("%d.%m.%Y")
            except ValueError:
                pass
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
    m = re.search(
        r"\b(?:в|на)\s+(?:клуб[еи]|бар[еи]|галере[еи]|музе[еи]|театр[еи]|центр[еи]|пространств[еи]|площадк[еи]|арен[еи]|холл[еи])\s+[«\"]?([А-ЯЁA-Z][^»\".,\n]{2,40})",
        text
    )
    if m:
        return normalize_venue(m.group(1).strip().strip('«»"\''), rules)
    m = re.search(
        r"\b(?:ул\.|улица|пр\.|проспект|пер\.|переулок|шоссе|бульвар)\s+[А-ЯЁA-Z][^,.\n]{2,40}(?:,\s*\d+[А-Яа-я]?)?",
        text
    )
    if m:
        return m.group(0).strip()
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
    low = (text or "").lower()
    if any(x in low for x in [
        "вход свобод", "вход бесплат", "бесплатно", "free",
        "по донату", "donation", "0₽", "0 ₽", "0 руб"
    ]):
        return "Вход свободный"
    m = re.search(r"(?:стоимость|вход|билет[ыа]?|цена)\s*[:\-—]?\s*([^\n.,;]{2,40})", low)
    if m:
        val = m.group(1).strip()
        m2 = re.search(r"(\d{2,6})\s*(?:₽|р|руб)", val)
        if m2:
            return f"{m2.group(1)} ₽"
        if "бесплат" in val or "свобод" in val:
            return "Вход свободный"
        if len(val) <= 40 and not val.startswith("http"):
            return val.capitalize()
    m = re.search(r"\b(\d{2,6})\s*[-–]\s*(\d{2,6})\s*(?:₽|р|руб)\b", low)
    if m:
        return f"{m.group(1)}–{m.group(2)} ₽"
    m = re.search(r"\bот\s*(\d{2,6})\s*(?:₽|р|руб)\b", low)
    if m:
        return f"от {m.group(1)} ₽"
    m = re.search(r"\b(\d{2,6})\s*(?:₽|р|руб)\b", low)
    if m:
        return f"{m.group(1)} ₽"
    return None

# ───────────────────────── Модель данных ─────────────────────────
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
    kind: str = "other"
    category: str = "other"
    first_seen: Optional[str] = None
    confidence: float = 0.0

EVENT_FIELDS = {f.name for f in fields(Event)}

def dict_to_event(e: dict) -> Optional[Event]:
    if not isinstance(e, dict):
        return None
    if not e.get("title") or not e.get("source_link"):
        return None
    try:
        return Event(**{k: e.get(k) for k in EVENT_FIELDS})
    except TypeError:
        return None

def row_to_event(r: dict) -> Event:
    """Строка из Supabase -> объект Event."""
    cat = r.get("category") or "other"
    return Event(
        title=r.get("title") or "Событие",
        desc=r.get("descr"),
        start=r.get("start_at"),
        date_text=r.get("date_text"),
        time_text=r.get("time_text"),
        city=r.get("city") or CITY,
        venue=r.get("venue"),
        price=r.get("price"),
        source=r.get("source") or "",
        source_link=r.get("source_link") or "",
        posted_at=None,
        raw=r.get("raw") or "",
        image=r.get("image"),
        kind=cat, category=cat,
        first_seen=r.get("first_seen"),
        confidence=float(r.get("confidence") or 0),
    )

def is_past(date_text: Optional[str], time_text: Optional[str] = None) -> bool:
    """True, если событие уже прошло (учитываем время)."""
    if not date_text:
        return False
    try:
        parts = date_text.split(".")
        if len(parts) == 3:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            hh, mm = 23, 59
            if time_text and ":" in time_text:
                pp = time_text.split(":")
                hh, mm = int(pp[0]), int(pp[1])
            event_dt = TZ.localize(datetime(y, m, d, hh, mm))
            return event_dt < datetime.now(TZ)
    except (ValueError, TypeError):
        pass
    return False

# ───────────────────────── Картинки ─────────────────────────
def upload_image_to_storage(path: Path) -> Optional[str]:
    """Кладёт картинку в Supabase Storage, возвращает публичный URL."""
    if not sb:
        return None
    try:
        bts = path.read_bytes()
        sb.storage.from_("images").upload(path.name, bts,
            {"content-type": "image/jpeg", "upsert": "true"})
        return sb.storage.from_("images").get_public_url(path.name)
    except Exception as e:
        logging.warning(f"Storage upload failed: {e}")
        return None

def download_image(url: str, channel: str) -> Optional[str]:
    try:
        r = fetch_with_retry(url, retries=2, timeout=15)
        ext = ".jpg"
        for e in (".png", ".webp", ".jpeg", ".jpg"):
            if e in url.lower(): ext = e; break
        h = hashlib.md5(url.encode()).hexdigest()[:10]
        fname = f"{channel}_{h}{ext}"
        path = IMAGES_DIR / fname
        path.write_bytes(r.content)
        pub = upload_image_to_storage(path)   # если база подключена — в облако
        return pub or f"data/images/{fname}"
    except Exception as e:
        logging.warning(f"Image download failed: {e}")
        return None

# ───────────────────────── Supabase ─────────────────────────
def db_id(source_link: str) -> str:
    return hashlib.md5((source_link or "").encode()).hexdigest()

def upsert_events_db(events: List[Event]):
    rows = []
    for ev in events:
        rows.append({
            "id": db_id(ev.source_link),
            "title": ev.title, "descr": ev.desc,
            "start_at": ev.start, "date_text": ev.date_text,
            "time_text": ev.time_text, "city": ev.city,
            "venue": ev.venue, "price": ev.price,
            "category": ev.category, "source": ev.source,
            "source_link": ev.source_link, "image": ev.image,
            "raw": ev.raw, "confidence": ev.confidence,
            "last_seen": datetime.now(TZ).isoformat(),
        })
    for i in range(0, len(rows), 50):  # пачками по 50
        sb.table("events").upsert(rows[i:i+50]).execute()
    logging.info(f"DB: upserted {len(rows)} events")

def purge_old_db():
    """Удаляем события, которые прошли больше 3 дней назад."""
    cutoff = (datetime.now(TZ) - timedelta(days=3)).isoformat()
    try:
        sb.table("events").delete().lt("start_at", cutoff).execute()
    except Exception as e:
        logging.warning(f"purge failed: {e}")

def load_future_from_db() -> List[dict]:
    now_iso = datetime.now(TZ).isoformat()
    res = (sb.table("events")
             .select("*")
             .eq("status", "published")
             .or_(f"start_at.gte.{now_iso},start_at.is.null")
             .execute())
    return res.data or []

# ───────────────────────── Сбор постов ─────────────────────────
def harvest_preview(channels: List[str], rules: dict) -> List[Event]:
    out: List[Event] = []
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    llm_used = 0
    for ch in channels:
        count = 0
        try:
            url = f"https://t.me/s/{ch}"
            r = fetch_with_retry(url)
            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.select("div.tgme_widget_message_wrap")
            for it in items[:100]:
                tnode = it.select_one(".tgme_widget_message_text")
                text = norm(tnode.get_text("\n", strip=True) if tnode else "")
                if not text or should_exclude(text, rules):
                    continue
                low = text.lower()
                if not EVENT_RE.search(low):
                    continue
                if not (re.search(DATE_TOKENS, low) or re.search(TIME_TOKENS, low)):
                    continue
                link_node = it.select_one("a.tgme_widget_message_date")
                link = link_node.get("href") if link_node else f"https://t.me/{ch}"
                img = None
                ph = it.select_one("a.tgme_widget_message_photo_wrap") or it.select_one("a.tgme_widget_message_video_thumb")
                if ph and ph.has_attr("style"):
                    mm = re.search(r"url\(['\"]?(.*?)['\"]?\)", ph["style"])
                    if mm:
                        img = download_image(mm.group(1), ch)
                ev = None
                # 1) пробуем LLM (лимит за запуск, чтобы не упереться в free-тариф)
                if llm_used < LLM_MAX_POSTS:
                    data = llm_extract(text, today)
                    if data:
                        llm_used += 1
                        ev = event_from_llm(data, text, ch, link, img)
                # 2) фолбэк — старые добрые регэкспы
                if ev is None:
                    dt, date_str, time_str = extract_datetime(text)
                    ev = Event(
                        title=clean_title(title_from_text(text), rules),
                        desc=make_desc(text),
                        start=dt.isoformat() if dt else None,
                        date_text=date_str, time_text=time_str,
                        city=CITY, venue=extract_venue(text, rules),
                        price=price_from_text(text),
                        source=ch, source_link=link, posted_at=None,
                        raw=text, image=img,
                        kind=detect_category(text), category=detect_category(text),
                        confidence=0.4,
                    )
                # 3) прошедшее — мимо
                if is_past(ev.date_text, ev.time_text):
                    continue
                out.append(ev); count += 1
            logging.info(f"{ch}: +{count} items")
        except Exception as e:
            logging.warning(f"Preview failed for {ch}: {e}")
        finally:
            time.sleep(CHANNEL_PAUSE)
    logging.info(f"LLM обработал постов: {llm_used}/{LLM_MAX_POSTS}")
    return out

# ───────────────────────── Дедупликация и сохранение ─────────────────────────
def smart_deduplicate(events: List[Event]) -> List[Event]:
    unique_events = {}
    for ev in events:
        fingerprint = (
            re.sub(r'[^\w\s]', '', (ev.title or "").lower())[:40],
            ev.date_text or "",
            ev.venue or "unknown"
        )
        if fingerprint not in unique_events:
            unique_events[fingerprint] = ev
        else:
            existing = unique_events[fingerprint]
            if ev.source not in existing.source:
                existing.source += f", {ev.source}"
            if ev.image and not existing.image:
                existing.image = ev.image
    return list(unique_events.values())

def merge_with_existing(new_events: List[Event]) -> List[Event]:
    """Локальный режим (без базы): сохраняем будущие события из прошлого запуска."""
    old = load_json_file("events.json", [])
    if not isinstance(old, list) or not old:
        for ev in new_events:
            ev.first_seen = datetime.now(TZ).isoformat()
        return new_events
    fresh_links = {ev.source_link for ev in new_events}
    now_iso = datetime.now(TZ).isoformat()
    kept: List[Event] = []
    for raw_e in old:
        ev = dict_to_event(raw_e)
        if ev is None:
            continue
        if ev.source_link in fresh_links or is_past(ev.date_text, ev.time_text):
            continue
        if not ev.first_seen:
            ev.first_seen = raw_e.get("first_seen") or now_iso
        kept.append(ev)
    for ev in new_events:
        ev.first_seen = now_iso
    return new_events + kept

def cleanup_unused_images(events: List[Event]):
    existing_images = set(p.name for p in IMAGES_DIR.glob("*") if p.is_file())
    used_images = set()
    for ev in events:
        if ev.image and ev.image.startswith("data/images/"):
            used_images.add(ev.image.replace("data/images/", ""))
    for img_name in (existing_images - used_images):
        try:
            (IMAGES_DIR / img_name).unlink()
        except Exception:
            pass

def save_outputs(events: List[Event]):
    DATA_DIR.mkdir(exist_ok=True)
    payload = [asdict(e) for e in events]
    (DATA_DIR / "events.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    Path("events.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    logging.info(f"Saved {len(events)} events")

def run_once():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    channels = load_json_file("channels.json", [])
    rules = load_json_file("rules.json", {"hard_exclude_words": [], "title_prefixes_remove": [], "venue_synonyms": {}})
    if not channels:
        logging.error("channels.json пуст или не найден")
        return
    mode = f"LLM: {'ON' if OPENROUTER_KEY else 'off'} | DB: {'ON' if sb else 'off (локально)'}"
    logging.info(f"Старт. Каналов: {len(channels)}. {mode}")
    items = harvest_preview(channels, rules)
    logging.info(f"Raw events: {len(items)}")
    items = smart_deduplicate(items)
    logging.info(f"After dedupe: {len(items)}")

    final = None
    if sb:
        try:
            upsert_events_db(items)
            purge_old_db()
            final = [row_to_event(r) for r in load_future_from_db()]
            logging.info(f"База: {len(final)} будущих событий в Supabase")
        except Exception as e:
            logging.warning(f"Ошибка БД, переключаюсь на локальный режим: {e}")
            final = None
    if final is None:
        merged = merge_with_existing(items)
        final = smart_deduplicate(merged)
        logging.info(f"Локальный режим: {len(final)} событий после мерджа")

    cleanup_unused_images(final)
    save_outputs(final)

if __name__ == "__main__":
    run_once()
