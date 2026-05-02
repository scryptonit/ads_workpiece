import time
import re
import imaplib
from datetime import datetime, timedelta, timezone
from email import message_from_bytes
from email.header import decode_header
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Optional, Pattern

from loguru import logger

DIGITS = "digits"
ALNUM = "alnum"
digits = DIGITS
alnum = ALNUM

IMAP_HOSTS = {
    "gmail.com": "imap.gmail.com",
    "googlemail.com": "imap.gmail.com",
    "yandex.ru": "imap.yandex.com",
    "yandex.com": "imap.yandex.com",
    "ya.ru": "imap.yandex.com",
    "mail.ru": "imap.mail.ru",
    "internet.ru": "imap.mail.ru",
    "bk.ru": "imap.mail.ru",
    "inbox.ru": "imap.mail.ru",
    "list.ru": "imap.mail.ru",
    "outlook.com": "outlook.office365.com",
    "hotmail.com": "outlook.office365.com",
    "live.com": "outlook.office365.com",
    "msn.com": "outlook.office365.com",
    "yahoo.com": "imap.mail.yahoo.com",
    "icloud.com": "imap.mail.me.com",
    "me.com": "imap.mail.me.com",
    "rambler.ru": "imap.rambler.ru",
    "lenta.ru": "imap.rambler.ru",
    "ro.ru": "imap.rambler.ru",
    "myrambler.ru": "imap.rambler.ru",
}


def _build_code_re(code_len: int = 6, code_charset: str = ALNUM) -> Pattern[str]:
    if not isinstance(code_len, int) or code_len <= 0:
        raise ValueError("code_len must be a positive integer")

    charset = (code_charset or ALNUM).lower()
    if charset == DIGITS:
        return re.compile(rf"\b\d{{{code_len}}}\b")
    if charset == ALNUM:
        return re.compile(rf"\b[A-Za-z0-9]{{{code_len}}}\b")
    raise ValueError(f"Unsupported code_charset: {code_charset!r}. Use '{DIGITS}' or '{ALNUM}'")


def _build_link_re(link_mask: str | Pattern[str]) -> Pattern[str]:
    if hasattr(link_mask, "search"):
        return link_mask
    escaped = re.escape(link_mask)
    return re.compile(rf"({escaped}[^\s\"'<>]*)")


def _match_text(match) -> str:
    value = match.group(1) if match.lastindex else match.group(0)
    return unescape(value).strip().strip("\"'<>")


def _imap_host_for_email(email: str) -> str:
    domain = email.rsplit("@", 1)[-1].strip().lower()
    host = IMAP_HOSTS.get(domain)
    if not host:
        raise ValueError(f"Unknown IMAP host for domain: {domain}")
    return host


def _decode_value(value: object) -> str:
    if not value:
        return ""

    parts = []
    for raw, enc in decode_header(str(value)):
        if isinstance(raw, bytes):
            parts.append(raw.decode(enc or "utf-8", errors="ignore"))
        else:
            parts.append(raw)
    return "".join(parts)


def _message_dt(msg) -> Optional[datetime]:
    raw = msg.get("Date")
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _message_text(msg) -> str:
    parts = []

    subject = _decode_value(msg.get("Subject"))
    if subject.strip():
        parts.append(subject)

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type not in ("text/plain", "text/html"):
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            parts.append(payload.decode(charset, errors="ignore"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            parts.append(payload.decode(charset, errors="ignore"))

    return "\n\n".join(parts)


def wait_email_code_by_imap(
    email: str,
    password: str,
    timeout_s: int = 180,
    poll_s: float = 3.0,
    code_re: Optional[Pattern[str]] = None,
    max_message_age_min: Optional[int] = 15,
    imap_host: Optional[str] = None,
    mailbox: str = "INBOX",
) -> Optional[str]:
    code_re = code_re or _build_code_re()
    host = imap_host or _imap_host_for_email(email)
    seen = set()
    t0 = time.time()

    while time.time() - t0 < timeout_s:
        with imaplib.IMAP4_SSL(host, 993) as client:
            client.login(email, password)
            client.select(mailbox)

            if max_message_age_min is not None:
                since_dt = datetime.now(timezone.utc) - timedelta(minutes=max_message_age_min)
                query = f'(SINCE "{since_dt.strftime("%d-%b-%Y")}")'
            else:
                query = "ALL"

            status, data = client.search(None, query)
            if status != "OK":
                raise RuntimeError("IMAP search failed")

            ids = (data[0] or b"").split()
            for mid in reversed(ids[-50:]):
                if mid in seen:
                    continue
                seen.add(mid)

                status, msg_data = client.fetch(mid, "(RFC822)")
                if status != "OK" or not msg_data or not isinstance(msg_data[0], tuple):
                    continue

                msg = message_from_bytes(msg_data[0][1])
                if max_message_age_min is not None:
                    msg_dt = _message_dt(msg)
                    if msg_dt is None:
                        continue
                    if datetime.now(timezone.utc) - msg_dt > timedelta(minutes=max_message_age_min):
                        continue

                mcode = code_re.search(_message_text(msg))
                if mcode:
                    return mcode.group(0)

        time.sleep(poll_s)

    return None


def wait_email_link_by_imap(
    email: str,
    password: str,
    link_mask: str | Pattern[str],
    timeout_s: int = 180,
    poll_s: float = 3.0,
    max_message_age_min: Optional[int] = 15,
    imap_host: Optional[str] = None,
    mailbox: str = "INBOX",
) -> Optional[str]:
    link_re = _build_link_re(link_mask)
    host = imap_host or _imap_host_for_email(email)
    seen = set()
    t0 = time.time()

    while time.time() - t0 < timeout_s:
        with imaplib.IMAP4_SSL(host, 993) as client:
            client.login(email, password)
            client.select(mailbox)

            if max_message_age_min is not None:
                since_dt = datetime.now(timezone.utc) - timedelta(minutes=max_message_age_min)
                query = f'(SINCE "{since_dt.strftime("%d-%b-%Y")}")'
            else:
                query = "ALL"

            status, data = client.search(None, query)
            if status != "OK":
                raise RuntimeError("IMAP search failed")

            ids = (data[0] or b"").split()
            for mid in reversed(ids[-50:]):
                if mid in seen:
                    continue
                seen.add(mid)

                status, msg_data = client.fetch(mid, "(RFC822)")
                if status != "OK" or not msg_data or not isinstance(msg_data[0], tuple):
                    continue

                msg = message_from_bytes(msg_data[0][1])
                if max_message_age_min is not None:
                    msg_dt = _message_dt(msg)
                    if msg_dt is None:
                        continue
                    if datetime.now(timezone.utc) - msg_dt > timedelta(minutes=max_message_age_min):
                        continue

                mlink = link_re.search(_message_text(msg))
                if mlink:
                    return _match_text(mlink)

        time.sleep(poll_s)

    return None


def get_email_imap_code(
    email: str,
    password: str,
    code_len: int = 6,
    code_charset: str = ALNUM,
    *,
    timeout_s: int = 180,
    poll_s: float = 3.0,
    max_message_age_min: Optional[int] = 15,
    imap_host: Optional[str] = None,
    mailbox: str = "INBOX",
) -> Optional[str]:
    code_re = _build_code_re(code_len=code_len, code_charset=code_charset)
    return wait_email_code_by_imap(
        email,
        password,
        timeout_s=timeout_s,
        poll_s=poll_s,
        code_re=code_re,
        max_message_age_min=max_message_age_min,
        imap_host=imap_host,
        mailbox=mailbox,
    )


def get_email_imap_link(
    email: str,
    password: str,
    link_mask: str | Pattern[str],
    *,
    timeout_s: int = 180,
    poll_s: float = 3.0,
    max_message_age_min: Optional[int] = 15,
    imap_host: Optional[str] = None,
    mailbox: str = "INBOX",
) -> Optional[str]:
    return wait_email_link_by_imap(
        email,
        password,
        link_mask,
        timeout_s=timeout_s,
        poll_s=poll_s,
        max_message_age_min=max_message_age_min,
        imap_host=imap_host,
        mailbox=mailbox,
    )


if __name__ == "__main__":
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    email = input("Email: ").strip()
    password = input("Password: ").strip()

    try:
        code = get_email_imap_code(email, password, 6, DIGITS, timeout_s=180, poll_s=3.0)
        if code:
            logger.success(f"Code: {code}")
        else:
            logger.warning("Code not found (timeout)")
    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP error: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")
