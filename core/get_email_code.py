import time
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Pattern

import requests
from loguru import logger

MAILTM = "https://api.mail.tm"
DIGITS = "digits"
ALNUM = "alnum"
digits = DIGITS
alnum = ALNUM


def _build_code_re(code_len: int = 6, code_charset: str = ALNUM) -> Pattern[str]:
    if not isinstance(code_len, int) or code_len <= 0:
        raise ValueError("code_len must be a positive integer")

    charset = (code_charset or ALNUM).lower()
    if charset == DIGITS:
        return re.compile(rf"\b\d{{{code_len}}}\b")
    if charset == ALNUM:
        return re.compile(rf"\b[A-Za-z0-9]{{{code_len}}}\b")
    raise ValueError(f"Unsupported code_charset: {code_charset!r}. Use '{DIGITS}' or '{ALNUM}'")


def _parse_mailtm_dt(value: object) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _message_dt(message: dict) -> Optional[datetime]:
    return _parse_mailtm_dt(message.get("createdAt")) or _parse_mailtm_dt(message.get("updatedAt"))


def get_mailtm_token(email: str, password: str) -> str:
    s = requests.Session()
    s.headers.update({"User-Agent": "temp-mailtm/1.0"})

    r = s.post(
        f"{MAILTM}/token",
        json={"address": email, "password": password},
        timeout=20,
    )
    r.raise_for_status()

    token = r.json().get("token")
    if not token:
        raise RuntimeError("mail.tm token missing")

    return token


def wait_email_code_by_token(
    token: str,
    timeout_s: int = 180,
    poll_s: float = 3.0,
    code_re: Optional[Pattern[str]] = None,
    max_message_age_min: Optional[int] = 15,
) -> Optional[str]:
    s = requests.Session()
    s.headers.update({"User-Agent": "temp-mailtm/1.0"})
    headers = {"Authorization": f"Bearer {token}"}
    code_re = code_re or _build_code_re()

    seen = set()
    t0 = time.time()

    while time.time() - t0 < timeout_s:
        r = s.get(f"{MAILTM}/messages", headers=headers, timeout=20)
        r.raise_for_status()
        msgs = r.json().get("hydra:member") or []

        if max_message_age_min is not None:
            now_utc = datetime.now(timezone.utc)
            max_age = timedelta(minutes=max_message_age_min)
            filtered_msgs = []
            for m in msgs:
                msg_dt = _message_dt(m)
                if msg_dt is None:
                    continue
                if now_utc - msg_dt <= max_age:
                    filtered_msgs.append(m)
            msgs = filtered_msgs

        msgs = sorted(
            msgs,
            key=lambda m: _message_dt(m) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        for m in msgs:
            mid = m.get("id")
            if not mid or mid in seen:
                continue
            seen.add(mid)

            r = s.get(f"{MAILTM}/messages/{mid}", headers=headers, timeout=20)
            r.raise_for_status()
            msg = r.json()

            parts = []

            intro = msg.get("intro")
            if isinstance(intro, str) and intro.strip():
                parts.append(intro)

            subject = msg.get("subject")
            if isinstance(subject, str) and subject.strip():
                parts.append(subject)

            for k in ("text", "html"):
                v = msg.get(k)
                if isinstance(v, list):
                    parts.extend([x for x in v if isinstance(x, str) and x.strip()])
                elif isinstance(v, str) and v.strip():
                    parts.append(v)

            text = "\n\n".join(parts)
            mcode = code_re.search(text)
            if mcode:
                return mcode.group(0)

        time.sleep(poll_s)

    return None


def get_email_code(
    email: str,
    password: str,
    code_len: int = 6,
    code_charset: str = ALNUM, #"digits" if only digits
    *,
    timeout_s: int = 180,
    poll_s: float = 3.0,
    max_message_age_min: Optional[int] = 15,
) -> Optional[str]:
    token = get_mailtm_token(email, password)
    code_re = _build_code_re(code_len=code_len, code_charset=code_charset)
    return wait_email_code_by_token(
        token,
        timeout_s=timeout_s,
        poll_s=poll_s,
        code_re=code_re,
        max_message_age_min=max_message_age_min,
    )


if __name__ == "__main__":
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    email = input("Email: ").strip()
    password = input("Password: ").strip()

    try:
        code = get_email_code(email, password, 6, DIGITS, timeout_s=180, poll_s=3.0)
        if code:
            logger.success(f"Code: {code}")
        else:
            logger.warning("Code not found (timeout)")
    except requests.RequestException as e:
        logger.error(f"Network/API error: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")
