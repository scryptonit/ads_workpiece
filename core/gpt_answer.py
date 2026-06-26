import base64
import mimetypes
from loguru import logger
from openai import OpenAI
from config.settings import OPENAI_API_KEY, OPENAI_MODEL

_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def _get_client() -> OpenAI:
    if _client is None:
        raise RuntimeError("OPENAI_API_KEY не задан в .env")
    return _client


def ask(prompt: str, *, model: str | None = None, max_tokens: int = 100) -> str | None:
    try:
        r = _get_client().chat.completions.create(
            model=model or OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.0,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"GPT error: {e}")
        return None


def ask_image(
    prompt: str,
    image: str | bytes,
    *,
    detail: str = "high",
    model: str | None = None,
    max_tokens: int = 100,
) -> str | None:
    try:
        if isinstance(image, (bytes, bytearray)):
            data_url = f"data:image/png;base64,{base64.b64encode(bytes(image)).decode()}"
        elif image.startswith(("http://", "https://", "data:")):
            data_url = image
        else:
            with open(image, "rb") as f:
                img_bytes = f.read()
            mime = mimetypes.guess_type(image)[0] or "image/png"
            data_url = f"data:{mime};base64,{base64.b64encode(img_bytes).decode()}"

        r = _get_client().chat.completions.create(
            model=model or OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url, "detail": detail}},
                    ],
                }
            ],
            max_tokens=max_tokens,
            temperature=0.0,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"GPT vision error: {e}")
        return None


if __name__ == "__main__":
    pass
    # ask("Answer with a single word: capital of France?")
    # ask("Reply only YES or NO: is 7 a prime number?", max_tokens=5)

    # ask_image("Return only the digits on the image.", "https://site.com/captcha.png")
    # ask_image("Return only the digits on the image.", page.locator("img#captcha").get_attribute("src"))
    # ask_image("Read the text on this screenshot.", page.locator("img#captcha").screenshot())
    # ask_image("What number is shown? Digits only.", "captcha.png", detail="low")
