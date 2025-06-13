# 🧠 AdsPower MetaMask Automation (Python)

Автоматизированный инструмент для работы с AdsPower-профилями через Playwright. Проект предназначен для **массового запуска автоматизированных действий в браузере** — от установки MetaMask до взаимодействия с Web3-сайтами, краудлеймами, дропами и другими dApps.

Подходит для Web3 фарма, тестнетов, абуза активностей, автоматизации повторяющихся действий и интеграции с антидетект-средой через AdsPower.

---

## ⚙️ Возможности

- ✅ Массовая установка MetaMask в профили AdsPower
- 🔐 Безопасная генерация паролей и работа с публичными адресами
- 🌐 Автоматизация dApps и сайтов через Playwright
- 🧠 Связка: `публичный адрес` → `AdsPower профиль` → `MetaMask`
- 🔁 Логика повторов, проверок и отслеживания статуса
- 📄 Логирование через `loguru`
- 🔌 Работа с локальным AdsPower API
- 🧰 Гибкая модульная структура под любые Web3-сценарии

---

## 📁 Структура проекта

```
ads_workpiece/
├── .env
├── config/
│   └── settings.py
├── core/
│   ├── get_metamask_password.py
│   ├── get_wallets_data.py
│   └── result_tracker.py
├── scripts/
│   ├── add_metamask/
│   │   ├── add_metamask.py
│   │   ├── get_seed.py
│   │   ├── addresses.txt       # Публичные адреса кошельков (один в строку)
│   │   └── profiles.txt        # ID профилей AdsPower (в том же порядке)
│   └── #template/
│       ├── main.py
│       ├── addresses.txt
│       └── profiles.txt
├── utils/
│   └── adspower_api_utils.py
├── requirements.txt
└── README.md
```

---

## 🧪 Пример `.env`

```env
ENCRYPTED_WALLETS_PATH=/путь/к/wallets.csv.enc
WALLET_SOURCE=keychain
WALLET_KEY_PATH=
USE_PROXY=true
LOG_LEVEL=INFO
```

---

## 🚀 Быстрый старт

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Создайте `.env` (см. выше)

3. Подготовьте файлы:
   - `addresses.txt`: публичные адреса (по одному в строке)
   - `profiles.txt`: соответствующие ID профилей AdsPower

4. Запустите скрипт:

```bash
python scripts/add_metamask/add_metamask.py
```

---

## 📌 Заметки

- Порядок адресов и профилей должен совпадать
- AdsPower должен быть запущен и доступен по локальному API
- Логика легко расширяется под любые dApps и сайты

---

## 📺 Видео-гайд

YouTube: **https://www.youtube.com/@scryptoni**  
Telegram: [@scryptonia](https://t.me/+FuS4BPeF_6RmNjk8)
