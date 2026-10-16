<!DOCTYPE html>
<html lang="ru" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Уфа для своих — афиша</title>
    <style>
        :root[data-theme="dark"] {
            --bg: #0a0a0a; --card: #141414; --border: #262626;
            --text: #f5f5f5; --muted: #a3a3a3; --accent: #c4ff4d; --accent-contrast: #000;
        }
        :root[data-theme="light"] {
            --bg: #f5f5f7; --card: #ffffff; --border: #e5e5ea;
            --text: #1d1d1f; --muted: #6e6e73; --accent: #007aff; --accent-contrast: #ffffff;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: var(--bg); color: var(--text); line-height: 1.5;
            padding: 20px; padding-bottom: 80px; max-width: 1200px; margin: 0 auto;
            -webkit-font-smoothing: antialiased; overflow-x: hidden;
            transition: background 0.3s, color 0.3s;
        }
        header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 24px; padding-bottom: 16px;
            border-bottom: 1px solid var(--border); flex-wrap: wrap; gap: 12px;
        }
        h1 { font-size: 2rem; font-weight: 800; letter-spacing: -1px; }
        h1 span { color: var(--accent); }
        .header-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .theme-toggle {
            background: var(--card); border: 1px solid var(--border);
            border-radius: 12px; width: 42px; height: 42px; cursor: pointer;
            font-size: 1.2rem; display: flex; align-items: center; justify-content: center;
            transition: all 0.2s; color: var(--text);
        }
        .theme-toggle:hover { border-color: var(--accent); }
        .weather-block {
            display: flex; gap: 8px; background: var(--card);
            border: 1px solid var(--border); border-radius: 14px;
            padding: 8px 12px; font-size: 0.9rem;
        }
        .weather-item {
            display: flex; flex-direction: column; align-items: center; gap: 2px;
            padding: 0 8px; border-right: 1px solid var(--border); min-width: 60px;
        }
        .weather-item:last-child { border-right: none; }
        .weather-label { font-size: 0.6rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
        .weather-icon { font-size: 1.2rem; line-height: 1; }
        .weather-temp { font-size: 0.9rem; font-weight: 800; color: var(--accent); }
        #count { color: var(--muted); font-size: 0.9rem; font-weight: 500; }
        .ai-search {
            background: linear-gradient(135deg, rgba(196, 255, 77, 0.08) 0%, rgba(196, 255, 77, 0.02) 100%);
            border: 1px solid var(--border); border-radius: 20px; padding: 20px; margin-bottom: 24px;
        }
        :root[data-theme="light"] .ai-search {
            background: linear-gradient(135deg, rgba(0, 122, 255, 0.08) 0%, rgba(0, 122, 255, 0.02) 100%);
        }
        .ai-search-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
        .ai-search-header .icon { font-size: 1.4rem; }
        .ai-search-header h2 { font-size: 1rem; font-weight: 700; color: var(--accent); }
        .ai-search-header .status { font-size: 0.75rem; color: var(--muted); margin-left: auto; }
        .ai-search input {
            width: 100%; background: var(--card); border: 1px solid var(--border);
            border-radius: 14px; padding: 14px 18px; color: var(--text);
            font-size: 1rem; outline: none; transition: border-color 0.2s;
        }
        .ai-search input:focus { border-color: var(--accent); }
        .ai-search input::placeholder { color: var(--muted); }
        .ai-search input:disabled { opacity: 0.5; cursor: not-allowed; }
        .search-wrap { margin-bottom: 20px; position: relative; }
        .search-wrap input {
            width: 100%; background: var(--card); border: 1px solid var(--border);
            border-radius: 14px; padding: 14px 18px 14px 44px; color: var(--text);
            font-size: 1rem; outline: none; transition: border-color 0.2s;
        }
        .search-wrap input:focus { border-color: var(--accent); }
        .search-wrap::before {
            content: '🔍'; position: absolute; left: 16px; top: 50%;
            transform: translateY(-50%); font-size: 1rem; opacity: 0.6;
        }
        .filters { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
        .filters button {
            background: var(--card); color: var(--muted);
            border: 1px solid var(--border); padding: 8px 16px;
            border-radius: 100px; cursor: pointer; font-size: 0.85rem;
            transition: all 0.2s; font-weight: 500;
        }
        .filters button:hover { border-color: var(--accent); color: var(--text); }
        .filters button.active {
            background: var(--accent); color: var(--accent-contrast);
            border-color: var(--accent); font-weight: 700;
        }
        .filters-label {
            font-size: 0.7rem; color: var(--muted); text-transform: uppercase;
            letter-spacing: 1px; font-weight: 600; margin-bottom: 6px; margin-top: 8px;
        }
        .grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .card {
            background: var(--card); border: 1px solid var(--border);
            border-radius: 20px; overflow: hidden;
            transition: transform 0.25s, border-color 0.25s, box-shadow 0.25s;
            display: flex; flex-direction: column; cursor: pointer;
        }
        .card:hover {
            transform: translateY(-4px); border-color: var(--accent);
            box-shadow: 0 12px 40px rgba(0, 122, 255, 0.08);
        }
        .card-image {
            width: 100%; aspect-ratio: 4/3; background: var(--border);
            background-size: cover; background-position: center; position: relative;
        }
        .card-body { padding: 16px; flex: 1; display: flex; flex-direction: column; }
        .card-tag {
            display: inline-block; font-size: 0.7rem; text-transform: uppercase;
            letter-spacing: 1px; color: var(--accent); margin-bottom: 8px; font-weight: 700;
        }
        .card h3 {
            font-size: 1.05rem; margin-bottom: 10px; line-height: 1.35; font-weight: 700;
            display: -webkit-box; -webkit-line-clamp: 3;
            -webkit-box-orient: vertical; overflow: hidden;
        }
        .card-meta {
            font-size: 0.85rem; color: var(--muted);
            margin-bottom: 5px; display: flex; align-items: center; gap: 6px;
        }
        .card-price {
            margin-top: auto; padding-top: 12px;
            font-weight: 800; font-size: 1rem;
        }
        .card-price.free { color: var(--accent); }
        .card-score {
            font-size: 0.75rem; color: var(--accent);
            margin-top: 6px; font-weight: 600;
        }
        .overlay {
            position: fixed; inset: 0; background: rgba(0,0,0,0.9);
            opacity: 0; pointer-events: none; transition: opacity 0.3s;
            z-index: 998; backdrop-filter: blur(8px);
        }
        .overlay.active { opacity: 1; pointer-events: auto; }
        .global-loader {
            position: fixed; inset: 0; background: var(--bg); z-index: 10000;
            display: flex; align-items: center; justify-content: center;
            transition: opacity 0.6s ease;
        }
        .global-loader.hidden { opacity: 0; pointer-events: none; }
        .global-loader-content {
            display: flex; flex-direction: column; align-items: center; gap: 16px;
        }
        .global-loader-text { font-size: 1.1rem; font-weight: 700; color: var(--accent); }
        .global-loader-sub { font-size: 0.85rem; color: var(--muted); }
        .spinner {
            width: 44px; height: 44px;
            border: 4px solid rgba(196, 255, 77, 0.2);
            border-top-color: var(--accent); border-radius: 50%;
            animation: spin 0.9s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .sidebar {
            position: fixed; inset: 0; width: 100vw; height: 100vh;
            z-index: 999; transform: translateX(-100%);
            transition: transform 0.45s cubic-bezier(0.34, 1.3, 0.64, 1);
            pointer-events: none; background: var(--bg);
        }
        .sidebar.active { transform: translateX(0); pointer-events: auto; }
        .sidebar-inner { width: 100%; height: 100%; display: flex; flex-direction: row; }
        .sidebar-inner.no-image .card-3d-wrap { display: none; }
        .sidebar-inner.no-image .card-info { border-left: none; }
        .card-3d-wrap {
            flex: 0 0 50%; display: flex; align-items: center; justify-content: center;
            padding: 20px; background: var(--bg); perspective: 1500px;
            overflow: hidden; height: 100vh; position: relative;
        }
        .card-3d {
            width: 100%; height: 100%; border-radius: 16px; background: var(--card);
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 30px 60px rgba(0,0,0,0.4), 0 0 0 1px var(--border) inset;
            transform-style: preserve-3d; transition: transform 0.1s ease-out;
            cursor: grab; position: relative; overflow: hidden;
        }
        .card-3d:active { cursor: grabbing; }
        .card-3d img {
            max-width: 100%; max-height: 100%; width: auto; height: auto;
            object-fit: contain; display: block; user-select: none;
            -webkit-user-drag: none; pointer-events: none;
        }
        .card-3d::after {
            content: ''; position: absolute; inset: 0; border-radius: 16px;
            background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, transparent 50%);
            pointer-events: none;
        }
        .card-3d-hint {
            position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
            background: rgba(0,0,0,0.7); color: #fff; font-size: 0.75rem;
            padding: 6px 14px; border-radius: 100px; pointer-events: none;
            transition: opacity 0.4s; opacity: 0; white-space: nowrap;
        }
        .sidebar.active .card-3d-hint { opacity: 1; }
        .card-3d-wrap.touched .card-3d-hint { opacity: 0; }
        .card-3d-loading {
            position: absolute; inset: 0; display: flex; flex-direction: column;
            align-items: center; justify-content: center; gap: 14px;
            background: var(--card); color: var(--muted); font-size: 0.9rem; z-index: 2;
        }
        .card-3d-loading.hidden { display: none; }
        .card-info {
            flex: 1; display: flex; flex-direction: column; overflow: hidden;
            border-left: 1px solid var(--border); background: var(--bg);
            height: 100vh; position: relative;
        }
        .card-info-header {
            display: flex; justify-content: space-between; align-items: center;
            padding: 18px 28px; border-bottom: 1px solid var(--border); flex-shrink: 0;
        }
        .card-info-header h2 {
            font-size: 0.85rem; font-weight: 700; color: var(--muted);
            text-transform: uppercase; letter-spacing: 1.5px;
        }
        .card-info-close {
            background: var(--card); border: 1px solid var(--border);
            color: var(--text); font-size: 1.4rem; width: 42px; height: 42px;
            border-radius: 50%; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            transition: background 0.2s; line-height: 1; flex-shrink: 0;
        }
        .card-info-close:hover { background: var(--border); }
        .card-info-scroll {
            flex: 1; overflow-y: auto; padding: 32px 28px;
            scrollbar-width: thin; scrollbar-color: var(--border) transparent;
        }
        .card-info-scroll::-webkit-scrollbar { width: 8px; }
        .card-info-scroll::-webkit-scrollbar-track { background: transparent; }
        .card-info-scroll::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        .card-info-loading {
            position: absolute; inset: 0; top: 63px;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            gap: 14px; background: var(--bg); color: var(--muted);
            font-size: 0.9rem; z-index: 2;
        }
        .card-info-loading.hidden { display: none; }
        .card-info-tag {
            display: inline-block; font-size: 0.75rem; text-transform: uppercase;
            letter-spacing: 1px; color: var(--accent); margin-bottom: 12px; font-weight: 700;
            padding: 4px 10px; background: var(--card);
            border: 1px solid var(--border); border-radius: 6px;
        }
        .card-info-title {
            font-size: 1.8rem; font-weight: 800; line-height: 1.3;
            margin-bottom: 24px; letter-spacing: -0.5px;
        }
        .card-info-meta {
            display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px;
            padding: 20px; background: var(--card);
            border-radius: 14px; border: 1px solid var(--border);
        }
        .card-info-meta-item {
            display: flex; align-items: flex-start; gap: 12px; font-size: 1rem;
        }
        .card-info-meta-item .icon {
            font-size: 1.2rem; flex-shrink: 0; width: 28px; text-align: center;
        }
        .card-info-meta-item .label {
            color: var(--muted); font-size: 0.75rem;
            text-transform: uppercase; letter-spacing: 0.5px;
            font-weight: 600; margin-bottom: 2px;
        }
        .card-info-meta-item .value { color: var(--text); font-weight: 500; }
        .card-info-meta-item .value.price-free { color: var(--accent); font-weight: 700; }
        .card-info-text {
            font-size: 1.05rem; line-height: 1.8; color: var(--text);
            white-space: pre-wrap; word-wrap: break-word; margin-bottom: 24px;
            padding: 20px; background: var(--card);
            border-radius: 14px; border: 1px solid var(--border); opacity: 0.9;
        }
        .card-info-actions { display: flex; flex-direction: column; gap: 10px; }
        .card-info-btn {
            display: flex; align-items: center; justify-content: center; gap: 10px;
            padding: 16px 24px; border-radius: 14px; font-size: 1rem;
            font-weight: 700; text-decoration: none; cursor: pointer;
            border: none; transition: all 0.2s;
        }
        .card-info-btn.primary { background: var(--accent); color: var(--accent-contrast); }
        .card-info-btn.primary:hover { opacity: 0.85; transform: translateY(-2px); }
        .card-info-btn.secondary {
            background: var(--card); color: var(--text); border: 1px solid var(--border);
        }
        .card-info-btn.secondary:hover { background: var(--border); }
        .empty { text-align: center; padding: 80px 20px; color: var(--muted); grid-column: 1/-1; }
        .toast {
            position: fixed; bottom: 30px; left: 50%;
            transform: translateX(-50%) translateY(80px);
            background: var(--accent); color: var(--accent-contrast);
            padding: 12px 24px; border-radius: 100px;
            font-weight: 700; font-size: 0.9rem; z-index: 10001;
            transition: transform 0.3s ease; pointer-events: none;
        }
        .toast.show { transform: translateX(-50%) translateY(0); }
        @media (max-width: 800px) {
            .sidebar-inner { flex-direction: column; }
            .card-3d-wrap { flex: 0 0 45%; height: 45vh; padding: 10px; }
            .card-3d { border-radius: 12px; }
            .card-info { height: 55vh; border-left: none; border-top: 1px solid var(--border); }
            .card-info-loading { top: 55px; }
            .card-info-title { font-size: 1.3rem; }
            .card-info-scroll { padding: 20px; }
            h1 { font-size: 1.5rem; }
            .weather-block { padding: 6px 8px; font-size: 0.8rem; }
            .weather-item { min-width: 50px; padding: 0 5px; }
            .weather-icon { font-size: 1rem; }
            .weather-temp { font-size: 0.85rem; }
            .grid { grid-template-columns: 1fr; }
            .filters button { padding: 6px 12px; font-size: 0.8rem; }
        }
    </style>
</head>
<body>
    <div id="global-loader" class="global-loader">
        <div class="global-loader-content">
            <div class="spinner"></div>
            <div class="global-loader-text">Загрузка сайта...</div>
            <div class="global-loader-sub" id="global-loader-sub">Подготовка умного поиска</div>
        </div>
    </div>

    <header>
        <h1>Уфа <span>для своих</span></h1>
        <div class="header-actions">
            <div class="weather-block" id="weather-block">
                <div class="weather-item">
                    <span class="weather-label">Сейчас</span>
                    <span class="weather-icon" id="w-now-icon">—</span>
                    <span class="weather-temp" id="w-now-temp">—</span>
                </div>
                <div class="weather-item">
                    <span class="weather-label">Вечер</span>
                    <span class="weather-icon" id="w-eve-icon">—</span>
                    <span class="weather-temp" id="w-eve-temp">—</span>
                </div>
                <div class="weather-item">
                    <span class="weather-label">Завтра</span>
                    <span class="weather-icon" id="w-tmr-icon">—</span>
                    <span class="weather-temp" id="w-tmr-temp">—</span>
                </div>
            </div>
            <button class="theme-toggle" id="theme-toggle" title="Сменить тему">🌙</button>
        </div>
    </header>

    <div class="ai-search">
        <div class="ai-search-header">
            <span class="icon">🤖</span>
            <h2>Спроси меня о событиях</h2>
            <span class="status" id="ai-status">Загрузка модели...</span>
        </div>
        <input type="text" id="ai-query" placeholder="Например: хочу что-то атмосферное и недорогое..." disabled>
    </div>

    <div class="search-wrap">
        <input type="text" id="search" placeholder="Поиск по словам...">
    </div>

    <div class="filters-label">Когда</div>
    <div class="filters" id="date-filters">
        <button data-date="all" class="active">Все</button>
        <button data-date="today">Сегодня</button>
        <button data-date="tomorrow">Завтра</button>
        <button data-date="weekend">Выходные</button>
        <button data-date="week">Неделя</button>
    </div>

    <div class="filters-label">Категория</div>
    <div class="filters" id="category-filters">
        <button data-category="all" class="active">Все</button>
        <button data-category="concert">🎵 Музыка</button>
        <button data-category="party">🎉 Вечеринки</button>
        <button data-category="cinema">🎬 Кино</button>
        <button data-category="theater">🎭 Театр</button>
        <button data-category="lecture">📚 Лекции</button>
        <button data-category="exhibition">🖼️ Выставки</button>
        <button data-category="market">🛍️ Маркеты</button>
        <button data-category="festival">🎪 Фестивали</button>
        <button data-category="standup">🎤 Стендап</button>
        <button data-category="free">💸 Бесплатно</button>
    </div>

    <div id="count" style="text-align:center;margin-bottom:16px;"></div>

    <div id="feed" class="grid"></div>

    <div class="overlay" id="overlay"></div>

    <aside class="sidebar" id="sidebar">
        <div class="sidebar-inner" id="sidebar-inner">
            <div class="card-3d-wrap" id="card-3d-wrap">
                <div class="card-3d" id="card-3d">
                    <div class="card-3d-loading" id="card-3d-loading">
                        <div class="spinner"></div>
                        <span>Загрузка картинки...</span>
                    </div>
                </div>
                <div class="card-3d-hint">👆 Поверни карточку</div>
            </div>
            <div class="card-info">
                <div class="card-info-header">
                    <h2>Событие</h2>
                    <button class="card-info-close" id="sidebar-close">×</button>
                </div>
                <div class="card-info-scroll" id="card-info-content"></div>
                <div class="card-info-loading" id="card-info-loading">
                    <div class="spinner"></div>
                    <span>Загрузка события...</span>
                </div>
            </div>
        </div>
    </aside>

    <div class="toast" id="toast">Ссылка скопирована</div>

    <script type="module">
        import { pipeline, env } from 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.0.2';
        env.allowLocalModels = false;

        let extractor = null;
        let eventEmbeddings = [];
        let allEvents = [];
        let aiReady = false;

        const globalLoader = document.getElementById('global-loader');
        const globalLoaderSub = document.getElementById('global-loader-sub');

        // ─── Тема ───
        function setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            const btn = document.getElementById('theme-toggle');
            if (btn) btn.textContent = theme === 'dark' ? '🌙' : '☀️';
        }
        function initTheme() {
            const saved = localStorage.getItem('theme');
            if (saved) { setTheme(saved); return; }
            const prefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
            setTheme(prefersLight ? 'light' : 'dark');
        }
        initTheme();
        document.getElementById('theme-toggle').addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            setTheme(current === 'dark' ? 'light' : 'dark');
        });

        // ─── Погода ───
        async function loadWeather() {
            const setW = (id, icon, temp) => {
                const el = document.getElementById(id);
                if (el) el.textContent = icon;
                const t = document.getElementById(id.replace('icon', 'temp'));
                if (t) t.textContent = temp;
            };
            const iconMap = {
                0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️', 45: '🌫️', 48: '🌫️',
                51: '🌦️', 53: '🌦️', 55: '🌦️', 61: '🌧️', 63: '🌧️', 65: '🌧️',
                71: '🌨️', 73: '🌨️', 75: '🌨️', 80: '🌧️', 81: '🌧️', 82: '🌧️',
                95: '⛈️', 96: '⛈️', 99: '⛈️',
            };
            try {
                const res = await fetch(
                    'https://api.open-meteo.com/v1/forecast?latitude=54.7388&longitude=55.9721&hourly=temperature_2m,weather_code&current=temperature_2m,weather_code&forecast_days=2&timezone=Asia%2FYekaterinburg',
                    { signal: AbortSignal.timeout(8000) }
                );
                if (!res.ok) throw new Error('HTTP ' + res.status);
                const data = await res.json();
                setW('w-now-icon', iconMap[data.current.weather_code] || '🌡️', Math.round(data.current.temperature_2m) + '°');

                const times = data.hourly.time;
                const temps = data.hourly.temperature_2m;
                const codes = data.hourly.weather_code;
                const today = new Date().toISOString().slice(0, 10);
                const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 10);

                let eveIdx = times.findIndex(t => t === `${today}T18:00`);
                if (eveIdx < 0) eveIdx = times.findIndex(t => t === `${today}T17:00`);
                let tmrIdx = times.findIndex(t => t === `${tomorrow}T12:00`);

                if (eveIdx >= 0) setW('w-eve-icon', iconMap[codes[eveIdx]] || '🌡️', Math.round(temps[eveIdx]) + '°');
                else setW('w-eve-icon', '—', '—');
                if (tmrIdx >= 0) setW('w-tmr-icon', iconMap[codes[tmrIdx]] || '🌡️', Math.round(temps[tmrIdx]) + '°');
                else setW('w-tmr-icon', '—', '—');
                return;
            } catch (err) { console.warn('Open-Meteo failed:', err); }
            try {
                const res = await fetch('https://wttr.in/Ufa?format=j1', { signal: AbortSignal.timeout(8000) });
                const data = await res.json();
                setW('w-now-icon', '🌡️', data.current_condition[0].temp_C + '°');
            } catch (err) { console.error('Weather failed:', err); }
        }
        loadWeather();
        setInterval(loadWeather, 30 * 60 * 1000);

        // ─── AI ───
        async function initAI() {
            const statusEl = document.getElementById('ai-status');
            const inputEl = document.getElementById('ai-query');
            if (!statusEl || !inputEl) return;
            try {
                statusEl.textContent = 'Загрузка модели (33 МБ)...';
                if (globalLoaderSub) globalLoaderSub.textContent = 'Загрузка AI-модели...';
                extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2', { dtype: 'q8' });
                statusEl.textContent = 'Индексация событий...';
                if (globalLoaderSub) globalLoaderSub.textContent = 'Индексация событий...';
                await indexEvents();
                statusEl.textContent = 'Готово! Спрашивай.';
                inputEl.disabled = false;
                aiReady = true;
                if (globalLoader) globalLoader.classList.add('hidden');
            } catch (err) {
                console.error('AI init error:', err);
                statusEl.textContent = 'AI недоступен';
                if (globalLoader) globalLoader.classList.add('hidden');
            }
        }
        async function indexEvents() {
            if (!extractor || allEvents.length === 0) return;
            eventEmbeddings = [];
            for (const event of allEvents) {
                const text = `${event.title || ''} ${event.desc || ''} ${event.venue || ''}`.trim();
                if (!text) { eventEmbeddings.push(null); continue; }
                try {
                    const output = await extractor(text, { pooling: 'mean', normalize: true });
                    eventEmbeddings.push(Array.from(output.data));
                } catch (err) { eventEmbeddings.push(null); }
            }
        }
        function cosineSimilarity(a, b) {
            if (!a || !b) return 0;
            let dot = 0, normA = 0, normB = 0;
            for (let i = 0; i < a.length; i++) {
                dot += a[i] * b[i]; normA += a[i] * a[i]; normB += b[i] * b[i];
            }
            return dot / (Math.sqrt(normA) * Math.sqrt(normB));
        }
        async function aiSearch(query) {
            if (!extractor || !query.trim()) { renderAll(); return; }
            const statusEl = document.getElementById('ai-status');
            if (statusEl) statusEl.textContent = 'Ищу...';
            try {
                const output = await extractor(query, { pooling: 'mean', normalize: true });
                const queryEmbedding = Array.from(output.data);
                const scored = allEvents.map((event, idx) => ({
                    event, score: eventEmbeddings[idx] ? cosineSimilarity(queryEmbedding, eventEmbeddings[idx]) : 0
                }));
                scored.sort((a, b) => b.score - a.score);
                const relevant = scored.filter(s => s.score > 0.2);
                if (statusEl) statusEl.textContent = `Найдено ${relevant.length} событий`;
                renderWithScores(relevant);
            } catch (err) {
                console.error('AI search error:', err);
                if (statusEl) statusEl.textContent = 'Ошибка поиска';
            }
        }

        // ─── Логика ───
        let currentDateFilter = 'all';
        let currentCategoryFilter = 'all';
        let searchQuery = '';

        async function load() {
            try {
                const res = await fetch('events.json?t=' + Date.now());
                if (!res.ok) throw new Error('HTTP ' + res.status);
                allEvents = await res.json();
                render();
                if (aiReady) await indexEvents();
            } catch (err) {
                console.error('LOAD ERROR:', err);
                const feed = document.getElementById('feed');
                if (feed) feed.innerHTML = '<div class="empty">Ошибка загрузки данных: ' + err.message + '</div>';
                if (globalLoader) globalLoader.classList.add('hidden');
            }
        }

        function formatDate(e) {
            const parts = [];
            if (e.date_text) parts.push(e.date_text);
            if (e.time_text) parts.push(e.time_text);
            if (parts.length) return parts.join(' · ');
            return 'Дата уточняется';
        }
        function isToday(e) {
            if (!e.date_text) return false;
            const t = new Date();
            return e.date_text === `${String(t.getDate()).padStart(2,'0')}.${String(t.getMonth()+1).padStart(2,'0')}.${t.getFullYear()}`;
        }
        function isTomorrow(e) {
            if (!e.date_text) return false;
            const t = new Date(Date.now() + 86400000);
            return e.date_text === `${String(t.getDate()).padStart(2,'0')}.${String(t.getMonth()+1).padStart(2,'0')}.${t.getFullYear()}`;
        }
        function isWeekend(e) {
            if (!e.date_text) return false;
            const now = new Date();
            for (let i = 0; i < 8; i++) {
                const d = new Date(now.getTime() + i * 86400000);
                if (d.getDay() === 6 || d.getDay() === 0) {
                    if (e.date_text === `${String(d.getDate()).padStart(2,'0')}.${String(d.getMonth()+1).padStart(2,'0')}.${d.getFullYear()}`) return true;
                }
            }
            return false;
        }
        function isThisWeek(e) {
            if (!e.date_text) return false;
            const now = new Date();
            for (let i = 0; i < 7; i++) {
                const d = new Date(now.getTime() + i * 86400000);
                if (e.date_text === `${String(d.getDate()).padStart(2,'0')}.${String(d.getMonth()+1).padStart(2,'0')}.${d.getFullYear()}`) return true;
            }
            return false;
        }
        function sortEvents(events) {
            return [...events].sort((a, b) => {
                const aHasDate = !!a.date_text;
                const bHasDate = !!b.date_text;
                if (aHasDate && bHasDate) return a.date_text.localeCompare(b.date_text);
                if (aHasDate) return -1;
                if (bHasDate) return 1;
                return 0;
            });
        }
        function escapeHtml(s) {
            const div = document.createElement('div');
            div.textContent = s || '';
            return div.innerHTML;
        }
        function renderCard(e, idx, score) {
            const img = e.image ? `<div class="card-image" style="background-image: url('${e.image}')"></div>` : '';
            const priceClass = (e.price || '').toLowerCase().includes('бесплат') || (e.price || '').toLowerCase().includes('свобод') ? 'free' : '';
            const source = e.source ? `<div class="card-tag">@${e.source}</div>` : '';
            const scoreHtml = score !== undefined ? `<div class="card-score">Релевантность: ${Math.round(score * 100)}%</div>` : '';

            // ─── Не показываем пустые поля ───
            const venueHtml = e.venue ? `<div class="card-meta">📍 ${escapeHtml(e.venue)}</div>` : '';
            const priceHtml = e.price ? `<div class="card-price ${priceClass}">${escapeHtml(e.price)}</div>` : '';

            return `
                <div class="card" data-index="${idx}" onclick="openSidebar(${idx})">
                    ${img}
                    <div class="card-body">
                        ${source}
                        <h3>${escapeHtml(e.title) || 'Без названия'}</h3>
                        <div class="card-meta">📅 ${formatDate(e)}</div>
                        ${venueHtml}
                        ${priceHtml}
                        ${scoreHtml}
                    </div>
                </div>
            `;
        }
        function render() {
            try {
                const feed = document.getElementById('feed');
                const countEl = document.getElementById('count');
                if (!feed) return;
                let filtered = allEvents;
                if (currentDateFilter === 'today') filtered = filtered.filter(isToday);
                else if (currentDateFilter === 'tomorrow') filtered = filtered.filter(isTomorrow);
                else if (currentDateFilter === 'weekend') filtered = filtered.filter(isWeekend);
                else if (currentDateFilter === 'week') filtered = filtered.filter(isThisWeek);
                if (currentCategoryFilter === 'free') {
                    filtered = filtered.filter(e => (e.price || '').toLowerCase().includes('бесплат') || (e.price || '').toLowerCase().includes('свобод'));
                } else if (currentCategoryFilter !== 'all') {
                    filtered = filtered.filter(e => (e.category === currentCategoryFilter) || (e.kind === currentCategoryFilter));
                }
                if (searchQuery) {
                    const q = searchQuery.toLowerCase();
                    filtered = filtered.filter(e => {
                        const text = ((e.title || '') + ' ' + (e.desc || '') + ' ' + (e.venue || '')).toLowerCase();
                        return text.includes(q);
                    });
                }
                filtered = sortEvents(filtered);
                if (countEl) countEl.textContent = filtered.length + ' событий';
                if (filtered.length === 0) {
                    feed.innerHTML = '<div class="empty">Ничего не найдено. Попробуй другой фильтр.</div>';
                    return;
                }
                feed.innerHTML = filtered.map((e, idx) => renderCard(e, idx)).join('');
                window.currentFiltered = filtered;
            } catch (err) {
                console.error('RENDER ERROR:', err);
                const feed = document.getElementById('feed');
                if (feed) feed.innerHTML = '<div class="empty">Ошибка рендера: ' + err.message + '</div>';
            }
        }
        function renderWithScores(scored) {
            const feed = document.getElementById('feed');
            const countEl = document.getElementById('count');
            if (!feed) return;
            if (countEl) countEl.textContent = scored.length + ' событий';
            if (scored.length === 0) {
                feed.innerHTML = '<div class="empty">Ничего не найдено по смыслу. Попробуй другой запрос.</div>';
                return;
            }
            feed.innerHTML = scored.map((s, idx) => renderCard(s.event, idx, s.score)).join('');
            window.currentFiltered = scored.map(s => s.event);
        }
        function renderAll() { render(); }
        function showToast(msg) {
            const t = document.getElementById('toast');
            if (!t) return;
            t.textContent = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 2000);
        }
        function openSidebar(index) {
            const e = window.currentFiltered[index];
            if (!e) return;
            const content = document.getElementById('card-info-content');
            const card3d = document.getElementById('card-3d');
            const loadingImg = document.getElementById('card-3d-loading');
            const loadingInfo = document.getElementById('card-info-loading');
            const sidebarInner = document.getElementById('sidebar-inner');
            if (!content || !card3d) return;
            if (!e.image) sidebarInner.classList.add('no-image');
            else sidebarInner.classList.remove('no-image');
            if (loadingImg) loadingImg.classList.remove('hidden');
            if (loadingInfo) loadingInfo.classList.remove('hidden');
            const oldImg = card3d.querySelector('img');
            if (oldImg) oldImg.remove();
            resetRotation();
            document.getElementById('sidebar').classList.add('active');
            document.getElementById('overlay').classList.add('active');
            document.body.style.overflow = 'hidden';
            if (e.image) {
                const img = new Image();
                img.onload = () => {
                    if (loadingImg) loadingImg.classList.add('hidden');
                    card3d.insertBefore(img, card3d.firstChild);
                };
                img.onerror = () => {
                    if (loadingImg) loadingImg.classList.add('hidden');
                    sidebarInner.classList.add('no-image');
                };
                img.alt = e.title || '';
                img.src = e.image;
            }
            const isFree = (e.price || '').toLowerCase().includes('бесплат') || (e.price || '').toLowerCase().includes('свобод');
            const tagHtml = e.source ? `<div class="card-info-tag">@${escapeHtml(e.source)}</div>` : '';
            const fullText = e.raw || e.desc || 'Описание отсутствует.';

            // ─── Не показываем пустые поля ───
            const venueBlock = e.venue ? `
                <div class="card-info-meta-item">
                    <span class="icon">📍</span>
                    <div><div class="label">Место</div><div class="value">${escapeHtml(e.venue)}</div></div>
                </div>` : '';
            const priceBlock = e.price ? `
                <div class="card-info-meta-item">
                    <span class="icon">💰</span>
                    <div><div class="label">Цена</div><div class="value ${isFree ? 'price-free' : ''}">${escapeHtml(e.price)}</div></div>
                </div>` : '';

            setTimeout(() => {
                content.innerHTML = `
                    ${tagHtml}
                    <h1 class="card-info-title">${escapeHtml(e.title) || 'Без названия'}</h1>
                    <div class="card-info-meta">
                        <div class="card-info-meta-item">
                            <span class="icon">📅</span>
                            <div><div class="label">Дата и время</div><div class="value">${formatDate(e)}</div></div>
                        </div>
                        ${venueBlock}
                        ${priceBlock}
                    </div>
                    <div class="card-info-text">${escapeHtml(fullText)}</div>
                    <div class="card-info-actions">
                        ${e.source_link ? `<a class="card-info-btn primary" href="${e.source_link}" target="_blank" rel="noopener">📱 Открыть в Telegram</a>` : ''}
                        <button class="card-info-btn secondary" onclick="downloadICS(${index})">📅 В календарь</button>
                        <button class="card-info-btn secondary" onclick="shareEvent(${index})">🔗 Поделиться</button>
                        <button class="card-info-btn secondary" onclick="closeSidebar()">Закрыть</button>
                    </div>
                `;
                if (loadingInfo) loadingInfo.classList.add('hidden');
            }, 150);
        }
        function shareEvent(index) {
            const e = window.currentFiltered[index];
            if (!e) return;
            const text = `${e.title}\n${e.source_link || ''}`;
            if (navigator.share) {
                navigator.share({ title: e.title, text: text }).catch(() => {});
            } else {
                navigator.clipboard.writeText(text).then(() => showToast('Скопировано!')).catch(() => showToast('Не удалось скопировать'));
            }
        }
        function downloadICS(index) {
            const e = window.currentFiltered[index];
            if (!e) return;
            if (!e.start) { showToast('Дата события не указана'); return; }
            const start = new Date(e.start);
            const end = new Date(start.getTime() + 2 * 60 * 60 * 1000);
            const fmt = d => d.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
            const ics = [
                "BEGIN:VCALENDAR", "VERSION:2.0", "BEGIN:VEVENT",
                `DTSTART:${fmt(start)}`, `DTEND:${fmt(end)}`,
                `SUMMARY:${e.title || "Событие"}`,
                `DESCRIPTION:${(e.desc || "").replace(/\n/g, ' ').substring(0, 200)}`,
                `LOCATION:${e.venue || ""}`, `URL:${e.source_link || ""}`,
                "END:VEVENT", "END:VCALENDAR"
            ].join("\r\n");
            const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${(e.title || "event").substring(0, 40)}.ics`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('Скачано!');
        }
        function closeSidebar() {
            document.getElementById('sidebar').classList.remove('active');
            document.getElementById('overlay').classList.remove('active');
            document.body.style.overflow = '';
            resetRotation();
        }
        const card3d = document.getElementById('card-3d');
        const card3dWrap = document.getElementById('card-3d-wrap');
        let rotX = 0, rotY = 0;
        let isDragging = false, startX = 0, startY = 0, startRotX = 0, startRotY = 0;
        function applyRotation() {
            if (!card3d) return;
            card3d.style.transform = `rotateX(${rotX}deg) rotateY(${rotY}deg)`;
        }
        function resetRotation() {
            rotX = 0; rotY = 0;
            if (!card3d) return;
            card3d.style.transition = 'transform 0.6s cubic-bezier(0.34, 1.3, 0.64, 1)';
            applyRotation();
            setTimeout(() => { card3d.style.transition = 'transform 0.1s ease-out'; }, 600);
        }
        function onStart(x, y) {
            isDragging = true;
            startX = x; startY = y;
            startRotX = rotX; startRotY = rotY;
            if (card3dWrap) card3dWrap.classList.add('touched');
            if (card3d) card3d.style.transition = 'none';
        }
        function onMove(x, y) {
            if (!isDragging) return;
            const dx = x - startX, dy = y - startY;
            rotY = Math.max(-40, Math.min(40, startRotY + dx * 0.4));
            rotX = Math.max(-40, Math.min(40, startRotX - dy * 0.4));
            applyRotation();
        }
        function onEnd() {
            isDragging = false;
            if (!card3d) return;
            card3d.style.transition = 'transform 0.6s cubic-bezier(0.34, 1.3, 0.64, 1)';
            rotX = 0; rotY = 0;
            applyRotation();
        }
        if (card3d) {
            card3d.addEventListener('mousedown', (e) => { onStart(e.clientX, e.clientY); e.preventDefault(); });
            document.addEventListener('mousemove', (e) => onMove(e.clientX, e.clientY));
            document.addEventListener('mouseup', onEnd);
            card3d.addEventListener('touchstart', (e) => { const t = e.touches[0]; onStart(t.clientX, t.clientY); }, { passive: true });
            card3d.addEventListener('touchmove', (e) => { const t = e.touches[0]; onMove(t.clientX, t.clientY); }, { passive: true });
            card3d.addEventListener('touchend', onEnd);
        }
        document.getElementById('sidebar-close').addEventListener('click', closeSidebar);
        document.getElementById('overlay').addEventListener('click', closeSidebar);
        document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeSidebar(); });
        document.getElementById('search').addEventListener('input', (e) => {
            searchQuery = e.target.value; render();
        });
        document.getElementById('ai-query').addEventListener('input', (e) => {
            const query = e.target.value;
            if (query.length > 3) aiSearch(query);
            else if (query.length === 0) renderAll();
        });
        document.getElementById('date-filters').addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON') {
                document.querySelectorAll('#date-filters button').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                currentDateFilter = e.target.dataset.date;
                render();
            }
        });
        document.getElementById('category-filters').addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON') {
                document.querySelectorAll('#category-filters button').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                currentCategoryFilter = e.target.dataset.category;
                render();
            }
        });
        window.openSidebar = openSidebar;
        window.closeSidebar = closeSidebar;
        window.shareEvent = shareEvent;
        window.downloadICS = downloadICS;
        setTimeout(() => {
            if (globalLoader && !globalLoader.classList.contains('hidden')) {
                globalLoader.classList.add('hidden');
            }
        }, 20000);
        load();
        initAI();
    </script>
</body>
</html>
