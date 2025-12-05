import math
import time
import random
import os
from loguru import logger
from patchright.sync_api import sync_playwright,expect
# from playwright.sync_api import sync_playwright
from utils.adspower_api_utils import start_browser, close_browser
from core.get_metamask_password import derive_password
from core.result_tracker import load_successful_profiles, save_success, save_success_wallets
from utils.mouse_random_click import human_like_mouse_click
from utils.human_type import human_like_type
from core.metamask_handler import auth_mm, confirm_mm


###########################################################################################
HEADLESS_NEW = False
DISPOSABLE = True # on/off disposable Ads-profile
DISPOSABLE_PROFILE_ID = '5'
disp_N = 10  # number of disposable profiles
T = 15  # seconds delay
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
def close_other_pages(page, context):
    time.sleep(2)
    for pages in context.pages:
        if pages.url != page.url:
            pages.close()

def activity(profile_number, wallet_addr):
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

        puppeteer_ws = start_browser(profile_number, headless = HEADLESS_NEW)
        if not puppeteer_ws:
            logger.error(f"Failed to launch browser for profile {profile_number}.")
            return

        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(puppeteer_ws)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
            close_other_pages(page, context)
            ###########################################################################################
            # auth_mm(page, profile_number)
            page.goto("https://...")
            page.wait_for_load_state("load")
            time.sleep(random.uniform(5, 10))


            
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
        for wallet in wallets_to_process:
            activity(DISPOSABLE_PROFILE_ID, wallet)
    else:
        profiles = load_profiles("profiles.txt")
        for i, profile in enumerate(profiles):
            if i < len(wallets_to_process):
                activity(profile, wallets_to_process[i])
