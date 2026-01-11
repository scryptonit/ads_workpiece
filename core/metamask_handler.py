import time
from loguru import logger
from core.get_metamask_password import derive_password
from core.get_seed import get_seed_for_address
from config.settings import DISPOSABLE_PROFILE_ID

def auth_mm(page, profile: str):
    password = derive_password(profile)

    try:
        page.goto("chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html")
        page.wait_for_load_state("load")

        try:
            unlock_input = page.get_by_test_id("unlock-password")
            unlock_input.wait_for(timeout=5000)
            unlock_input.fill(password)
            page.get_by_test_id("unlock-submit").click()

            page.get_by_test_id("eth-overview-buy").wait_for(timeout=5000)
            logger.success(f"MetaMask unlocked successfully for profile: {profile}")

        except:
            if page.query_selector('[data-testid="eth-overview-buy"]'):
                logger.success(f"MetaMask already unlocked for profile: {profile}")
            else:
                logger.error(f"MetaMask unlock failed for profile: {profile}")
    except Exception as e:
        logger.error(f"MetaMask unlock exception for profile {profile}: {e}")

def auth_mm_disp(page, wallet_address: str, profile_id: str | None = None):
    page.goto("chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#restore-vault")
    page.wait_for_load_state("load")
    seed = get_seed_for_address(wallet_address)
    seed_words = seed.split()
    for i, word in enumerate(seed_words):
        page.get_by_test_id(f'import-srp__srp-word-{i}').fill(word)
    effective_profile_id = profile_id or DISPOSABLE_PROFILE_ID
    password = derive_password(effective_profile_id)

    page.get_by_test_id('create-vault-password').fill(password)
    page.get_by_test_id('create-vault-confirm-password').fill(password)
    page.get_by_test_id('create-new-vault-submit-button').click()
    time.sleep(1)
    page.get_by_test_id('eth-overview-receive').click()


    if wallet_address[:7].lower() == page.get_by_test_id('multichain-address-row-address').first.inner_text()[:7].lower():
        logger.success(f"[OK] Profile {wallet_address} successfully imported to MetaMask.")
        return True

    raise RuntimeError(f"MetaMask address mismatch for wallet {wallet_address}")

def confirm_mm(context):
    try:
        metamask_page = context.new_page()
        metamask_page.goto("chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/sidepanel.html")
        metamask_page.wait_for_load_state("load")
        time.sleep(3)
        button_ids = ["confirm-btn", "page-container-footer-next", "confirm-footer-button"]
        for test_id in button_ids:
            try:
                button = metamask_page.get_by_test_id(test_id)
                if button.count():
                    button.click()
                    logger.success(f"MetaMask confirmed with button: {test_id}")
                    break
            except:
                continue
        else:
            logger.warning("MetaMask confirmation buttons not found.")
    except Exception as e:
        logger.error(f"MetaMask confirmation failed: {e}")
    finally:
        try:
            metamask_page.close()
        except Exception:
            pass
