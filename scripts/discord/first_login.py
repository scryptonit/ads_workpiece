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
SHUFFLE_WALLETS = False  # randomize processing wallets/profiles
DISCORD_LOGIN_BY_TOKEN = False
NEW_PASSWORD = ""


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


def save_step_success(profile_number, step_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "first_login_steps.txt")
    row = f"{profile_number}:{step_name}:1"

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            if row in {line.strip() for line in f if line.strip()}:
                logger.info(f"[STEP SKIP] {profile_number} {step_name}")
                return

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(row + "\n")
    logger.success(f"[STEP OK] {profile_number} {step_name}")


def is_step_success(profile_number, step_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "first_login_steps.txt")
    row = f"{profile_number}:{step_name}:1"

    if not os.path.exists(file_path):
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        return row in {line.strip() for line in f if line.strip()}


def skip_step_success(profile_number, step_name):
    if is_step_success(profile_number, step_name):
        logger.info(f"[STEP SKIP] {profile_number} {step_name}")
        return True
    return False


def save_discord_account(profile_number, discord_login, discord_password, discord_token=""):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "discord.txt")
    row = f"{profile_number}:{discord_login}:{discord_password}:{discord_token}"

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            existing = {line.strip() for line in f if line.strip()}
            prefix = f"{profile_number}:{discord_login}:{discord_password}:"
            if any(line.startswith(prefix) for line in existing):
                logger.info(f"[DISCORD SKIP] {profile_number} already saved")
                return

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(row + "\n")
    logger.success(f"[DISCORD SAVED] {profile_number} token={'***' if discord_token else 'empty'}")


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
            browser = playwright.chromium.connect_over_cdp(puppeteer_ws, slow_mo=10)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
            close_other_pages(page, context)
            time.sleep(1.1)

            def get_discord_credentials():
                with open(os.path.join('', "profiles.txt"), "r") as f:
                    prof_rows = [line.strip() for line in f if line.strip()]
                with open(os.path.join('', "credentials.txt"), "r") as f:
                    cred_rows = [line.strip() for line in f if line.strip()]

                prof_idx = prof_rows.index(str(profile_number))
                return cred_rows[prof_idx].split(":", 2)

            discord_login, discord_password, discord_token = get_discord_credentials()

            ###########################################################################################

            def cap_guru_ext():
                if is_step_success(profile_number, "chrome_extension"): return
                api_token = ''
                guru_page = context.new_page()
                guru_page.goto("chrome-extension://algafagdlkjomdlegpghjljfaflppanh/popup.html")
                guru_page.wait_for_load_state("load")
                time.sleep(5)
                if guru_page.get_by_role("button", name="Enable plugin").count():
                    human_like_mouse_click(guru_page.get_by_role("button", name="Enable plugin"))
                time.sleep(2)
                human_like_type(guru_page.get_by_placeholder("Enter your api key"), api_token)
                captchas = {
                    "hcaptcha": "fhcap",
                    "hcap auto": "fhcap_autoopen",
                    "fancaptcha": "ffuncap",
                }
                for captcha_name, checkbox_id in captchas.items():
                    checkbox = guru_page.locator(f'#{checkbox_id}')
                    if not checkbox.is_checked():
                        human_like_mouse_click(guru_page.locator(f'label.switchBtn[for="{checkbox_id}"]'))
                for captcha_name, checkbox_id in captchas.items():
                    checkbox = guru_page.locator(f'#{checkbox_id}')
                    if not checkbox.is_checked():
                        human_like_mouse_click(guru_page.locator(f'label.switchBtn[for="{checkbox_id}"]'))
                save_step_success(profile_number, "chrome_extension")
                time.sleep(3)
                guru_page.close()

            cap_guru_ext()

            ###########################################################################################

            def discord_token_enter():
                if is_step_success(profile_number, "discord_login"): return
                page = context.new_page()
                page.goto("https://discord.com/login")
                page.wait_for_load_state("load")
                time.sleep(3)
                if "login" in page.url:
                    page.evaluate("""token => { localStorage.setItem('token', JSON.stringify(token)); }""", discord_token)
                                    
                    page.reload()
                    page.wait_for_load_state("load")
                    time.sleep(3)
                    if "login" not in page.url:
                        save_step_success(profile_number, "discord_login")
                        logger.success(f"Discord Login for profile {profile_number}")
                return page

            ###########################################################################################

            def discord_login_enter():
                if is_step_success(profile_number, "discord_login"): return
                page = context.new_page()
                page.goto("https://discord.com/login")
                page.wait_for_load_state("load")
                time.sleep(3)
                try:
                    page.get_by_role("textbox", name="Email or Phone Number").wait_for(state='visible')
                    human_like_type(page.get_by_role("textbox", name="Email or Phone Number"), discord_login)
                    human_like_type(page.get_by_role("textbox", name="Password"), discord_password)
                    human_like_mouse_click(page.get_by_role("button", name="Log In"))
                    try:
                        page.get_by_text("location detected").wait_for(state='visible')
                        time.sleep(15)
                        link = get_email_imap_link(discord_login, discord_password, "https://click.discord.com")
                        link_page = context.new_page()
                        link_page.goto(link)
                        link_page.wait_for_load_state("load")
                        time.sleep(3)
                        link_page.close()
                        human_like_mouse_click(page.get_by_role("button", name="Log In"))
                    except:
                        pass

                except:
                    pass
                time.sleep(7)
                if "channels" in page.url:
                    save_step_success(profile_number, "discord_login")
                    logger.success(f"Discord Login for profile {profile_number}")
                return page



            ###########################################################################################

            def discord_change_password(page):
                if is_step_success(profile_number, "discord_changed_password"): return
                if page is None or page.is_closed():
                    page = context.new_page()
                if page.url == "about:blank":
                    page.goto("https://discord.com/login")
                    page.wait_for_load_state("load")
                    time.sleep(3)

                human_like_mouse_click(page.get_by_role("button", name="User Settings"))
                human_like_mouse_click(page.get_by_role("button", name="Change Password"))
                human_like_type(page.get_by_role("textbox", name="Current Password"), discord_password)
                human_like_type(page.get_by_role("textbox", name="New Password", exact=True), NEW_PASSWORD)
                human_like_type(page.get_by_role("textbox", name="Confirm New Password", exact=True), NEW_PASSWORD)
                human_like_mouse_click(page.get_by_role("button", name="Done"))
                time.sleep(3)
                if page.get_by_text("Update your password").count():
                    page.get_by_text("Update your password").wait_for(state='detached', timeout=90000)

                save_step_success(profile_number, "discord_changed_password")

                new_token = page.evaluate("() => JSON.parse(localStorage.getItem('token') || 'null')")
                save_discord_account(profile_number, discord_login, NEW_PASSWORD, new_token)
                return page

            if DISCORD_LOGIN_BY_TOKEN:
                page = discord_token_enter()
            else:
                page = discord_login_enter()
            page = discord_change_password(page)

            ###########################################################################################

            def rambler_change_password():
                if is_step_success(profile_number, "rambler_changed_password"): return
                rambler_page = context.new_page()
                rambler_page.goto("https://id.rambler.ru/login-20/login")
                rambler_page.wait_for_load_state("load")
                time.sleep(5)
                try:
                    rambler_page.get_by_role("textbox", name="Почта").wait_for(state='visible', timeout=10000)
                    human_like_type(rambler_page.get_by_role("textbox", name="Почта"), discord_login)
                    human_like_type(rambler_page.get_by_role("textbox", name="Пароль"), discord_password)
                    time.sleep(1)
                    human_like_mouse_click(rambler_page.get_by_role("button", name="Войти"))
                    if rambler_page.get_by_text("проверку на робота").count():
                        rambler_page.get_by_text("проверку на робота").wait_for(state='detached', timeout=90000)
                        human_like_mouse_click(rambler_page.get_by_role("button", name="Войти"))
                except:
                    pass
                time.sleep(5)
                if rambler_page.get_by_text("подтвердить позже").count():
                    human_like_mouse_click(rambler_page.get_by_text("подтвердить позже"))
                rambler_page.goto("https://id.rambler.ru/account/change-password")
                time.sleep(3)
                if rambler_page.get_by_text("пожалуйста").count():
                    rambler_page.get_by_text("пожалуйста").wait_for(state='detached', timeout=90000)
                human_like_type(rambler_page.get_by_role("textbox", name="Текущий пароль"), discord_password)
                human_like_type(rambler_page.get_by_role("textbox", name="Новый пароль"), NEW_PASSWORD)
                human_like_mouse_click(rambler_page.get_by_role("button", name="Сохранить"))
                time.sleep(3)
                rambler_page.reload()
                if "profile" in rambler_page.url:
                    save_step_success(profile_number, "rambler_changed_password")
                    save_success(profile_number)

            rambler_change_password()
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

        if not wallets_to_process:
            logger.info("addresses.txt is empty, nothing to process.")
            raise SystemExit(0)
        if not email_accounts:
            logger.info("email.txt is empty, email data will not be used.")

        items = [
            (
                DISPOSABLE_PROFILE_ID,
                wallets_to_process[i],
                email_accounts[i][0] if i < len(email_accounts) else None,
                email_accounts[i][1] if i < len(email_accounts) else None,
            )
            for i in range(len(wallets_to_process))
        ]

        if SHUFFLE_WALLETS:
            random.shuffle(items)

        for profile_id, wallet, email, email_password in items:
            activity(profile_id, wallet, email, email_password)

    else:
        profiles = load_profiles("profiles.txt")
        regular_accounts = load_email_accounts("email.txt")

        if not profiles:
            logger.info("profiles.txt is empty, nothing to process.")
            raise SystemExit(0)
        if not wallets_to_process:
            logger.info("addresses.txt is empty, wallet data will not be used.")
        if not regular_accounts:
            logger.info("email.txt is empty, email data will not be used.")

        if wallets_to_process and len(profiles) != len(wallets_to_process):
            logger.warning(
                f"Length mismatch: profiles={len(profiles)}, wallets={len(wallets_to_process)}. "
                "Missing wallet rows will be ignored."
            )
        if regular_accounts and len(profiles) != len(regular_accounts):
            logger.warning(
                f"Length mismatch: profiles={len(profiles)}, accounts={len(regular_accounts)}. "
                "Missing email rows will be ignored."
            )

        items = [
            (
                profiles[i],
                wallets_to_process[i] if i < len(wallets_to_process) else None,
                regular_accounts[i][0] if i < len(regular_accounts) else None,
                regular_accounts[i][1] if i < len(regular_accounts) else None,
            )
            for i in range(len(profiles))
        ]

        if SHUFFLE_WALLETS:
            random.shuffle(items)

        for profile, wallet, email, email_password in items:
            activity(profile, wallet, email, email_password)
