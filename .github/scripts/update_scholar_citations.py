#!/usr/bin/env python3
"""Refresh the Google Scholar "Cited by" badges in P_by_year.html.

Scrapes the citation counts from the public Google Scholar profile page and
writes them into the existing ``class="cite-count"`` links, keeping the
``citation_for_view`` target in sync. Exits non-zero only when the profile
cannot be read, so a transient Scholar outage never rewrites the page.
"""

import html
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCHOLAR_USER = "lNvHzJEAAAAJ"
PROFILE_URL = (
    "https://scholar.google.com/citations?hl=en&user={user}&cstart=0&pagesize=100"
)
PAGE = Path(__file__).resolve().parents[2] / "P_by_year.html"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

ROW_RE = re.compile(r'<tr class="gsc_a_tr">(.*?)</tr>', re.S)
ROW_TITLE_RE = re.compile(r'<a href="([^"]*)"[^>]*class="gsc_a_at">(.*?)</a>', re.S)
ROW_COUNT_RE = re.compile(r'class="gsc_a_ac[^"]*"[^>]*>\s*(\d*)\s*<')

TOKEN_RE = re.compile(
    r'<a style="color: #000000; text-decoration: none;">(?P<title>.*?)</a>'
    r"|(?P<badge><a href=\"https://scholar\.google\.com/citations\?view_op=view_citation"
    r'[^>]*class="cite-count"[^>]*>.*?Cited by (?P<count>\d+)</a>)',
    re.S,
)
CITATION_ID_RE = re.compile(r"(citation_for_view=%s:)([\w-]+)" % SCHOLAR_USER)
CITED_BY_RE = re.compile(r"Cited by \d+")


def normalize(text):
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\xa0", " ")
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def scrape(url, attempts=3):
    """Return the page body, retrying transient failures."""
    last_error = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": random.choice(USER_AGENTS),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                page = response.read().decode("utf-8", "ignore")
            if "gsc_a_tr" in page:
                return page
            last_error = "response had no publication rows (captcha or API error)"
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = str(exc)
        print(
            "  attempt %d/%d failed: %s" % (attempt, attempts, last_error),
            file=sys.stderr,
        )
        if attempt < attempts:
            time.sleep(20 * attempt)
    raise RuntimeError(last_error)


def fetch_profile():
    url = PROFILE_URL.format(user=SCHOLAR_USER)
    try:
        return scrape(url)
    except RuntimeError as exc:
        raise SystemExit("Could not read the Google Scholar profile: %s" % exc)


def parse_counts(page):
    counts = {}
    for row in ROW_RE.findall(page):
        title = ROW_TITLE_RE.search(row)
        if not title:
            continue
        href, raw_title = title.group(1), title.group(2)
        citation_id = CITATION_ID_RE.search(href)
        count = ROW_COUNT_RE.search(row)
        counts[normalize(raw_title)] = (
            int(count.group(1)) if count and count.group(1) else 0,
            citation_id.group(2) if citation_id else None,
        )
    if not counts:
        raise SystemExit("No publications found on the Google Scholar profile")
    return counts


def rewrite(page, counts):
    changed = []
    seen = set()
    current = None
    pieces = []
    last = 0
    for match in TOKEN_RE.finditer(page):
        pieces.append(page[last:match.start()])
        last = match.end()

        if match.group("title") is not None:
            current = normalize(match.group("title"))
            pieces.append(match.group(0))
            continue

        entry = counts.get(current) if current else None
        if entry is None:
            pieces.append(match.group(0))
            continue

        seen.add(current)
        count, citation_id = entry
        badge = match.group(0)
        if citation_id:
            badge = CITATION_ID_RE.sub(
                lambda m: m.group(1) + citation_id, badge, count=1
            )
        badge = CITED_BY_RE.sub("Cited by %d" % count, badge, count=1)

        old = int(match.group("count"))
        if old != count:
            changed.append((current, old, count))
        pieces.append(badge)

    pieces.append(page[last:])
    return "".join(pieces), changed, seen


def main():
    counts = parse_counts(fetch_profile())
    page = PAGE.read_text(encoding="utf-8")
    updated, changed, seen = rewrite(page, counts)

    missing = [key for key in counts if key not in seen]
    if missing:
        print(
            "Warning: %d Scholar entries have no matching badge on the page:"
            % len(missing),
            file=sys.stderr,
        )
        for key in missing:
            print("  - " + key, file=sys.stderr)

    if updated == page:
        print("Citation counts are already up to date.")
        return

    PAGE.write_text(updated, encoding="utf-8", newline="")
    print("Updated %d citation count(s):" % len(changed))
    for key, before, after in changed:
        print("  %s: %d -> %d" % (key, before, after))


if __name__ == "__main__":
    main()
