# 🧠 AdsPower MetaMask Automation (Python)

Automated tool to interact with AdsPower profiles using Playwright. This project is designed for **mass browser automation** — from MetaMask installation to interaction with Web3 dApps, faucets, airdrops, and other onchain activities.

Ideal for Web3 farming, testnets, activity automation, and seamless integration with an anti-detect environment via AdsPower.

---

## ⚙️ Features

- ✅ Mass MetaMask installation into AdsPower profiles
- 🔐 Secure password generation and use of public wallet addresses
- 🌐 Automate Web3 dApps and sites via Playwright
- 🧠 One-to-one: `public wallet address` → `AdsPower profile` → `MetaMask`
- 🔁 Retry logic and result tracking
- 📄 Logging via `loguru`
- 🔌 Works through local AdsPower API
- 🧰 Modular structure ready for future dApps and automation scripts
- MetaMask v13.13

---

## 📁 Project Structure

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
│   │   ├── addresses.txt       # Public wallet addresses (one per line)
│   │   └── profiles.txt        # Matching AdsPower profile IDs
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

## 🧪 Example `.env`

```env
ENCRYPTED_WALLETS_PATH=/path/to/wallets.csv.enc
WALLET_SOURCE=keychain
WALLET_KEY_PATH=
USE_PROXY=true
LOG_LEVEL=INFO
DISPOSABLE_PROFILE_ID=999
```

---

## 🚀 Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file

3. Prepare data files:
   - `addresses.txt`: public wallet addresses (one per line)
   - `profiles.txt`: matching AdsPower profile IDs (same order)

4. Run the script:

```bash
python scripts/add_metamask/add_metamask.py
```

---

## 📌 Notes

- Order of addresses and profiles must match
- AdsPower must be running and accessible via local API
- Easily extendable for any Web3 dApp or site automation

---

## 📺 Video Guide

YouTube: **https://www.youtube.com/@scryptoni**  
Telegram: [@scryptonia](https://t.me/+FuS4BPeF_6RmNjk8)
