import json
import requests
from loguru import logger
from config.settings import ADSPOWER_API_URL


def start_browser(profile_number: str, headless: bool = False) -> str | None:
    launch_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-popup-blocking",
        "--disable-default-apps"
    ]

    params = {
        'serial_number': profile_number,
        'launch_args': json.dumps(launch_args),
        'open_tabs': 1
    }
    if headless:
        params['headless'] = 1

    try:
        response = requests.get(f'{ADSPOWER_API_URL}/api/v1/browser/start', params=params)
        logger.debug(f"[start_browser] Raw response: {response.text}")
        response.raise_for_status()
        data = response.json()

        if data.get("code") == 0:
            puppeteer_ws = data["data"]["ws"]["puppeteer"]
            logger.success(f"[start_browser] Browser started for profile {profile_number}")
            return puppeteer_ws
        else:
            logger.error(f"[start_browser] Failed to start browser for profile {profile_number}: {data.get('msg')}")
            return None

    except requests.exceptions.RequestException as e:
        logger.exception(f"[start_browser] Request error for profile {profile_number}: {e}")
        return None


def get_user_id_by_serial(serial_number: str) -> str | None:
    try:
        params = {"serial_number": serial_number, "page": 1, "page_size": 50}
        response = requests.get(f'{ADSPOWER_API_URL}/api/v1/user/list', params=params)
        logger.debug(f"[get_user_id_by_serial] Raw response: {response.text}")
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 0:
            logger.error(f"[get_user_id_by_serial] Failed for serial {serial_number}: {data.get('msg')}")
            return None

        items = None
        if isinstance(data.get("data"), dict):
            items = data["data"].get("list") or data["data"].get("data") or data["data"].get("items")
        elif isinstance(data.get("data"), list):
            items = data["data"]

        if not items:
            logger.warning(f"[get_user_id_by_serial] No users found for serial {serial_number}")
            return None

        for item in items:
            if str(item.get("serial_number")).strip() == str(serial_number).strip():
                return item.get("user_id") or item.get("id")

        return items[0].get("user_id") or items[0].get("id")
    except requests.exceptions.RequestException as e:
        logger.exception(f"[get_user_id_by_serial] Request error for serial {serial_number}: {e}")
        return None


def check_browser_status(profile_number: str) -> bool:
    try:
        response = requests.get(f'{ADSPOWER_API_URL}/api/v1/browser/active', params={'serial_number': profile_number})
        logger.debug(f"[check_browser_status] Raw response: {response.text}")
        response.raise_for_status()
        data = response.json()

        if data.get("code") == 0 and data["data"]["status"] == "Active":
            logger.info(f"[check_browser_status] Browser is active for profile {profile_number}")
            return True
        else:
            logger.warning(f"[check_browser_status] Browser is NOT active for profile {profile_number}")
            return False

    except requests.exceptions.RequestException as e:
        logger.exception(f"[check_browser_status] Request error for profile {profile_number}: {e}")
        return False


def close_browser(profile_number: str) -> bool:
    try:
        response = requests.get(f'{ADSPOWER_API_URL}/api/v1/browser/stop', params={'serial_number': profile_number})
        logger.debug(f"[close_browser] Raw response: {response.text}")
        response.raise_for_status()
        data = response.json()

        if data.get("code") == 0:
            logger.success(f"[close_browser] Browser closed for profile {profile_number}")
            return True
        msg = data.get("msg", "")
        if "not open" in msg.lower():
            logger.debug(f"[close_browser] Profile {profile_number} already closed: {msg}")
            return True
        if "User_id is not open" in msg or "user_id" in msg:
            user_id = get_user_id_by_serial(profile_number)
            if not user_id:
                logger.error(f"[close_browser] Failed to resolve user_id for serial {profile_number}")
                return False

            response = requests.get(f'{ADSPOWER_API_URL}/api/v1/browser/stop', params={'user_id': user_id})
            logger.debug(f"[close_browser] Retry by user_id response: {response.text}")
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0:
                logger.success(f"[close_browser] Browser closed for user_id {user_id} (serial {profile_number})")
                return True

        logger.error(f"[close_browser] Failed to close browser for profile {profile_number}: {data.get('msg')}")
        return False

    except requests.exceptions.RequestException as e:
        logger.exception(f"[close_browser] Request error for profile {profile_number}: {e}")
        return False


def clear_profile_data(profile_number: str, types: list[str] | None = None) -> bool:
    if types is None:
        types = ["cookie", "history", "image_file"]
    payload = {
        "profile_id": [profile_number],
        "type": types,
    }
    try:
        response = requests.post(f'{ADSPOWER_API_URL}/api/v2/browser-profile/delete-cache', json=payload)
        logger.debug(f"[clear_profile_data] Raw response: {response.text}")
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 0:
            logger.success(f"[clear_profile_data] Profile data cleared for {profile_number}")
            return True
        else:
            logger.error(f"[clear_profile_data] Failed to clear profile data for {profile_number}: {data.get('msg')}")
            return False
    except requests.exceptions.RequestException as e:
        logger.exception(f"[clear_profile_data] Request error for profile {profile_number}: {e}")
        return False
