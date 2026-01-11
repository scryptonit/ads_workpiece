# WORKS WITH METAMASK v13.13
import time
import random
import os
from loguru import logger
from patchright.sync_api import sync_playwright
from utils.adspower_api_utils import start_browser, close_browser
from core.get_metamask_password import derive_password
from core.result_tracker import load_successful_profiles, save_success
from get_seed import get_address_and_seed_for_profile


def load_profiles(file_name="profiles.txt"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def close_other_pages(keep_page, context):
    time.sleep(2)
    for p in list(context.pages):
        if p is not keep_page and not p.is_closed():
            try:
                p.close()
            except Exception:
                pass

def activity(profile_number):
    try:
        puppeteer_ws = None
        successful = load_successful_profiles()
        if profile_number in successful:
            logger.info(f"[SKIP] Profile {profile_number} already processed.")
            return

        puppeteer_ws = start_browser(profile_number)
        if not puppeteer_ws:
            logger.error(f"Failed to launch browser for profile {profile_number}.")
            return

        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(puppeteer_ws, slow_mo=random.randint(1000, 1500))
            context = browser.contexts[0] if browser.contexts else browser.new_context()


            page = context.new_page()
            close_other_pages(page, context)

            page.goto("chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html")
            page.wait_for_load_state("load")
            page.get_by_test_id('onboarding-import-wallet').click()
            page.get_by_test_id('onboarding-import-with-srp-button').click()

            addr, seed = get_address_and_seed_for_profile(profile_number)
            seed_textbox = page.get_by_test_id("srp-input-import__srp-note")
            seed_textbox.click()
            page.keyboard.type(seed, delay=40)

            page.get_by_test_id('import-srp-confirm').click()

            password = derive_password(profile_number)
            page.get_by_test_id('create-password-new-input').fill(password)
            page.get_by_test_id('create-password-confirm-input').fill(password)
            page.get_by_role('checkbox').click()
            page.get_by_test_id('create-password-submit').click()
            page.get_by_role('checkbox').first.click()

            page.get_by_test_id('metametrics-i-agree').click()
            page.get_by_test_id('onboarding-complete-done').click()

            page.goto("chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html")
            page.get_by_test_id('eth-overview-receive').click()

            if addr[:7] == page.get_by_test_id('multichain-address-row-address').first.inner_text()[:7]:
                save_success(profile_number)
                logger.success(f"[OK] Profile {profile_number} successfully imported to MetaMask.")
            else:
                logger.warning(f"[CHECK] Address verification failed for profile {profile_number}.")

            browser.close()

    except Exception as e:
        logger.error(f"Error for profile {profile_number}: {e}")


    finally:
        if puppeteer_ws:
            time.sleep(random.uniform(0.5, 1.5))
            close_browser(profile_number)


if __name__ == "__main__":
    profiles = load_profiles("profiles.txt")
    for profile in profiles:
        activity(profile)
