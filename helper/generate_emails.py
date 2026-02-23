import time
import random
import string
from pathlib import Path
from typing import List, Tuple

import requests
from loguru import logger

MAILTM = "https://api.mail.tm"


def _rnd(n: int = 12) -> str:
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def _get_domains(session: requests.Session) -> List[str]:
    r = session.get(f"{MAILTM}/domains", timeout=20)
    r.raise_for_status()
    items = r.json().get("hydra:member") or []
    if not items:
        raise RuntimeError("mail.tm domains empty")
    domains = [item.get("domain") for item in items if item.get("domain")]
    if not domains:
        raise RuntimeError("mail.tm domains empty")
    return domains


def create_mailbox(session: requests.Session, domains: List[str], max_attempts: int = 50) -> Tuple[str, str]:
    wait_s = 3

    for attempt in range(1, max_attempts + 1):
        domain = random.choice(domains)
        email = f"{_rnd(12)}@{domain}"
        password = _rnd(16)

        r = session.post(
            f"{MAILTM}/accounts",
            json={"address": email, "password": password},
            timeout=20,
        )

        if r.status_code == 422:
            try:
                error_data = r.json()
            except ValueError:
                error_data = {}
            msg = str(error_data.get("detail") or error_data.get("message") or "").lower()
            if "used" in msg or "exists" in msg or "already" in msg:
                continue
            raise RuntimeError(f"mail.tm 422: {error_data or r.text}")

        if r.status_code == 409:
            continue

        if r.status_code == 429:
            logger.warning(f"Rate limited (429). Waiting {wait_s}s before retry ({attempt}/{max_attempts})")
            time.sleep(wait_s)
            wait_s = min(wait_s * 2, 60)
            continue

        r.raise_for_status()
        return email, password

    raise RuntimeError(f"Failed to create mailbox after {max_attempts} attempts")


def create_many_mailboxes(count: int) -> List[Tuple[str, str]]:
    session = requests.Session()
    session.headers.update({"User-Agent": "temp-mailtm/1.0"})

    domains = _get_domains(session)
    accounts: List[Tuple[str, str]] = []

    for i in range(count):
        email, password = create_mailbox(session, domains)
        accounts.append((email, password))
        logger.info(f"[{i + 1}/{count}] Created mailbox: {email}")
        time.sleep(5)

    return accounts


def save_accounts(accounts: List[Tuple[str, str]], filename: str = "email.txt") -> None:
    out_path = Path(filename)
    if not out_path.is_absolute():
        out_path = Path(__file__).resolve().parent / out_path
    with open(out_path, "w", encoding="utf-8") as f:
        for email, password in accounts:
            f.write(f"{email}:{password}\n")


def ask_count() -> int:
    while True:
        raw = input("How many mailboxes to create? (e.g. 1 or 20): ").strip()
        if not raw:
            logger.warning("Please enter a number")
            continue
        if not raw.isdigit():
            logger.warning("Input must be an integer, e.g. 1")
            continue
        count = int(raw)
        if count <= 0:
            logger.warning("Number must be greater than 0")
            continue
        return count


if __name__ == "__main__":
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )

    try:
        count = ask_count()
        accounts = create_many_mailboxes(count)
        output_path = Path(__file__).resolve().parent / "email.txt"
        save_accounts(accounts, str(output_path))
        logger.success(f"Done. Saved {len(accounts)} mailbox(es) to {output_path}")
    except requests.RequestException as e:
        logger.error(f"Network/API error: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")
