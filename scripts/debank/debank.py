"""Export wallet tokens as token/amount/usd_value and the 20 latest transactions.

Profiles and addresses correspond by line number. Run from any directory:
    python scripts/debank/debank.py --profile 1
    python scripts/debank/debank.py              # all profiles, in file order
Only a fully verified set of five CSVs is recorded in _results.txt.
"""

import argparse
import csv
import json
import os
import re
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from loguru import logger
from patchright.sync_api import expect, sync_playwright

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parents[1] / ".env")
ADSPOWER_API_URL = os.getenv("ADSPOWER_API_URL", "http://localhost:50325").rstrip("/")
HEADLESS_NEW = True
TIMEOUT = 60_000
PORTFOLIO_TIMEOUT = 300_000
TRANSACTION_LIMIT = 20
RESULTS_FILE = BASE_DIR / "_results.txt"
CHAINS = (("eth", "Ethereum", "ethereum.csv"),
          ("arb", "Arbitrum", "arbitrum.csv"),
          ("base", "Base", "base.csv"))
PORTFOLIO_FIELDS = ("token", "amount", "usd_value")
TRANSACTION_FIELDS = ("profile", "address", "collected_at_utc", "chain", "tx_hash",
                      "tx_url", "time", "action", "changes", "explanation",
                      "token_changes_json", "text")



def read_lines(filename):
    return [line.strip() for line in (BASE_DIR / filename).read_text(encoding="utf-8-sig").splitlines()
            if line.strip()]


def load_profiles(file_name="profiles.txt"):
    return read_lines(file_name)


def load_wallets_from_file(file_name="addresses.txt"):
    return read_lines(file_name)


def profile_pairs():
    profiles = load_profiles()
    addresses = load_wallets_from_file()
    if not profiles or len(profiles) != len(addresses):
        raise ValueError("profiles.txt and addresses.txt must contain the same nonzero number of lines")
    if len(set(profiles)) != len(profiles):
        raise ValueError("Duplicate profile numbers in profiles.txt")
    for profile, address in zip(profiles, addresses):
        if not re.fullmatch(r"[0-9]+", profile):
            raise ValueError(f"Invalid profile number: {profile!r}")
        if not re.fullmatch(r"0x[0-9a-fA-F]{40}", address):
            raise ValueError(f"Invalid address for profile {profile}: {address!r}")
    return list(zip(profiles, addresses))


def ads_request(endpoint, **params):
    response = requests.get(f"{ADSPOWER_API_URL}/api/v1/browser/{endpoint}",
                            params=params, timeout=45)
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != 0:
        raise RuntimeError(f"ADSPower {endpoint}: {payload.get('msg', payload)}")
    return payload.get("data", {})


def start_browser(profile_number, headless=False):
    params = {"serial_number": profile_number, "open_tabs": 1}
    if headless:
        params["headless"] = 1
    return ads_request("start", **params)["ws"]["puppeteer"]


def close_browser(profile_number):
    ads_request("stop", serial_number=profile_number)


def unique_visible(locator):
    """Re-resolve against the current DOM and require an unambiguous target."""
    target = locator.filter(visible=True)
    expect(target).to_have_count(1)
    expect(target).to_be_visible()
    return target


def check_dom(page, step):
    """Validate the current page after every navigation/interaction."""
    main = page.get_by_role("main")
    expect(main).to_have_count(1)
    expect(main).to_be_visible()
    text = main.inner_text()
    blockers = r"verify you are human|access denied|too many requests|something went wrong|failed to load|sign in to view|connect wallet to view"
    if re.search(blockers, text, re.I):
        raise RuntimeError(f"{step}: DeBank returned an error or access restriction")
    if step != "waiting for data":
        logger.debug("DOM checked: {} ({})", step, page.url)
    return main


# Poll only rendered structure/readiness. Prices, rewards and relative clocks
# can change continuously and must not restart the stability timer.
DOM_STATE = r"""main => {
    const text = e => (e?.innerText || '').trim();
    const visible = e => !!(e.getClientRects().length);
    const history = location.pathname.endsWith('/history');
    const content = text(main);
    const loading = [...main.querySelectorAll('div,span')].some(e =>
        visible(e) && /^(Updating data|Loading(?:\.\.\.)?)$/i.test(text(e)));
    const empty = /No (?:assets|tokens|holdings|portfolio|transactions|history|records)|Nothing to show/i.test(content);
    const wallet = main.querySelector('#Wallet')?.parentElement;
    const headers = wallet ? [...wallet.querySelectorAll('.db-table-headerItem')].map(text) : [];
    const tokens = [...(wallet?.querySelectorAll('.db-table-row') || [])].map(row => ({
        links: [...row.querySelectorAll('a[href^="/token/"]')].map(a => a.getAttribute('href')),
        cells: [...row.querySelectorAll(':scope > .db-table-cell')].map(e => !!text(e))}));
    const transactions = [...main.querySelectorAll('a[href*="/tx/"]')].map(a => a.href);
    const ready = history ? transactions.length > 0 || empty :
        (!!wallet && headers.join('|') === 'Token|Price|Amount|USD Value' &&
            tokens.every(r => r.links.length === 1 && r.cells.length === 4 &&
                r.cells.every(Boolean))) || empty;
    return {ready, loading, empty, tokens: tokens.length,
        transactions: transactions.length,
        fingerprint: JSON.stringify({history, empty, wallet: !!wallet, tokens, transactions, headers})};
}"""


def settle_dom(page):
    """Wait for complete rendered tables, not for changing prices to freeze."""
    history = page.url.split("?", 1)[0].endswith("/history")
    timeout = TIMEOUT if history else PORTFOLIO_TIMEOUT
    deadline = time.monotonic() + timeout / 1000
    previous = None
    stable_since = time.monotonic()
    next_progress = time.monotonic() + 15
    state = {}
    while time.monotonic() < deadline:
        main = check_dom(page, "waiting for data")
        state = main.evaluate(DOM_STATE)
        current = state["fingerprint"]
        if current != previous or state["loading"] or not state["ready"]:
            previous = current
            stable_since = time.monotonic()
        elif time.monotonic() - stable_since >= 1.2:
            return main
        if time.monotonic() >= next_progress:
            logger.info("Waiting for DeBank: updating={}, tokens={}, transactions={}",
                        state["loading"], state["tokens"], state["transactions"])
            next_progress = time.monotonic() + 15
        page.wait_for_timeout(300)
    raise TimeoutError(f"DeBank tables not ready after {timeout // 1000}s: "
                       f"updating={state.get('loading')}, "
                       f"tokens={state.get('tokens')}, transactions={state.get('transactions')}")


def click_checked(page, locator, step):
    unique_visible(locator).click()
    check_dom(page, step)


def open_portfolio(page, address):
    page.goto(f"https://debank.com/profile/{address}", wait_until="domcontentloaded")
    main = check_dom(page, "open portfolio")
    cookie = page.get_by_role("dialog").get_by_role("button", name="Accept", exact=True)
    if cookie.is_visible():
        click_checked(page, cookie, "accept cookies")
    expect(main.get_by_text(address, exact=True)).to_be_visible(timeout=TIMEOUT)
    expect(main.get_by_text("All Chain", exact=True)).to_be_visible(timeout=TIMEOUT)
    settle_dom(page)


def expand_portfolio(page):
    main = check_dom(page, "before expanding wallet tokens")
    # Restrict this control to Wallet; DeFi balances are outside the export.
    wallet = main.locator("#Wallet").locator("..")
    if wallet.count():
        more = wallet.get_by_text(re.compile(r"^Tokens with small balances are not displayed\."))
        if more.is_visible():
            click_checked(page, more, "expand wallet tokens")
            settle_dom(page)
    expand_chains(page)


def expand_chains(page):
    main = check_dom(page, "before expanding chains")
    unfold = main.get_by_text(re.compile(r"^Unfold \d+ chains$"))
    if unfold.is_visible():
        click_checked(page, unfold, "expand chains")
        settle_dom(page)


# DeBank's wallet has no ARIA table role. Its stable Wallet ID, table
# classes and token hrefs identify the rows; generated CSS classes are unused.
PORTFOLIO_DOM = r"""main => {
    const text = e => (e?.innerText || '').trim();
    const wallet = main.querySelector('#Wallet')?.parentElement;
    if (!wallet) return {rows: [], chains: [], text: text(main), wallet: false};
    const headers = [...wallet.querySelectorAll('.db-table-headerItem')].map(text);
    if (headers.join('|') !== 'Token|Price|Amount|USD Value')
        throw Error('Wallet table headers changed');
    const cleanNumber = value => value.replace(/[$,]/g, '').replace(
        /0\.0([₀₁₂₃₄₅₆₇₈₉]+)(\d+)/g, (_, subscript, digits) => {
            const count = Number([...subscript].map(c => '₀₁₂₃₄₅₆₇₈₉'.indexOf(c)).join(''));
            if (count > 100) throw Error('Unexpected number notation');
            return '0.' + '0'.repeat(count) + digits;
        });
    const chains = [];
    const rows = [...wallet.querySelectorAll('.db-table-row')].map(row => {
        const cells = [...row.querySelectorAll(':scope > .db-table-cell')].map(text);
        const links = [...row.querySelectorAll('a[href^="/token/"]')];
        if (cells.length !== 4 || links.length !== 1 || cells.some(c => !c))
            throw Error('Wallet row changed or is incomplete');
        chains.push(links[0].getAttribute('href').split('/')[2]);
        return {token: text(links[0]), amount: cleanNumber(cells[2]),
                usd_value: cleanNumber(cells[3])};
    });
    return {rows, chains, text: text(wallet), wallet: true};
}"""


def collect_portfolio(page, scope):
    expand_portfolio(page)
    main = settle_dom(page)
    data = main.evaluate(PORTFOLIO_DOM)
    if not data["rows"] and not re.search(
            r"No assets|No tokens|No holdings|No portfolio", data["text"], re.I):
        raise RuntimeError(f"{scope}: no wallet tokens or explicit empty state")
    if scope != "all" and set(data["chains"]) - {scope}:
        raise RuntimeError(f"Wrong network in {scope} wallet: {set(data['chains'])}")
    logger.info("Wallet {}: {} tokens", scope, len(data["rows"]))
    return data["rows"]


TRANSACTIONS_DOM = r"""(main, limit) => {
    const text = e => (e?.innerText || '').trim();
    return [...main.querySelectorAll('a[href*="/tx/"]')].slice(0, limit).map(a => {
        const row = a.parentElement.parentElement.parentElement;
        const cells = [...row.children];
        if (cells.length !== 4 || row.querySelectorAll('a[href*="/tx/"]').length !== 1)
            throw Error('Transaction row structure changed');
        const chain = cells[0].querySelector('img[alt]')?.alt || '';
        const hash = a.href.match(/\/tx\/([^/?#]+)/)?.[1];
        if (!chain || !hash) throw Error('Missing transaction chain/hash');
        return {chain, tx_hash: hash, tx_url: a.href,
            time: text(cells[0]).replace(text(a), '').trim(), action: text(cells[1]),
            changes: text(cells[2]), explanation: text(cells[3]), text: text(row),
            token_changes: [...row.querySelectorAll('[data-token-chain][data-id]')].map(e => ({
                chain: e.dataset.tokenChain, id: e.dataset.id, name: e.dataset.name || '',
                text: text(e)}))};
    });
}"""


def collect_transactions(page, profile_number, wallet_addr):
    main = check_dom(page, "before Transactions")
    click_checked(page, main.get_by_text("Transactions", exact=True), "open Transactions")
    expect(page).to_have_url(re.compile(r"/history(?:\?|$)"))
    # This is collected before changing the portfolio chain, but verify the
    # actual filter rather than assuming a tab switch resets it.
    expect(main.get_by_text("All Chain", exact=True)).to_be_visible()
    expect(main.get_by_text("Filter by token: All", exact=True)).to_be_visible()
    main = settle_dom(page)
    current = main.evaluate(TRANSACTIONS_DOM, TRANSACTION_LIMIT)
    if not current:
        text = main.inner_text()
        if not re.search(r"No transactions|No history|No records", text, re.I):
            raise RuntimeError("No transactions and no explicit empty state")
    keys = [(row["chain"], row["tx_hash"]) for row in current]
    if len(set(keys)) != len(keys):
        raise RuntimeError("Duplicate transactions in the latest batch")
    logger.info("Latest transactions: {} (limit {})", len(current), TRANSACTION_LIMIT)
    metadata = {"profile": str(profile_number), "address": wallet_addr,
                "collected_at_utc": datetime.now(timezone.utc).isoformat()}
    for row in current:
        row["token_changes_json"] = json.dumps(row.pop("token_changes"), ensure_ascii=False)
        row.update(metadata)
    return current


def write_csv(path, fields, rows):
    """Write exactly the schema produced by the collector, with no extra columns."""
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != tuple(fields) or sum(1 for _ in reader) != len(rows):
            raise RuntimeError(f"CSV verification failed: {path}")


def load_successful_profiles():
    if not RESULTS_FILE.exists():
        return set()
    return set(RESULTS_FILE.read_text(encoding="utf-8").splitlines())


def save_success(profile_number):
    existing = load_successful_profiles()
    existing.add(str(profile_number))
    temporary = RESULTS_FILE.with_suffix(".txt.tmp")
    temporary.write_text("".join(f"{p}\n" for p in sorted(existing, key=int)), encoding="utf-8")
    temporary.replace(RESULTS_FILE)


def valid_export(profile_number, address):
    folder = BASE_DIR / str(profile_number)
    expected = {"portfolio.csv", "ethereum.csv", "arbitrum.csv", "base.csv", "transactions.csv"}
    if not folder.is_dir() or {p.name for p in folder.iterdir()} != expected:
        return False
    # Identity stays in the input files and folder name, outside the three
    # requested columns. Any input change forces a fresh collection.
    inputs_modified = max((BASE_DIR / name).stat().st_mtime_ns
                          for name in ("profiles.txt", "addresses.txt"))
    for filename in expected:
        path = folder / filename
        if path.stat().st_mtime_ns < inputs_modified:
            return False
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                fields = TRANSACTION_FIELDS if filename == "transactions.csv" else PORTFOLIO_FIELDS
                if tuple(reader.fieldnames or ()) != fields:
                    return False
                rows = list(reader)
                if any(None in row or None in row.values() for row in rows):
                    return False
                if filename == "transactions.csv":
                    if len(rows) > TRANSACTION_LIMIT:
                        return False
                    if any(r["profile"] != str(profile_number) or r["address"].lower() != address.lower()
                           or not r["tx_hash"] or not r["time"] or not r["chain"] for r in rows):
                        return False
                    if len({(r["chain"], r["tx_hash"]) for r in rows}) != len(rows):
                        return False
                elif any(not r["token"] or not r["amount"] or not r["usd_value"] for r in rows):
                    return False
        except (OSError, UnicodeError, csv.Error):
            return False
    return True


def activity(profile_number, wallet_addr, *, force=False, keep_open=False):
    profile_number = str(profile_number)
    if not force and profile_number in load_successful_profiles() and valid_export(profile_number, wallet_addr):
        logger.info("[SKIP] Profile {} already exported", profile_number)
        return True
    started = False
    staging = None
    page = None
    try:
        logger.info("Starting ADSPower profile {}", profile_number)
        started = True
        endpoint = start_browser(profile_number, headless=HEADLESS_NEW)
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(endpoint)
            if not browser.contexts:
                raise RuntimeError("ADSPower browser has no existing context")
            context = browser.contexts[0]
            page = context.new_page()
            page.set_default_timeout(TIMEOUT)
            page.set_default_navigation_timeout(TIMEOUT)
            open_portfolio(page, wallet_addr)
            portfolios = {"portfolio.csv": ("all", collect_portfolio(page, "all"))}
            # Collect the latest all-chain transactions before selecting a network.
            transactions = collect_transactions(page, profile_number, wallet_addr)
            click_checked(page, page.get_by_role("main").get_by_text("Portfolio", exact=True),
                          "return to Portfolio")
            settle_dom(page)
            for chain, name, filename in CHAINS:
                expand_chains(page)
                main = check_dom(page, f"before selecting {name}")
                # Exact data-chain scopes the semantic name to a single chain.
                target = main.locator(f'[data-chain="{chain}"]').filter(
                    has=page.get_by_text(name, exact=True))
                click_checked(page, target, f"select {name}")
                settle_dom(page)
                portfolios[filename] = (chain, collect_portfolio(page, chain))
            staging = Path(tempfile.mkdtemp(prefix=f".{profile_number}-", dir=BASE_DIR))
            for filename, (scope, rows) in portfolios.items():
                write_csv(staging / filename, PORTFOLIO_FIELDS, rows)
            write_csv(staging / "transactions.csv", TRANSACTION_FIELDS, transactions)
            destination = BASE_DIR / profile_number
            # All network reads and all CSV checks have succeeded before replacing
            # an existing result. Preserve the previous export if replacement fails.
            backup = BASE_DIR / f".{profile_number}-previous"
            if backup.exists():
                raise RuntimeError(f"Previous interrupted export needs review: {backup}")
            if destination.exists():
                destination.rename(backup)
            try:
                staging.rename(destination)
                staging = None
                if not valid_export(profile_number, wallet_addr):
                    raise RuntimeError("Final export verification failed")
            except Exception:
                if destination.exists():
                    shutil.rmtree(destination)
                if backup.exists():
                    backup.rename(destination)
                raise
            save_success(profile_number)
            if backup.exists():
                shutil.rmtree(backup)
            logger.success("Profile {}: five CSV files saved in {}", profile_number, destination)
            if not keep_open:
                page.close()
        return True
    except Exception:
        logger.exception("Export failed for profile {}; success was not recorded", profile_number)
        return False
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
        if started and not keep_open:
            try:
                close_browser(profile_number)
            except Exception as error:
                logger.warning("Could not close profile {}: {}", profile_number, error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="Export just this profile number from profiles.txt")
    parser.add_argument("--force", action="store_true", help="Refresh an already successful export")
    parser.add_argument("--keep-open", action="store_true", help="Leave the ADSPower browser open")
    args = parser.parse_args()
    pairs = profile_pairs()
    if args.profile:
        pairs = [(p, a) for p, a in pairs if p == args.profile]
        if not pairs:
            parser.error("The requested profile is not in profiles.txt")
    outcomes = [activity(p, a, force=args.force, keep_open=args.keep_open) for p, a in pairs]
    return 0 if all(outcomes) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        logger.warning("Stopped by user; incomplete exports were not marked successful")
        raise SystemExit(130)
