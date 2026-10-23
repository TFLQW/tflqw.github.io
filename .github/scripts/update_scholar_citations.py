#!/usr/bin/env python3
"""Refresh the Google Scholar "Cited by" counters on the publication pages.

Scrapes the citation counts from the public Google Scholar profile page and
writes them into the existing ``class="cite-count"`` spans on P_by_year.html and
P_by_type.html. Exits non-zero only when the profile cannot be read, so a
transient Scholar outage never rewrites the pages.
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
PAGES = [
    Path(__file__).resolve().parents[2] / name
    for name in ("P_by_year.html", "P_by_type.html")
]

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
    r'|(?P<badge><span class="cite-count"[^>]*>.*?Cited by (?P<count>\d+)</span>)',
    re.S,
)
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
        count = ROW_COUNT_RE.search(row)
        counts[normalize(title.group(2))] = (
            int(count.group(1)) if count and count.group(1) else 0
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
        badge = CITED_BY_RE.sub("Cited by %d" % entry, match.group(0), count=1)

        old = int(match.group("count"))
        if old != entry:
            changed.append((current, old, entry))
        pieces.append(badge)

    pieces.append(page[last:])
    return "".join(pieces), changed, seen


def main():
    counts = parse_counts(fetch_profile())

    for path in PAGES:
        page = path.read_text(encoding="utf-8")
        updated, changed, seen = rewrite(page, counts)

        missing = [key for key in counts if key not in seen]
        if missing:
            print(
                "Warning: %s has no badge for %d Scholar entries:"
                % (path.name, len(missing)),
                file=sys.stderr,
            )
            for key in missing:
                print("  - " + key, file=sys.stderr)

        if updated == page:
            print("%s: citation counts are already up to date." % path.name)
            continue

        path.write_text(updated, encoding="utf-8", newline="")
        print("%s: updated %d citation count(s)" % (path.name, len(changed)))
        for key, before, after in changed:
            print("  %s: %d -> %d" % (key, before, after))


if __name__ == "__main__":
    main()
