import time
import base64
import requests
from loguru import logger
from config.settings import TWOCAPTCHA_API_KEY

IN_URL = "https://2captcha.com/in.php"
RES_URL = "https://2captcha.com/res.php"


def _to_base64(image: str | bytes) -> str:
    if isinstance(image, (bytes, bytearray)):
        return base64.b64encode(bytes(image)).decode()
    if image.startswith("data:"):
        return image.split(",", 1)[1]
    if image.startswith(("http://", "https://")):
        resp = requests.get(image, timeout=30)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode()
    with open(image, "rb") as f:
        return base64.b64encode(f.read()).decode()


def solve_image_captcha(
    image: str | bytes,
    length: int | None = None,
    numbers: bool = False,
    *,
    timeout: int = 120,
    poll: float = 5.0,
    api_key: str | None = None,
) -> str | None:
    key = api_key or TWOCAPTCHA_API_KEY
    if not key:
        raise RuntimeError("TWOCAPTCHA_API_KEY не задан в .env")

    data = {"key": key, "method": "base64", "body": _to_base64(image), "json": 1}
    if numbers:
        data["numeric"] = 1
    if length is not None:
        data["min_len"] = length
        data["max_len"] = length

    try:
        r = requests.post(IN_URL, data=data, timeout=30).json()
    except Exception as e:
        logger.error(f"2captcha in.php request failed: {e}")
        return None

    if r.get("status") != 1:
        logger.error(f"2captcha in.php error: {r.get('request')}")
        return None
    captcha_id = r["request"]

    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(poll)
        try:
            rr = requests.get(
                RES_URL,
                params={"key": key, "action": "get", "id": captcha_id, "json": 1},
                timeout=30,
            ).json()
        except Exception as e:
            logger.error(f"2captcha res.php request failed: {e}")
            return None

        if rr.get("status") == 1:
            answer = rr["request"].strip()
            logger.success(f"2captcha solved: {answer}")
            return answer
        if rr.get("request") != "CAPCHA_NOT_READY":
            logger.error(f"2captcha res.php error: {rr.get('request')}")
            return None

    logger.error("2captcha timeout")
    return None


if __name__ == "__main__":
    pass
    # code = solve_image_captcha(page.locator('a[href*="captcha"]').get_attribute("href"))            # цифры и буквы
    # code = solve_image_captcha(page.locator('a[href*="captcha"]').get_attribute("href"), 6, numbers=True)  # 6 цифр
    # code = solve_image_captcha(page.locator("img#captcha").screenshot(), numbers=True)
