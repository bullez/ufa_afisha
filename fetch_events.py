import json
from datetime import datetime, timedelta

def fetch_ufa_events():
    """
    Пока здесь тестовые данные с картинками.
    Позже заменим на реальный источник.
    """
    today = datetime.now()
    
    events = [
        {
            "title": "АйдаФест",
            "category": "фестиваль",
            "date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
            "place": "Арт-Квадрат",
            "price": "бесплатно",
            "image": "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=600&q=80"
        },
        {
            "title": "Яшьлек Party",
            "category": "вечеринка",
            "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "place": "Огни Уфы",
            "price": "платно",
            "image": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=600&q=80"
        },
        {
            "title": "Инди-концерт в подвале",
            "category": "музыка",
            "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "place": "Бар «Синяя борода»",
            "price": "500 ₽",
            "image": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=600&q=80"
        },
        {
            "title": "Выставка современного искусства",
            "category": "арт",
            "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "place": "Центр современного искусства",
            "price": "бесплатно",
            "image": "https://images.unsplash.com/photo-1531243269054-5ebf6f34081e?w=600&q=80"
        }
    ]
    
    return events


def filter_for_millennials(events):
    keywords = ['фестиваль', 'вечеринка', 'музыка', 'арт', 'бесплатно', 'дизайн', 'лекция', 'стендап']
    filtered = []
    for e in events:
        text = (e.get('title', '') + ' ' + e.get('category', '')).lower()
        if any(kw in text for kw in keywords):
            filtered.append(e)
    return filtered


if __name__ == "__main__":
    raw = fetch_ufa_events()
    clean = filter_for_millennials(raw)
    
    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
    
    print(f"Обновлено. Событий: {len(clean)}")
