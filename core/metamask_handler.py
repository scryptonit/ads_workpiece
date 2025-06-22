import time
from loguru import logger
from core.get_metamask_password import derive_password

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


def confirm_mm(context):
    try:
        metamask_page = context.new_page()
        metamask_page.goto("chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html")
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
