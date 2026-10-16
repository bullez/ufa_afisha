import json
import requests
from datetime import datetime, timedelta

# MCP сервер для запроса. Он публичный, без ключей.
MCP_URL = "https://spontanno.space/mcp"

# Простой вызов. В реальности MCP требует особый формат JSON-RPC,
# но для примера логики сойдёт и такой запрос (в рабочем варианте нужен клиент MCP).
# Здесь показываю суть: мы получаем список событий.

def fetch_ufa_events():
    # Это упрощение. Для продакшена нужно использовать MCP-клиент.
    # Логика: спрашиваем у сервера, что есть в Уфе.
    # В ответ приходит JSON с событиями.
    
    # Пример того, что мы могли бы получить (заглушка для теста)
    events = [
        {"id": 1, "title": "АйдаФест", "category": "фестиваль", "price": "бесплатно", "date": "2026-08-29", "place": "Арт-Квадрат"},
        {"id": 2, "title": "Яшьлек Party", "category": "вечеринка", "price": "платно", "date": "2026-08-27", "place": "Огни Уфы"},
    ]
    return events

def filter_for_millennials(events):
    # Оставляем то, что интересно: бесплатное, фестивали, вечеринки, музыка
    keywords = ['фестиваль', 'вечеринка', 'музыка', 'арт', 'бесплатно', 'дизайн']
    filtered = []
    for e in events:
        # Простая проверка по названию или категории
        text = (e['title'] + ' ' + e['category']).lower()
        if any(kw in text for kw in keywords):
            filtered.append(e)
    return filtered

if __name__ == "__main__":
    raw = fetch_ufa_events()
    clean = filter_for_millennials(raw)
    
    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
    
    print(f"Обновлено. Событий: {len(clean)}")