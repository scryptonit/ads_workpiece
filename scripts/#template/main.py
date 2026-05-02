import math
import time
import random
import os
from loguru import logger
from patchright.sync_api import sync_playwright, expect
# from playwright.sync_api import sync_playwright
from utils.adspower_api_utils import start_browser, close_browser, clear_profile_data
from core.get_metamask_password import derive_password
from core.result_tracker import load_successful_profiles, save_success, save_success_wallets
from utils.mouse_random_click import human_like_mouse_click
from utils.human_type import human_like_type
from core.metamask_handler import auth_mm, auth_mm_disp, confirm_mm
from config.settings import DISPOSABLE_PROFILE_ID
from core.get_email_code import get_email_code, get_email_link
from core.get_imap_email_code import get_email_imap_code, get_email_imap_link
###########################################################################################
HEADLESS_NEW = False
DISPOSABLE = False  # on/off disposable Ads-profile
disp_N = 5  # number of disposable profiles
T = 15  # seconds delay
SHUFFLE_WALLETS = True  # randomize processing wallets/profiles


###########################################################################################

def load_profiles(file_name="profiles.txt"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_wallets_from_file(file_name="addresses.txt"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def load_email_accounts(file_name="email.txt"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)

    accounts = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if ":" not in line:
                logger.warning(f"Skip invalid account line: {line}")
                continue
            email, password = line.split(":", 1)
            accounts.append((email.strip(), password.strip()))
    return accounts
def close_other_pages(keep_page, context):
    time.sleep(2)
    for p in list(context.pages):
        if p is not keep_page and not p.is_closed():
            try:
                p.close()
            except Exception:
                pass


def activity(profile_number, wallet_addr, email=None, email_password=None):
    try:
        puppeteer_ws = None
        successful = load_successful_profiles()
        if DISPOSABLE:
            if wallet_addr in successful:
                logger.info(f"[SKIP] Кошелек {wallet_addr} уже обработан.")
                return
        else:
            if profile_number in successful:
                logger.info(f"[SKIP] Профиль {profile_number} уже обработан.")
                return

        if DISPOSABLE:
            close_browser(profile_number)
            time.sleep(1.1)
            clear_profile_data(profile_number)
            time.sleep(1.1)
        puppeteer_ws = start_browser(profile_number, headless=HEADLESS_NEW)
        if not puppeteer_ws:
            logger.error(f"Failed to launch browser for profile {profile_number}.")
            return

        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(puppeteer_ws)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
            close_other_pages(page, context)
            time.sleep(1.1)
            ###########################################################################################
            # auth_mm_disp(page, wallet_addr) if DISPOSABLE else auth_mm(page, profile_number)
            page.goto(
                "https://")
            page.wait_for_load_state("load")

            success_text = ""
            success_locator = page.get_by_text(success_text)
            success_locator.wait_for(state='visible', timeout=30000)
            if success_locator.count():
                if DISPOSABLE:
                    save_success_wallets(wallet_addr)
                    logger.success(f"Success for wallet {wallet_addr}")
                else:
                    save_success(profile_number)
                    logger.success(f"Success for profile {profile_number}")

            ###########################################################################################

            browser.close()
            time.sleep(random.uniform(T * 0.85, T * 1.15))

    except Exception as e:
        logger.error(f"Error for profile {profile_number}: {e}")


    finally:
        if puppeteer_ws:
            time.sleep(random.uniform(0.5, 1.5))
            close_browser(profile_number)


if __name__ == "__main__":
    wallets_to_process = load_wallets_from_file("addresses.txt")

    if DISPOSABLE:
        email_accounts = load_email_accounts("email.txt")

        if len(email_accounts) < len(wallets_to_process):
            logger.error(
                f"Not enough accounts in email.txt: {len(email_accounts)} < {len(wallets_to_process)}"
            )
            raise SystemExit(1)

        items = [
            (DISPOSABLE_PROFILE_ID, wallets_to_process[i], email_accounts[i][0], email_accounts[i][1])
            for i in range(len(wallets_to_process))
        ]

        if SHUFFLE_WALLETS:
            random.shuffle(items)

        for profile_id, wallet, email, email_password in items:
            activity(profile_id, wallet, email, email_password)

    else:
        profiles = load_profiles("profiles.txt")
        regular_accounts = load_email_accounts("accounts.txt")

        min_len = min(len(profiles), len(wallets_to_process), len(regular_accounts))
        if min_len == 0:
            logger.error("Empty input file(s)")
            raise SystemExit(1)

        if len(profiles) != len(wallets_to_process) or len(profiles) != len(regular_accounts):
            logger.warning(
                f"Length mismatch: profiles={len(profiles)}, wallets={len(wallets_to_process)}, accounts={len(regular_accounts)}. "
                f"Will process first {min_len} rows by index."
            )

        items = [
            (profiles[i], wallets_to_process[i], regular_accounts[i][0], regular_accounts[i][1])
            for i in range(min_len)
        ]

        if SHUFFLE_WALLETS:
            random.shuffle(items)

        for profile, wallet, email, email_password in items:
            activity(profile, wallet, email, email_password)
