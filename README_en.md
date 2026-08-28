# 🧠 AdsPower Workpiece (Python)

A modular framework for **mass browser automation** through AdsPower anti-detect profiles and Playwright/Patchright.

A workpiece for any scenario: Web3 farming and testnets, MetaMask setup and usage, social activity on X (Twitter) and Discord, mailbox registration, captcha solving and AI-generated text.

---

## ⚙️ Features

- 🔌 AdsPower profile management via local API (start, stop, clear data)
- 🌐 Website and dApp automation via Playwright / Patchright (CDP connection)
- 🦊 Mass MetaMask installation (v13.13) and wallet unlocking
- 🐦 Full set of X actions: follow, like, retweet, reply, quote, tag friends
- 💬 Discord: sign-up, email confirmation, server verification
- 🤖 Text generation and image recognition via OpenAI API
- 🔓 Image captcha solving via 2Captcha
- 📧 Fetching codes and links from email (mail.tm API and IMAP)
- 🖱️ Human-like clicks and typing (curved trajectories, typos, pauses)
- 🔁 Result tracking and resume-from-where-you-stopped
- 🔐 Encrypted wallet storage (Fernet) and deterministic passwords
- 📄 Logging via `loguru`

---

## 📁 Project Structure

```
ads_workpiece/
├── .env_example                     # environment variables template
├── .gitignore
├── README_ru.md / README_en.md
├── requirements.txt
├── config/
│   └── settings.py                  # single .env entry point + logger setup
├── core/
│   ├── get_wallets_data.py          # wallet CSV decryption (Fernet)
│   ├── get_seed.py                  # profile → address → seed phrase mapping
│   ├── get_metamask_password.py     # deterministic password from profile ID
│   ├── metamask_handler.py          # MetaMask unlock and confirmation
│   ├── get_email_code.py            # codes/links from email via mail.tm API
│   ├── get_imap_email_code.py       # codes/links from email via IMAP
│   ├── gpt_answer.py                # OpenAI requests (text and images)
│   ├── solve_captcha.py             # image captcha solving via 2Captcha
│   └── result_tracker.py            # tracking of successfully processed profiles
├── utils/
│   ├── adspower_api_utils.py        # AdsPower local API
│   ├── mouse_random_click.py        # human-like mouse click (patchright)
│   ├── playwright_mouse_random_click.py  # same for plain playwright
│   └── human_type.py                # human-like typing / clipboard paste
├── helper/
│   └── generate_emails.py           # bulk mailbox creation (mail.tm)
└── scripts/
    ├── #template/                   # template for a new script
    │   ├── main.py
    │   ├── addresses_example.txt
    │   └── profiles_example.txt
    ├── add_metamask/                # mass MetaMask installation
    │   ├── add_metamask.py
    │   ├── get_seed.py
    │   ├── addresses_example.txt
    │   └── profiles_example.txt
    ├── x/                           # X (Twitter) automation
    │   ├── main.py
    │   ├── credentials.txt.example
    │   ├── reply.txt.example
    │   ├── quote.txt.example
    │   └── friends.txt.example
    └── discord/                     # Discord automation
        ├── first_login.py           # account preparation
        ├── profiles.txt             # empty placeholders for your data
        ├── credentials.txt
        ├── addresses.txt
        ├── email.txt
        └── examples/
            ├── zeko.py              # example: verification with captcha
            └── hyper.py             # example: verification via AI
```

The project is built in layers: `config/` (settings and logger) → `core/` + `utils/` (reusable logic) → `scripts/<project>/` (concrete scenarios). Every script follows the same pattern: start an AdsPower profile → connect Playwright over CDP → run the scenario → record the result → guaranteed browser shutdown.

---

## 📋 Requirements

- **Python 3.11+** (the code uses `str | None` syntax)
- **AdsPower** installed, running, with the **local API enabled** in its settings
- Accounts for the services your scenario needs: OpenAI, 2Captcha, email
- macOS — if the wallet encryption key is stored in Keychain

---

## 🚀 Quick Start

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Configure the environment**

Copy the template and fill in your own values:

```bash
cp .env_example .env
```

```env
# AdsPower local API
ADSPOWER_API_URL=http://localhost:50325
DISPOSABLE_PROFILE_ID=999

# Wallets
ENCRYPTED_WALLETS_PATH=/path/to/wallets.csv.enc
WALLET_SOURCE=keychain
WALLET_KEY_PATH=

# OpenAI / GPT
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o

# 2Captcha
TWOCAPTCHA_API_KEY=your_2captcha_api_key

# Logging
LOG_LEVEL=INFO
```

| Variable | Purpose |
|---|---|
| `ADSPOWER_API_URL` | AdsPower local API address |
| `DISPOSABLE_PROFILE_ID` | Disposable profile ID for `DISPOSABLE` mode |
| `ENCRYPTED_WALLETS_PATH` | Path to the encrypted wallet CSV |
| `WALLET_SOURCE` | Where to read the encryption key from: `keychain` or `usb` |
| `WALLET_KEY_PATH` | Key file path (only when `WALLET_SOURCE=usb`) |
| `OPENAI_API_KEY` | OpenAI key |
| `OPENAI_MODEL` | Any OpenAI model available to your key |
| `TWOCAPTCHA_API_KEY` | 2Captcha key |
| `LOG_LEVEL` | Logging level (`INFO`, `DEBUG`, ...) |

You only need the keys your scenario actually uses: no AI texts — no `OPENAI_API_KEY`, no captcha — no `TWOCAPTCHA_API_KEY`, no wallets — no `WALLET_*` block.

**3. Prepare your data**

In the folder of the script you need, rename the `*_example.txt` files into working ones and fill them with your own data.

**4. Run**

The scripts import modules from the project root, so the root must be on `PYTHONPATH`:

```bash
PYTHONPATH=. python scripts/x/main.py
PYTHONPATH=. python scripts/add_metamask/add_metamask.py
PYTHONPATH=. python scripts/discord/first_login.py
```

In PyCharm the project root is added automatically — running the file normally is enough there.

> AdsPower must be running with the local API enabled in its settings.

---

## 📄 Data File Formats

All files follow the **line N = profile N** rule — the line order must match `profiles.txt`.

| File | Format | Description |
|---|---|---|
| `profiles.txt` | `1` | AdsPower profile IDs, one per line |
| `addresses.txt` | `0xAbC...` | Public wallet addresses |
| `email.txt` / `accounts.txt` | `email@domain.com:password` | Email and password separated by a colon |
| `credentials.txt` (X) | `username\|password\|email\|email_password\|2fa\|auth_token\|ct0` | 7 fields separated by `\|` |
| `credentials.txt` (Discord) | `login:password:token` | Login, password and token separated by colons |
| `reply.txt` / `quote.txt` | plain text | Reply/quote text, one per profile |
| `friends.txt` | `alice,bob,carol` | Usernames to tag, comma-separated |

The `2fa` field in the X `credentials.txt` is a base32 secret — the code is generated on the fly via `pyotp`.

Results are stored in `{script_name}_results.txt` as `id:1` — already processed profiles are skipped on restart.

### 🔐 Wallet Storage

Only needed by the MetaMask-related scripts. Wallets live in a Fernet-encrypted CSV:

```csv
address,private_key,seed
0xAbC...,0x123...,word1 word2 word3 ...
```

The path to the encrypted file goes into `ENCRYPTED_WALLETS_PATH`, and the encryption key is read according to `WALLET_SOURCE`:

- **`keychain`** — from the macOS Keychain. The entry must exist with account `mishka` and service `uncle_mischa`:
  ```bash
  security add-generic-password -a mishka -s uncle_mischa -w '<your_fernet_key>'
  ```
- **`usb`** — from the file at `WALLET_KEY_PATH` (e.g. a removable drive)

You can verify decryption like this — it prints the list of addresses:

```bash
PYTHONPATH=. python core/get_wallets_data.py
```

---

## 🧩 Core Modules

### `config/settings.py`
The single place where `.env` is read and `loguru` is configured (console output plus a rotating file in `logs/`). Every other module takes its settings from here instead of calling `os.getenv` directly.

### `utils/adspower_api_utils.py`
Wrapper around the AdsPower local API.

```python
start_browser(profile_number, headless=False)   # start a profile → WebSocket endpoint for CDP
close_browser(profile_number)                   # stop a profile
check_browser_status(profile_number)            # check whether a profile is running
clear_profile_data(profile_number, types=None)  # clear profile data
get_user_id_by_serial(serial_number)            # serial number → internal ID
```

### `utils/mouse_random_click.py` and `utils/human_type.py`
Emulation of real user behaviour: mouse movement along curved trajectories with jitter and pre-click aiming, smooth scrolling to the element, plus typing with typos, pauses between words and clipboard paste.

```python
human_like_mouse_click(locator, time_sleep=2.0, speed_mode="fast", no_scroll=False)
human_like_type(locator, text, speed_mode="paste", clear_before=True, focus_with_click=True)
```

Speed profiles: `fast` / `medium` / `slow` / `manual`. Typing also supports `paste` — insertion through the clipboard.

### `core/gpt_answer.py`
OpenAI requests. The prompt is written by the caller — the module contains no hidden instructions.

```python
ask(prompt, model=None, max_tokens=100, temperature=0.0)
ask_image(prompt, image, detail="high", model=None, max_tokens=100)
```

`ask_image` accepts a URL, a file path or raw bytes (e.g. the result of `locator.screenshot()`). Raise `temperature` when different profiles need different wording.

### `core/solve_captcha.py`
Image captcha solving via 2Captcha.

```python
solve_image_captcha(image, length=None, numbers=False, *, timeout=120, poll=5.0, api_key=None)
```

Accepts a URL, a path, base64 or raw bytes. `numbers=True` — digits only, `length` — exact answer length.

### `core/get_email_code.py` and `core/get_imap_email_code.py`
Wait for an email and extract a confirmation code or a link from it — either through the mail.tm API or over IMAP.

```python
get_email_code(email, password, ...)        # mail.tm
get_email_link(email, password, mask, ...)  # mail.tm
get_email_imap_code(email, password, ...)   # IMAP
get_email_imap_link(email, password, mask, ...)
```

The IMAP host is resolved automatically from the email domain (Gmail, Yandex, Mail.ru, Outlook, Yahoo, iCloud, Rambler).

### `core/get_wallets_data.py`, `core/get_seed.py`, `core/get_metamask_password.py`
Wallet handling: CSV decryption (Fernet, key from Keychain or a file), `profile → address → seed` mapping, and deterministic MetaMask password generation from the profile ID (PBKDF2-HMAC-SHA256). Passwords are never stored — they are always derived again from the key.

### `core/metamask_handler.py`
Unlocking the MetaMask extension and confirming transactions/signatures in the popup.

```python
auth_mm(page, profile)                              # unlock with the profile password
auth_mm_disp(page, wallet_address, profile_id=None) # seed import for a disposable profile
confirm_mm(context)                                 # confirm in the popup
```

### `core/result_tracker.py`
Tracks successfully processed profiles in `{script_name}_results.txt`. Processed profiles are skipped on restart.

### `helper/generate_emails.py`
Bulk creation of disposable mailboxes via mail.tm. Run it separately — it asks how many you need and saves the result to `helper/email.txt` in `email:password` format, exactly what the scripts' loaders expect.

```bash
python helper/generate_emails.py
```

---

## 📜 Scripts

### `scripts/x/main.py` — X (Twitter) automation

A full set of social actions for a single campaign:

| Function | Action |
|---|---|
| `x_follow(page, username)` | Follow an account |
| `x_like(page, tweet_id)` | Like a tweet |
| `x_retweet(page, tweet_id)` | Repost |
| `x_reply(page, tweet_id, text, username)` | Reply |
| `x_quote(page, tweet_id, text, username)` | Quote with text |
| `x_tag_friends(page, tweet_id, friends, username)` | Reply tagging friends |

**Highlights:**

- **Two login methods** — through the form (username/password/2FA) or by injecting `auth_token` + `ct0` cookies (taken from DevTools → Application → Cookies of an already logged-in account)
- **Reply texts** — either from `reply.txt`/`quote.txt` or generated by AI based on the tweet content (`USE_AI_COMMENTS` flag)
- **Result verification** — button state in the DOM (`Following`, `unlike`, `unretweet`) plus interception of the API network response, which carries the ID of the created post
- **Post links** — replies, quotes and tag posts store a direct link to the created tweet
- **Resume support** — results are written to `{script_name}_results.json`; on the next run finished actions are skipped and fully processed profiles are not launched at all

Result file format:

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

Settings at the top of the file:

```python
HEADLESS_NEW = False       # run without a visible window
T = 15                     # delay between profiles, seconds
SHUFFLE_WALLETS = True     # randomize profile processing order
USE_AI_COMMENTS = True     # True — AI writes the texts, False — read from files
EXPECTED_ACTIONS = 6       # how many successful actions mean the profile is done
```

### `scripts/add_metamask/add_metamask.py`
Mass MetaMask (v13.13) installation into AdsPower profiles: seed phrase import, generated password setup and onboarding screens. At the end it opens "Receive" and compares the wallet address with the expected one — the profile is marked successful only on a match.

> The script imports its neighbouring `get_seed.py`, so it must be run from its own directory.

### `scripts/discord/first_login.py`
End-to-end preparation of Discord accounts:

- CapGuru captcha-solver extension setup
- Discord login by username/password or by injecting a token into `localStorage`
- handling of the "new location detected" screen — the confirmation link is pulled from the mailbox over IMAP
- changing the Discord password and the linked email password
- saving the resulting data into `discord.txt` (`profile:login:password:token`)

Progress is tracked **step by step** in `first_login_steps.txt` — completed steps are skipped on restart.

### `scripts/discord/examples/`
Ready-made scenario examples for specific servers:

- **`zeko.py`** — accepting the invite, picking a role, verification with a numeric captcha solved through 2Captcha
- **`hyper.py`** — emoji-based verification: the target word is read from the embed message and the matching emoji is picked with AI

### `scripts/#template/main.py`
A template for a new script: profile connection, loading data from files, error handling and result tracking. Copy the folder and write your own logic inside the `activity()` block.

---

## 📌 Notes

- The line order in every data file must match `profiles.txt`
- Only `profiles.txt` is required — all other files are optional, a warning is logged when one is missing
- Do not use the mouse in the browser window while the script is running — it conflicts with the automation
- Files with real data (`credentials.txt`, `profiles.txt`, `.env`, etc.) must never be committed to the repository

---

## 📺 Contacts

YouTube: **https://www.youtube.com/@scryptoni**
Telegram: [@scryptonia](https://t.me/+FuS4BPeF_6RmNjk8)
