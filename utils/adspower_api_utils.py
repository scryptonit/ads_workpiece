import json
import requests
from loguru import logger
from config.settings import ADSPOWER_API_URL


def start_browser(profile_number: str) -> str | None:
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
        else:
            logger.error(f"[close_browser] Failed to close browser for profile {profile_number}: {data.get('msg')}")
            return False

    except requests.exceptions.RequestException as e:
        logger.exception(f"[close_browser] Request error for profile {profile_number}: {e}")
        return False
