import math
import time
import random
import os
import sys
import re
import json
import pyotp
from loguru import logger
from patchright.sync_api import sync_playwright, expect
# from playwright.sync_api import sync_playwright
from utils.adspower_api_utils import start_browser, close_browser
from core.get_metamask_password import derive_password
from core.result_tracker import load_successful_profiles, save_success
from utils.mouse_random_click import human_like_mouse_click
from utils.human_type import human_like_type
from core.metamask_handler import auth_mm, confirm_mm
from core.get_email_code import get_email_code, get_email_link
from core.get_imap_email_code import get_email_imap_code, get_email_imap_link
from core.gpt_answer import ask
###########################################################################################
HEADLESS_NEW = False
T = 15  # seconds delay
SHUFFLE_WALLETS = True  # randomize processing profiles
USE_AI_COMMENTS = True  # True = AI api writes reply/quote, False = read from reply.txt/quote.txt
EXPECTED_ACTIONS = 6  # how many successful actions in x_results.json = profile fully done

script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
x_results_filename = f"{script_name}_results.json"


###########################################################################################

def load_profiles(file_name="profiles.txt"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_email_accounts(file_name="email.txt"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)

    accounts = []
    if not os.path.exists(file_path):
        return accounts
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
###############################__X__#####################################
def x_load_credentials(file_name="credentials.txt"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)

    accounts = []
    if not os.path.exists(file_path):
        return accounts
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            accounts.append(line.split("|"))
    return accounts


def x_load_lines(file_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def x_load_friends(file_name="friends.txt"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [[u.strip().lstrip("@") for u in line.split(",") if u.strip()] for line in f if line.strip()]


def x_login_with_cookies(context, page, auth_token, ct0):
    context.add_cookies([
        {"name": "auth_token", "value": auth_token, "domain": ".x.com", "path": "/"},
        {"name": "ct0", "value": ct0, "domain": ".x.com", "path": "/"},
    ])
    page.goto("https://x.com/home")
    page.wait_for_load_state("load")


def x_login_scope(page):
    layers = page.locator("#layers")
    return layers if layers.count() > 0 else page


def x_login_with_form(page, username, password, twofa_secret=None):
    human_like_type(page.get_by_role("textbox", name="Email or username"), username)
    time.sleep(random.uniform(2, 3))
    human_like_mouse_click(page.get_by_role("button", name="Continue", exact="True"))
    time.sleep(random.uniform(2, 3))
    human_like_type(x_login_scope(page).get_by_role("textbox", name="Password"), password)
    time.sleep(random.uniform(2, 3))
    human_like_mouse_click(x_login_scope(page).get_by_role("button", name="Continue", exact="True"))
    if twofa_secret:
        time.sleep(random.uniform(2, 3))
        code = pyotp.TOTP(twofa_secret).now()
        human_like_type(x_login_scope(page).get_by_role("textbox"), code)


def x_dismiss_popup(page):
    try:
        page.get_by_role("button", name="Accept all cookies").click(timeout=3000)
    except Exception:
        pass
    try:
        page.get_by_role("button", name="Got it").click(timeout=5000)
    except Exception:
        pass


_x_context = {"profile_number": None, "project": None}


def x_set_context(profile_number, project):
    _x_context["profile_number"] = profile_number
    _x_context["project"] = project


def x_is_done(action, target):
    data = x_load_results()
    profile_data = data.get(str(_x_context["profile_number"]), {})
    project_data = profile_data.get(_x_context["project"], {})
    return project_data.get(action, {}).get(str(target))


def x_follow(page, username):
    done = x_is_done("follow", username)
    if done:
        logger.info(f"[SKIP] follow already done: {done}")
        return done
    page.goto(f"https://x.com/intent/follow?screen_name={username}")
    page.wait_for_load_state("load")
    time.sleep(random.uniform(1, 2))
    x_dismiss_popup(page)
    follow_btn = page.get_by_role("button", name=f"Follow @{username}", exact=True)
    following_btn = page.get_by_role("button", name=f"Following @{username}", exact=True)
    try:
        follow_btn.or_(following_btn).wait_for(timeout=15000)
    except Exception:
        logger.error(f"Follow button did not appear for {username}")
    try:
        already_following = following_btn.count() > 0
    except Exception:
        already_following = False
    if already_following:
        logger.info(f"[DETECTED] already following {username}")
        x_save_action(_x_context["profile_number"], _x_context["project"], "follow", username, username)
        return username
    human_like_mouse_click(follow_btn)
    time.sleep(random.uniform(2, 3))
    x_dismiss_popup(page)
    time.sleep(random.uniform(2, 3))
    try:
        following_btn.wait_for(timeout=8000)
        followed = True
    except Exception:
        followed = False
    if not followed:
        logger.error(f"Follow verification failed for {username}")
        x_save_action(_x_context["profile_number"], _x_context["project"], "follow", username, False)
        return None
    x_save_action(_x_context["profile_number"], _x_context["project"], "follow", username, username)
    return username


def x_like(page, tweet_id):
    done = x_is_done("like", tweet_id)
    if done:
        logger.info(f"[SKIP] like already done: {done}")
        return done
    page.goto(f"https://x.com/i/status/{tweet_id}")
    page.wait_for_load_state("load")
    time.sleep(random.uniform(1, 2))
    x_dismiss_popup(page)
    main_article = page.get_by_role("article").first
    like_btn = main_article.get_by_test_id("like")
    unlike_btn = main_article.get_by_test_id("unlike")
    try:
        like_btn.or_(unlike_btn).wait_for(timeout=15000)
    except Exception:
        logger.error(f"Like button did not appear for tweet {tweet_id}")
    try:
        already_liked = unlike_btn.count() > 0
    except Exception:
        already_liked = False
    if already_liked:
        logger.info(f"[DETECTED] already liked {tweet_id}")
        x_save_action(_x_context["profile_number"], _x_context["project"], "like", tweet_id, tweet_id)
        return tweet_id
    human_like_mouse_click(like_btn)
    time.sleep(random.uniform(2, 3))
    x_dismiss_popup(page)
    time.sleep(random.uniform(2, 3))
    try:
        unlike_btn.wait_for(timeout=8000)
        liked = True
    except Exception:
        liked = False
    if not liked:
        logger.error(f"Like verification failed for tweet {tweet_id}")
        x_save_action(_x_context["profile_number"], _x_context["project"], "like", tweet_id, False)
        return None
    x_save_action(_x_context["profile_number"], _x_context["project"], "like", tweet_id, tweet_id)
    return tweet_id


def x_retweet(page, tweet_id):
    done = x_is_done("retweet", tweet_id)
    if done:
        logger.info(f"[SKIP] retweet already done: {done}")
        return True
    page.goto(f"https://x.com/i/status/{tweet_id}")
    page.wait_for_load_state("load")
    time.sleep(random.uniform(1, 2))
    x_dismiss_popup(page)
    main_article = page.get_by_role("article").first
    retweet_btn = main_article.get_by_test_id("retweet")
    unretweet_btn = main_article.get_by_test_id("unretweet")
    try:
        retweet_btn.or_(unretweet_btn).wait_for(timeout=15000)
    except Exception:
        logger.error(f"Retweet button did not appear for tweet {tweet_id}")
    try:
        already_retweeted = unretweet_btn.count() > 0
    except Exception:
        already_retweeted = False
    if already_retweeted:
        logger.info(f"[DETECTED] already retweeted {tweet_id}")
        x_save_action(_x_context["profile_number"], _x_context["project"], "retweet", tweet_id, tweet_id)
        return True
    with page.expect_response(lambda r: "CreateRetweet" in r.url) as resp_info:
        human_like_mouse_click(retweet_btn)
        time.sleep(random.uniform(2, 3))
        human_like_mouse_click(page.get_by_test_id("retweetConfirm"))
    time.sleep(random.uniform(2, 3))
    x_dismiss_popup(page)
    success = resp_info.value.status == 200
    if not success:
        logger.error(f"Retweet failed for tweet {tweet_id}: {resp_info.value.status}")
    x_save_action(_x_context["profile_number"], _x_context["project"], "retweet", tweet_id, tweet_id if success else False)
    return success


def x_generate_comment(page):
    tweet_text = page.get_by_role("article").first.get_by_test_id("tweetText").first.inner_text()
    prompt = (
        "React to this tweet with a short, casual reply (under 12 words, no hashtags, no quote marks). "
        "Pick ONE random angle: a question, hype, mild skepticism, humor, or a personal take. "
        "Vary wording, do not default to generic hype phrases like \"exciting\" or \"can't wait\". "
        f"Tweet: \"{tweet_text}\""
    )
    return ask(prompt, temperature=1.3)


def x_click_and_capture_tweet_id(page, click_locator, tweet_id, attempts=3):
    for attempt in range(attempts):
        try:
            with page.expect_response(lambda r: "CreateTweet" in r.url, timeout=15000) as resp_info:
                human_like_mouse_click(click_locator)
            if resp_info.value.status == 200:
                return resp_info.value.json()["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"]
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{attempts}: CreateTweet response not captured for tweet {tweet_id}: {e}")
        match = re.search(r"/status/(\d+)", page.url)
        if match and match.group(1) != str(tweet_id):
            return match.group(1)
        time.sleep(random.uniform(2, 3))
    return None


def x_reply(page, tweet_id, text=None, username=None):
    done = x_is_done("reply", tweet_id)
    if done:
        logger.info(f"[SKIP] reply already done: {done}")
        return done
    page.goto(f"https://x.com/i/status/{tweet_id}")
    page.wait_for_load_state("load")
    time.sleep(random.uniform(1, 2))
    x_dismiss_popup(page)
    if text is None:
        text = x_generate_comment(page)
    human_like_type(page.get_by_test_id("tweetTextarea_0").first, text)
    time.sleep(random.uniform(2, 3))
    rest_id = x_click_and_capture_tweet_id(page, page.get_by_test_id("tweetButtonInline").first, tweet_id)
    time.sleep(random.uniform(2, 3))
    x_dismiss_popup(page)
    if rest_id is None:
        logger.error(f"Reply failed for tweet {tweet_id}")
        x_save_action(_x_context["profile_number"], _x_context["project"], "reply", tweet_id, False)
        return None
    reply_url = f"https://x.com/{username}/status/{rest_id}"
    logger.success(f"Reply posted: {reply_url}")
    x_save_action(_x_context["profile_number"], _x_context["project"], "reply", tweet_id, reply_url)
    return reply_url


def x_tag_friends(page, tweet_id, friends, username, text=None):
    done = x_is_done("tag_friends", tweet_id)
    if done:
        logger.info(f"[SKIP] tag_friends already done: {done}")
        return done
    page.goto(f"https://x.com/i/status/{tweet_id}")
    page.wait_for_load_state("load")
    time.sleep(random.uniform(1, 2))
    x_dismiss_popup(page)
    if text is None:
        text = x_generate_comment(page)
    mentions = " ".join(f"@{f}" for f in friends)
    human_like_type(page.get_by_test_id("tweetTextarea_0").first, f"{text} {mentions} ")
    time.sleep(random.uniform(2, 3))
    rest_id = x_click_and_capture_tweet_id(page, page.get_by_test_id("tweetButtonInline").first, tweet_id)
    time.sleep(random.uniform(2, 3))
    x_dismiss_popup(page)
    if rest_id is None:
        logger.error(f"Tag friends failed for tweet {tweet_id}")
        x_save_action(_x_context["profile_number"], _x_context["project"], "tag_friends", tweet_id, False)
        return None
    tag_url = f"https://x.com/{username}/status/{rest_id}"
    logger.success(f"Tag friends posted: {tag_url}")
    x_save_action(_x_context["profile_number"], _x_context["project"], "tag_friends", tweet_id, tag_url)
    return tag_url


def x_quote(page, tweet_id, text=None, username=None):
    done = x_is_done("quote", tweet_id)
    if done:
        logger.info(f"[SKIP] quote already done: {done}")
        return done
    page.goto(f"https://x.com/i/status/{tweet_id}")
    page.wait_for_load_state("load")
    time.sleep(random.uniform(1, 2))
    x_dismiss_popup(page)
    if text is None:
        text = x_generate_comment(page)
    main_article = page.get_by_role("article").first
    human_like_mouse_click(main_article.get_by_test_id("retweet").or_(main_article.get_by_test_id("unretweet")))
    time.sleep(random.uniform(1, 2))
    human_like_mouse_click(page.get_by_role("menuitem", name="Quote"))
    time.sleep(random.uniform(1, 2))
    dialog = page.get_by_role("dialog")
    human_like_type(dialog.get_by_test_id("tweetTextarea_0"), text)
    time.sleep(random.uniform(1, 2))
    rest_id = x_click_and_capture_tweet_id(page, dialog.get_by_test_id("tweetButton"), tweet_id)
    time.sleep(random.uniform(2, 3))
    x_dismiss_popup(page)
    if rest_id is None:
        logger.error(f"Quote failed for tweet {tweet_id}")
        x_save_action(_x_context["profile_number"], _x_context["project"], "quote", tweet_id, False)
        return None
    quote_url = f"https://x.com/{username}/status/{rest_id}"
    logger.success(f"Quote posted: {quote_url}")
    x_save_action(_x_context["profile_number"], _x_context["project"], "quote", tweet_id, quote_url)
    return quote_url


def x_load_results(file_name=x_results_filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def x_save_action(profile_number, project, action, target, value, file_name=x_results_filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)
    data = x_load_results(file_name)
    data.setdefault(str(profile_number), {}).setdefault(project, {}).setdefault(action, {})[str(target)] = value
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def x_count_done(project):
    data = x_load_results()
    profile_data = data.get(str(_x_context["profile_number"]), {})
    project_data = profile_data.get(project, {})
    return sum(
        1
        for targets in project_data.values()
        for value in targets.values()
        if value
    )


def activity(profile_number, email=None, email_password=None, creds=None, reply_text=None, quote_text=None, friends=None):
    try:
        puppeteer_ws = None
        x_set_context(profile_number, "hyperliquid")
        if x_count_done("hyperliquid") >= EXPECTED_ACTIONS:
            logger.info(f"[SKIP] Профиль {profile_number} уже полностью обработан.")
            return

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
            username = creds[0]
            x_password = creds[1]
            x_email = creds[2]
            x_email_password = creds[3]
            x_2fa = creds[4]
            auth_token = creds[5]
            ct0 = creds[6]
            if USE_AI_COMMENTS:
                reply_text = None
                quote_text = None
            ###########################################################################################
            page.goto("https://x.com")
            page.wait_for_load_state("load")
            login_textbox = page.get_by_role("textbox", name="Email or username")
            try:
                login_textbox.wait_for(state="visible", timeout=5000)
                needs_login = True
            except Exception:
                needs_login = False
            if needs_login:
                # x_login_with_cookies(context, page, auth_token, ct0)
                x_login_with_form(page, username, x_password, x_2fa)
                time.sleep(random.uniform(8, 10))

            # x_follow(page, "HyperliquidX")
            # time.sleep(random.uniform(2, 3))
            # x_like(page, "2090122188074491951")
            # time.sleep(random.uniform(2, 3))
            # x_retweet(page, "2090122188074491951")
            # time.sleep(random.uniform(2, 3))
            # x_reply(page, "2090122188074491951", reply_text, username)
            # time.sleep(random.uniform(2, 3))
            # x_quote(page, "2090122188074491951", quote_text, username)
            # if friends:
            #     time.sleep(random.uniform(2, 3))
            #     x_tag_friends(page, "2090122188074491951", friends, username)


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
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for fname in ("profiles.txt", "accounts.txt", "email.txt", "credentials.txt", "reply.txt", "quote.txt", "friends.txt"):
        if not os.path.exists(os.path.join(base_dir, fname)):
            logger.warning(f"[FILE MISSING] {fname}")

    x_credentials = x_load_credentials("credentials.txt")
    x_replies = x_load_lines("reply.txt")
    x_quotes = x_load_lines("quote.txt")
    x_friends = x_load_friends("friends.txt")

    profiles = load_profiles("profiles.txt")
    regular_accounts = load_email_accounts("accounts.txt")

    if not profiles:
        logger.error("profiles.txt is empty")
        raise SystemExit(1)

    if len(x_credentials) < len(profiles):
        logger.error(
            f"Not enough lines in credentials.txt: {len(x_credentials)} < {len(profiles)}"
        )
        raise SystemExit(1)

    if not USE_AI_COMMENTS and (len(x_replies) < len(profiles) or len(x_quotes) < len(profiles)):
        logger.error(
            f"Not enough lines: reply.txt={len(x_replies)}, quote.txt={len(x_quotes)}, needed={len(profiles)}"
        )
        raise SystemExit(1)

    items = [
        (
            profiles[i],
            regular_accounts[i][0] if i < len(regular_accounts) else None,
            regular_accounts[i][1] if i < len(regular_accounts) else None,
            x_credentials[i] if i < len(x_credentials) else None,
            x_replies[i] if i < len(x_replies) else None,
            x_quotes[i] if i < len(x_quotes) else None,
            x_friends[i] if i < len(x_friends) else None,
        )
        for i in range(len(profiles))
    ]

    if SHUFFLE_WALLETS:
        random.shuffle(items)

    for profile, email, email_password, creds, reply_text, quote_text, friends in items:
        activity(profile, email, email_password, creds, reply_text, quote_text, friends)
