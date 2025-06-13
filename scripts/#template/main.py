import math
import time
import random
import os
from loguru import logger
from patchright.sync_api import sync_playwright
from utils.adspower_api_utils import start_browser, close_browser
from core.get_metamask_password import derive_password
from core.result_tracker import load_successful_profiles, save_success


###########################################################################################
DISPOSABLE = True
disp_N = 10  # number of disposable profiles
T = 15  # seconds delay
###########################################################################################

def load_profiles(file_name="profiles.txt"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def click_random(locator, manual_radius: float = None):
    time.sleep(random.uniform(1, 2))
    locator.wait_for(state='visible', timeout=50000)
    box = locator.bounding_box()
    if box is None:
        raise Exception("Bounding box not found")
    width, height = box["width"], box["height"]
    cx, cy = width / 2, height / 2
    radius = manual_radius if manual_radius is not None else min(width, height) / 2
    angle = random.uniform(0, 2 * math.pi)
    r = radius * math.sqrt(random.uniform(0, 1))
    rand_x = cx + r * math.cos(angle)
    rand_y = cy + r * math.sin(angle)

    locator.click(position={"x": rand_x, "y": rand_y})

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
            browser = playwright.chromium.connect_over_cdp(puppeteer_ws, slow_mo=random.randint(2000, 3000))
            context = browser.contexts[0] if browser.contexts else browser.new_context()

            context.add_init_script("""
                Object.defineProperty(window, 'navigator', {
                    value: new Proxy(navigator, {
                        has: (target, key) => key === 'webdriver' ? false : key in target,
                        get: (target, key) =>
                            key === 'webdriver' ? undefined : typeof target[key] === 'function' ? target[key].bind(target) : target[key]
                    })
                });
            """)

            page = context.new_page()
            ###########################################################################################
            page.goto("https://bot.sannysoft.com/")
            page.wait_for_load_state("load")
            # save_success(profile_number)
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
    if DISPOSABLE:
        profiles = ['5'] * disp_N
    else:
        profiles = load_profiles("profiles.txt")
    for profile in profiles:
        activity(profile)
