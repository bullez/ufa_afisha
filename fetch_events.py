# -*- coding: utf-8 -*-
"""
Ufa Afisha — гибрид: t.me/s/ + rules.json
- Сбор постов из публичных превью Telegram (без API, безопасно)
- Фильтрация через rules.json (что выкидывать, что оставлять)
- Сохранение в data/events.json и events.json (для текущего сайта)
"""

import os, re, json, time, html, logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

import pytz, requests
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────────────────────────────────────
# Конфиг
# ─────────────────────────────────────────────────────────────────────────────
CITY = "Уфа"
TZ = pytz.timezone("Asia/Yekaterinburg")
FRESH_DAYS = int(os.getenv("FRESH_DAYS", "90"))

DATA_DIR = Path("data")
IMAGES_DIR = DATA_DIR / "images"

DEFAULT_CHANNELS = [
    "enter_ufa","gorod347","ufa_arteria","prostranstvoera",
    "gallerymiras","zamamuseum","vintaq_spot","kuda_go_ufa",
    "ppuummkkaaufa","ufamesto","clubmechti","lutufa",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124 Safari/537.36"
}

EVENT_KEYWORDS = [
    "кино","фильм","кинопоказ","концерт","джаз","оркестр","джем","dj","вечеринк","рейв",
    "лектор","лекци","семинар","мастер-класс","воркшоп","театр","спектакл","перформанс",
    "выставк","галере","музей","арт","экскурс","киноклуб"
]
EVENT_RE = re.compile("|".join(EVENT_KEYWORDS), re.I)

URL_RE = re.compile(r"https?://[^\s)>\]]+", re.I)
DATE_TOKENS = r"(?:\b\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?|\b\d{1,2}\s+(?:янв|фев|мар|апр|мая|июн|июл|авг|сен|окт|ноя|дек|января|февраля|марта|апреля|июня|июля|августа|сентября|октября|ноября|декабря)\b)"
TIME_TOKENS = r"(?:\b[01]?\d|2[0-3])[:.]\d{2}"

# ─────────────────────────────────────────────────────────────────────────────
# rules.json
# ─────────────────────────────────────────────────────────────────────────────
def load_rules() -> dict:
    path = Path("rules.json")
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return {
        "title_prefixes_remove": [],
        "hard_exclude_words": [],
        "venue_hints_patterns": [],
        "venue_blacklist_patterns": []
    }

def should_exclude(text: str, rules: dict) -> bool:
    low = (text or "").lower()
    return any(w.lower() in low for w in rules.get("hard_exclude_words", []))

def clean_title(title: str, rules: dict) -> str:
    for prefix in rules.get("title_prefixes_remove", []):
        title = re.sub(rf"^{re.escape(prefix)}\s*[:,—-]?\s*", "", title, flags=re.I)
    return title.strip()

# ─────────────────────────────────────────────────────────────────────────────
# Модель
# ─────────────────────────────────────────────────────────────────────────────
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
    score: float = 0.0
    image: Optional[str] = None
    kind: str = "event"

# ─────────────────────────────────────────────────────────────────────────────
# Утилиты
# ─────────────────────────────────────────────────────────────────────────────
def _ensure_dir(p: Path): p.mkdir(parents=True, exist_ok=True)

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()

def extract_urls(text: str) -> List[str]:
    return URL_RE.findall(text or "")

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
    dt = None; date_str = None
    m = re.search(r"\b(\d{1,2})[./-](\d{1,2})(?:[./-](\d{2,4}))?\b", t)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
        y = int(y) if y else datetime.now(TZ).year
        try:
            dt = TZ.localize(datetime(y, mo, d)); date_str = f"{d:02d}.{mo:02d}.{y}"
        except: pass
    time_str = None
    tm = re.search(r"\b([01]?\d|2[0-3])[:.](\d{2})\b", t)
    if tm:
        hh, mm = int(tm.group(1)), int(tm.group(2))
        time_str = f"{hh:02d}:{mm:02d}"
        if dt: dt = dt.replace(hour=hh, minute=mm)
    return dt, date_str, time_str

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
    parts = [p for p in parts if 25 <= len(p) <= 200][:2]
    out = " ".join(parts) if parts else t[:180]
    return sentence_case(out)

def price_from_text(text: str) -> Optional[str]:
    low = (text or "").lower()
    if any(x in low for x in ["вход свобод", "вход бесплат", "бесплатно", "free", "по донату"]):
        return "Вход свободный"
    m = re.search(r"\bот?\s*(\d{2,6})\s*(?:₽|р|руб)\b", low)
    if m: return f"от {m.group(1)} ₽"
    m = re.search(r"\b(\d{2,6})\s*(?:₽|р|руб)\b", low)
    if m: return f"{m.group(1)} ₽"
    return None

# ─────────────────────────────────────────────────────────────────────────────
# Сбор с t.me/s/
# ─────────────────────────────────────────────────────────────────────────────
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

                # Фильтрация по rules.json
                if should_exclude(text, rules):
                    continue

                dt, date_str, time_str = extract_datetime(text)
                link_node = it.select_one("a.tgme_widget_message_date")
                link = link_node.get("href") if link_node else f"https://t.me/{ch}"

                # Картинка (ссылка на CDN, не скачиваем)
                img = None
                ph = it.select_one("a.tgme_widget_message_photo_wrap") or it.select_one("a.tgme_widget_message_video_thumb")
                if ph and ph.has_attr("style"):
                    mm = re.search(r"url\(['\"]?(.*?)['\"]?\)", ph["style"])
                    if mm: img = mm.group(1)

                # Классификация
                low = text.lower()
                if EVENT_RE.search(low) or re.search(DATE_TOKENS, low) or re.search(TIME_TOKENS, low):
                    kind = "event"
                else:
                    continue  # показываем только события

                title = clean_title(title_from_text(text), rules)
                desc = make_desc(text)
                price = price_from_text(text) or "—"

                ev = Event(
                    title=title, desc=desc,
                    start=dt.isoformat() if dt else None,
                    date_text=date_str, time_text=time_str,
                    city=CITY, venue=None, price=price,
                    source=ch, source_link=link, posted_at=None,
                    raw=text, image=img, kind=kind
                )
                out.append(ev); count += 1

            logging.info(f"{ch}: +{count} items")
        except Exception as e:
            logging.warning(f"Preview failed for {ch}: {e}")
    return out

# ─────────────────────────────────────────────────────────────────────────────
# Сохранение
# ─────────────────────────────────────────────────────────────────────────────
def save_outputs(events: List[Event]):
    _ensure_dir(DATA_DIR)
    payload = [asdict(e) for e in events]
    (DATA_DIR / "events.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    # Дублируем в корень, чтобы текущий index.html сразу заработал
    Path("events.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    logging.info(f"Saved {len(events)} events → data/events.json и events.json")

# ─────────────────────────────────────────────────────────────────────────────
# Запуск
# ─────────────────────────────────────────────────────────────────────────────
def run_once():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    rules = load_rules()
    channels = DEFAULT_CHANNELS
    logging.info(f"Harvest. Channels: {len(channels)}; rules loaded: {bool(rules)}")
    items = harvest_preview(channels, rules)
    save_outputs(items)

if __name__ == "__main__":
    run_once()
