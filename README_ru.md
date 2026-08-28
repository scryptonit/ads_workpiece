# 🧠 AdsPower Workpiece (Python)

Модульный фреймворк для **массовой автоматизации браузерных действий** через антидетект-профили AdsPower и Playwright/Patchright.

Заготовка (workpiece) под любые сценарии: Web3-фарм и тестнеты, установка и работа с MetaMask, соцактивности в X (Twitter) и Discord, регистрация почт, решение капчи и генерация текстов через ИИ.

---

## ⚙️ Возможности

- 🔌 Управление профилями AdsPower через локальное API (запуск, остановка, очистка)
- 🌐 Автоматизация сайтов и dApps через Playwright / Patchright (CDP-подключение)
- 🦊 Массовая установка MetaMask (v13.13) и авторизация в кошельке
- 🐦 Полный набор действий в X: подписка, лайк, репост, комментарий, цитата, тег друзей
- 💬 Discord: регистрация, подтверждение почты, прохождение верификации
- 🤖 Генерация текстов и распознавание картинок через OpenAI API
- 🔓 Решение image-капчи через 2Captcha
- 📧 Получение кодов и ссылок из почты (mail.tm API и IMAP)
- 🖱️ Человекоподобные клики и ввод текста (кривые траектории, опечатки, паузы)
- 🔁 Отслеживание результатов и возобновление с места остановки
- 🔐 Шифрованное хранилище кошельков (Fernet) и детерминированные пароли
- 📄 Логирование через `loguru`

---

## 📁 Структура проекта

```
ads_workpiece/
├── .env_example                     # шаблон переменных окружения
├── .gitignore
├── README_ru.md / README_en.md
├── requirements.txt
├── config/
│   └── settings.py                  # единая точка чтения .env + настройка логгера
├── core/
│   ├── get_wallets_data.py          # расшифровка CSV с кошельками (Fernet)
│   ├── get_seed.py                  # связка профиль → адрес → seed-фраза
│   ├── get_metamask_password.py     # детерминированный пароль по ID профиля
│   ├── metamask_handler.py          # авторизация и подтверждение в MetaMask
│   ├── get_email_code.py            # коды/ссылки из почты через mail.tm API
│   ├── get_imap_email_code.py       # коды/ссылки из почты через IMAP
│   ├── gpt_answer.py                # запросы к OpenAI (текст и картинки)
│   ├── solve_captcha.py             # решение image-капчи через 2Captcha
│   └── result_tracker.py            # учёт успешно обработанных профилей
├── utils/
│   ├── adspower_api_utils.py        # локальное API AdsPower
│   ├── mouse_random_click.py        # человекоподобный клик мышью (patchright)
│   ├── playwright_mouse_random_click.py  # то же для чистого playwright
│   └── human_type.py                # человекоподобный ввод текста / вставка
├── helper/
│   └── generate_emails.py           # массовое создание почт (mail.tm)
└── scripts/
    ├── #template/                   # шаблон для нового скрипта
    │   ├── main.py
    │   ├── addresses_example.txt
    │   └── profiles_example.txt
    ├── add_metamask/                # массовая установка MetaMask
    │   ├── add_metamask.py
    │   ├── get_seed.py
    │   ├── addresses_example.txt
    │   └── profiles_example.txt
    ├── x/                           # автоматизация X (Twitter)
    │   ├── main.py
    │   ├── credentials.txt.example
    │   ├── reply.txt.example
    │   ├── quote.txt.example
    │   └── friends.txt.example
    └── discord/                     # автоматизация Discord
        ├── first_login.py           # подготовка аккаунтов
        ├── profiles.txt             # пустые заготовки под ваши данные
        ├── credentials.txt
        ├── addresses.txt
        ├── email.txt
        └── examples/
            ├── zeko.py              # пример: верификация с капчей
            └── hyper.py             # пример: верификация через ИИ
```

Проект собран слоями: `config/` (настройки и логгер) → `core/` + `utils/` (переиспользуемая логика) → `scripts/<проект>/` (конкретные сценарии). Все скрипты следуют одному шаблону: запуск профиля AdsPower → подключение Playwright по CDP → сценарий → запись результата → гарантированное закрытие браузера.

---

## 📋 Требования

- **Python 3.11+** (используется синтаксис `str | None`)
- **AdsPower** установлен, запущен, и в его настройках **включён локальный API**
- Аккаунты сервисов под ваш сценарий: OpenAI, 2Captcha, почта
- macOS — если ключ шифрования кошельков хранится в Keychain

---

## 🚀 Быстрый старт

**1. Установка зависимостей**

```bash
pip install -r requirements.txt
```

**2. Настройка окружения**

Скопируйте шаблон и заполните своими значениями:

```bash
cp .env_example .env
```

```env
# AdsPower local API
ADSPOWER_API_URL=http://localhost:50325
DISPOSABLE_PROFILE_ID=999

# Кошельки
ENCRYPTED_WALLETS_PATH=/путь/к/wallets.csv.enc
WALLET_SOURCE=keychain
WALLET_KEY_PATH=

# OpenAI / GPT
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o

# 2Captcha
TWOCAPTCHA_API_KEY=your_2captcha_api_key

# Логирование
LOG_LEVEL=INFO
```

| Переменная | Назначение |
|---|---|
| `ADSPOWER_API_URL` | Адрес локального API AdsPower |
| `DISPOSABLE_PROFILE_ID` | ID одноразового профиля для режима `DISPOSABLE` |
| `ENCRYPTED_WALLETS_PATH` | Путь к зашифрованному CSV с кошельками |
| `WALLET_SOURCE` | Откуда брать ключ шифрования: `keychain` или `usb` |
| `WALLET_KEY_PATH` | Путь к файлу ключа (только при `WALLET_SOURCE=usb`) |
| `OPENAI_API_KEY` | Ключ OpenAI |
| `OPENAI_MODEL` | Любая модель OpenAI, доступная вашему ключу |
| `TWOCAPTCHA_API_KEY` | Ключ 2Captcha |
| `LOG_LEVEL` | Уровень логирования (`INFO`, `DEBUG`, ...) |

Нужны только те ключи, которые использует ваш сценарий: без ИИ-текстов не нужен `OPENAI_API_KEY`, без капчи — `TWOCAPTCHA_API_KEY`, без кошельков — блок `WALLET_*`.

**3. Подготовка данных**

В папке нужного скрипта переименуйте `*_example.txt` в рабочие файлы и заполните своими данными.

**4. Запуск**

Скрипты импортируют модули из корня проекта, поэтому корень должен быть в `PYTHONPATH`:

```bash
PYTHONPATH=. python scripts/x/main.py
PYTHONPATH=. python scripts/add_metamask/add_metamask.py
PYTHONPATH=. python scripts/discord/first_login.py
```

В PyCharm корень проекта подставляется автоматически — там достаточно обычного запуска файла.

> AdsPower должен быть запущен, а локальный API включён в его настройках.

---

## 📄 Форматы файлов данных

Все файлы работают по принципу **строка N = профиль N** — порядок строк должен совпадать с `profiles.txt`.

| Файл | Формат | Описание |
|---|---|---|
| `profiles.txt` | `1` | ID профилей AdsPower, по одному в строке |
| `addresses.txt` | `0xAbC...` | Публичные адреса кошельков |
| `email.txt` / `accounts.txt` | `email@domain.com:password` | Почта и пароль через двоеточие |
| `credentials.txt` (X) | `username\|password\|email\|email_password\|2fa\|auth_token\|ct0` | 7 полей через `\|` |
| `credentials.txt` (Discord) | `login:password:token` | Логин, пароль и токен через двоеточие |
| `reply.txt` / `quote.txt` | обычный текст | Текст комментария/цитаты, по одному на профиль |
| `friends.txt` | `alice,bob,carol` | Ники для тега, через запятую |

Поле `2fa` в `credentials.txt` для X — это base32-секрет, из которого код генерируется на лету через `pyotp`.

Результаты работы сохраняются в файл `{имя_скрипта}_results.txt` в формате `id:1` — при перезапуске обработанные профили пропускаются.

### 🔐 Хранилище кошельков

Нужно только скриптам, работающим с MetaMask. Кошельки лежат в CSV, зашифрованном Fernet:

```csv
address,private_key,seed
0xAbC...,0x123...,word1 word2 word3 ...
```

Путь к зашифрованному файлу указывается в `ENCRYPTED_WALLETS_PATH`, а ключ шифрования берётся по значению `WALLET_SOURCE`:

- **`keychain`** — из macOS Keychain. Запись должна существовать с аккаунтом `mishka` и сервисом `uncle_mischa`:
  ```bash
  security add-generic-password -a mishka -s uncle_mischa -w '<ваш_fernet_ключ>'
  ```
- **`usb`** — из файла по пути `WALLET_KEY_PATH` (например, со съёмного носителя)

Проверить расшифровку можно так — выведет список адресов:

```bash
PYTHONPATH=. python core/get_wallets_data.py
```

---

## 🧩 Основные модули

### `config/settings.py`
Единая точка чтения `.env` и настройка `loguru` (вывод в консоль + файл в `logs/` с ротацией). Все остальные модули берут настройки отсюда, а не из `os.getenv` напрямую.

### `utils/adspower_api_utils.py`
Работа с локальным API AdsPower.

```python
start_browser(profile_number, headless=False)   # запуск профиля → WebSocket-адрес для CDP
close_browser(profile_number)                   # остановка профиля
check_browser_status(profile_number)            # проверка, запущен ли профиль
clear_profile_data(profile_number, types=None)  # очистка данных профиля
get_user_id_by_serial(serial_number)            # серийный номер → внутренний ID
```

### `utils/mouse_random_click.py` и `utils/human_type.py`
Имитация живого поведения: движение мыши по кривым траекториям с дрожанием и «прицеливанием», плавный скролл к элементу, а также ввод текста с опечатками, паузами между словами и вставкой из буфера.

```python
human_like_mouse_click(locator, time_sleep=2.0, speed_mode="fast", no_scroll=False)
human_like_type(locator, text, speed_mode="paste", clear_before=True, focus_with_click=True)
```

Профили скорости: `fast` / `medium` / `slow` / `manual`. Для ввода дополнительно `paste` — вставка через буфер обмена.

### `core/gpt_answer.py`
Запросы к OpenAI. Промпт пишется вызывающей стороной — модуль не содержит скрытых инструкций.

```python
ask(prompt, model=None, max_tokens=100, temperature=0.0)
ask_image(prompt, image, detail="high", model=None, max_tokens=100)
```

`ask_image` принимает URL, путь к файлу или байты (например, результат `locator.screenshot()`). Параметр `temperature` повышают, когда нужен разный текст для разных профилей.

### `core/solve_captcha.py`
Решение image-капчи через 2Captcha.

```python
solve_image_captcha(image, length=None, numbers=False, *, timeout=120, poll=5.0, api_key=None)
```

Принимает ссылку, путь, base64 или байты. `numbers=True` — только цифры, `length` — точная длина ответа.

### `core/get_email_code.py` и `core/get_imap_email_code.py`
Ожидание письма и извлечение из него кода подтверждения или ссылки — через API mail.tm либо по IMAP.

```python
get_email_code(email, password, ...)        # mail.tm
get_email_link(email, password, mask, ...)  # mail.tm
get_email_imap_code(email, password, ...)   # IMAP
get_email_imap_link(email, password, mask, ...)
```

IMAP-хост определяется автоматически по домену адреса (Gmail, Яндекс, Mail.ru, Outlook, Yahoo, iCloud, Rambler).

### `core/get_wallets_data.py`, `core/get_seed.py`, `core/get_metamask_password.py`
Работа с кошельками: расшифровка CSV (Fernet, ключ из Keychain или файла), связка `профиль → адрес → seed`, генерация детерминированного пароля MetaMask по ID профиля (PBKDF2-HMAC-SHA256). Пароли нигде не хранятся — всегда выводятся заново из ключа.

### `core/metamask_handler.py`
Авторизация в расширении MetaMask и подтверждение транзакций/подписей во всплывающем окне.

```python
auth_mm(page, profile)                              # вход по паролю профиля
auth_mm_disp(page, wallet_address, profile_id=None) # вход для одноразового профиля
confirm_mm(context)                                 # подтверждение в попапе
```

### `core/result_tracker.py`
Учёт успешно обработанных профилей в файле `{имя_скрипта}_results.txt`. При перезапуске обработанные профили пропускаются.

### `helper/generate_emails.py`
Массовое создание одноразовых почтовых ящиков через mail.tm. Запускается отдельно, спрашивает нужное количество и сохраняет результат в `helper/email.txt` в формате `email:password` — именно его потом читают скрипты.

```bash
python helper/generate_emails.py
```

---

## 📜 Скрипты

### `scripts/x/main.py` — автоматизация X (Twitter)

Полный набор социальных действий под одну кампанию:

| Функция | Действие |
|---|---|
| `x_follow(page, username)` | Подписка на аккаунт |
| `x_like(page, tweet_id)` | Лайк твита |
| `x_retweet(page, tweet_id)` | Репост |
| `x_reply(page, tweet_id, text, username)` | Комментарий |
| `x_quote(page, tweet_id, text, username)` | Цитата с текстом |
| `x_tag_friends(page, tweet_id, friends, username)` | Комментарий с тегом друзей |

**Особенности:**

- **Два способа входа** — через форму (логин/пароль/2FA) или подстановкой cookies `auth_token` + `ct0` (берутся из DevTools → Application → Cookies уже авторизованного аккаунта)
- **Тексты комментариев** — либо из `reply.txt`/`quote.txt`, либо генерируются ИИ по содержанию твита (флаг `USE_AI_COMMENTS`)
- **Проверка результата** — состояние кнопки в DOM (`Following`, `unlike`, `unretweet`) и перехват сетевого ответа API, из которого берётся ID созданного поста
- **Ссылки на посты** — для комментариев, цитат и тегов сохраняется прямая ссылка на созданный твит
- **Возобновление** — результаты пишутся в `{имя_скрипта}_results.json`, при повторном запуске уже выполненные действия пропускаются, а полностью обработанные профили не запускаются вовсе

Формат файла результатов:

```json
{
  "1": {
    "hyperliquid": {
      "follow":  { "HyperliquidX": "HyperliquidX" },
      "like":    { "2090122188074491951": "2090122188074491951" },
      "reply":   { "2090122188074491951": "https://x.com/user/status/2092939173044883885" }
    }
  }
}
```

Настройки в начале файла:

```python
HEADLESS_NEW = False       # запуск без интерфейса
T = 15                     # пауза между профилями, сек
SHUFFLE_WALLETS = True     # случайный порядок обработки профилей
USE_AI_COMMENTS = True     # True — тексты пишет ИИ, False — берутся из файлов
EXPECTED_ACTIONS = 6       # сколько успешных действий = профиль отработан
```

### `scripts/add_metamask/add_metamask.py`
Массовая установка MetaMask (v13.13) в профили AdsPower: импорт seed-фразы, установка сгенерированного пароля, прохождение экранов онбординга. В конце открывает «Receive» и сверяет адрес кошелька с ожидаемым — только при совпадении профиль отмечается успешным.

> Скрипт импортирует соседний `get_seed.py`, поэтому запускать его нужно из его собственной папки.

### `scripts/discord/first_login.py`
Подготовка Discord-аккаунтов «под ключ»:

- настройка расширения-солвера капчи CapGuru
- вход в Discord по логину/паролю или подстановкой токена в `localStorage`
- обработка экрана «new location detected» — ссылка подтверждения забирается из почты по IMAP
- смена пароля Discord и пароля привязанной почты
- сохранение итоговых данных в `discord.txt` (`профиль:логин:пароль:токен`)

Прогресс отслеживается **пошагово** в `first_login_steps.txt` — при перезапуске уже выполненные шаги пропускаются.

### `scripts/discord/examples/`
Готовые примеры сценариев под конкретные серверы:

- **`zeko.py`** — принятие инвайта, выбор роли, верификация с решением цифровой капчи через 2Captcha
- **`hyper.py`** — верификация выбором эмодзи: нужное слово читается из embed-сообщения, а соответствие эмодзи определяется через ИИ

### `scripts/#template/main.py`
Шаблон для нового скрипта: подключение к профилю, загрузка данных из файлов, обработка ошибок, учёт результатов. Копируйте папку и пишите свою логику в блоке `activity()`.

---

## 📌 Заметки

- Порядок строк во всех файлах данных должен совпадать с `profiles.txt`
- Обязателен только `profiles.txt` — остальные файлы опциональны, при их отсутствии в лог выводится предупреждение
- Не запускайте другие действия мышью в окне браузера, пока работает скрипт — это конфликтует с автоматизацией
- Файлы с реальными данными (`credentials.txt`, `profiles.txt`, `.env` и т.д.) не должны попадать в репозиторий

---

## 📺 Контакты

YouTube: **https://www.youtube.com/@scryptoni**
Telegram: [@scryptonia](https://t.me/+FuS4BPeF_6RmNjk8)
