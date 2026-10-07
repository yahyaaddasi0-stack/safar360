#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sequential, restartable Micro-Khizana enrichment for pending Sard360 posts.

The script never invents ISBNs or treats an HTTP 200 bot/challenge page as a
valid Amazon product. It only publishes a shelf after bibliographic lookup,
ISBN edition resolution, live Amazon product-title verification, and a final
HTML/link audit. Registry checkpoints are written atomically per post.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WP_BASE = "https://sard360.com/wp-json/wp/v2"
REGISTRY_PATH = Path(__file__).with_name("articles_registry.json")
SHELF_PREFIX = "sard360-khizana-article-"
AMAZON_TAG = "sard360-20"
MODEL = "gpt-5-mini"
OPENLIBRARY_SEARCH = "https://openlibrary.org/search.json"
UA = "Sard360-KhizanaResearch/1.0 (https://sard360.com)"

BOOK_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "author": {"type": "string"},
        "title_ar": {"type": "string"},
        "author_ar": {"type": "string"},
        "kind_ar": {"type": "string"},
        "summary_ar": {"type": "string"},
        "rationale": {"type": "string"},
    },
    "required": ["title", "author", "title_ar", "author_ar", "kind_ar", "summary_ar", "rationale"],
    "additionalProperties": False,
}

SCHEMA = {
    "type": "object",
    "properties": {
        "is_book_list": {"type": "boolean"},
        "listed_work_count": {"type": "integer"},
        "books": {"type": "array", "items": BOOK_SCHEMA},
        "alternates": {"type": "array", "items": BOOK_SCHEMA},
    },
    "required": ["is_book_list", "listed_work_count", "books", "alternates"],
    "additionalProperties": False,
}

STOP = {
    "the", "a", "an", "of", "and", "in", "on", "for", "to", "by", "with", "from", "at", "as",
    "de", "la", "le", "les", "des", "du", "et", "un", "une", "el", "al", "fi", "wa", "an",
}

# Exact citation titles already present in the first pending article's
# bibliography; these avoid asking an LLM to reverse-translate Arabic titles.
MANUAL_BOOK_SEEDS = {
    "4818": [
        {
            "title": "Rosalind Franklin: The Dark Lady of DNA",
            "author": "Brenda Maddox",
            "title_ar": "روزاليند فرانكلين: سيرة عالمة كشفت أسرار الحمض النووي",
            "author_ar": "بريندا مادوكس",
            "kind_ar": "سيرة علمية موثقة",
            "summary_ar": "سيرة صحفية راسخة تعيد بناء مسار روزاليند فرانكلين العلمي، وتضع صورها البلورية في سياقها التاريخي والإنساني.",
            "rationale": "Book explicitly cited in the article bibliography; title, author and ISBN independently checked.",
        },
        {
            "title": "Pirates of the South China Coast, 1790–1810",
            "author": "Dian H. Murray",
            "title_ar": "قراصنة ساحل جنوب الصين: 1790–1810",
            "author_ar": "ديان مَري",
            "kind_ar": "دراسة تاريخية أكاديمية",
            "summary_ar": "دراسة تاريخية موثقة عن شبكات القرصنة في بحر الصين الجنوبي، وتكشف البنية الاجتماعية والسياسية التي صعدت منها تشينغ شي.",
            "rationale": "Book explicitly cited in the article bibliography; Stanford University Press, 1987.",
        },
    ]
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def tokens(s: str) -> set[str]:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return {t for t in re.findall(r"[a-z0-9]+", s) if len(t) > 1 and t not in STOP}


def overlap(a: str, b: str) -> float:
    aa, bb = tokens(a), tokens(b)
    return len(aa & bb) / max(1, len(aa))


def is_valid_isbn10(value: str) -> bool:
    s = re.sub(r"[^0-9Xx]", "", value).upper()
    return len(s) == 10 and all(c.isdigit() for c in s[:9]) and sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(s)) % 11 == 0


def isbn13_to_10(value: str) -> str | None:
    s = re.sub(r"[^0-9]", "", value)
    if len(s) != 13 or not s.startswith("978"):
        return None
    core = s[3:12]
    checksum = (11 - sum((10 - i) * int(d) for i, d in enumerate(core)) % 11) % 11
    out = core + ("X" if checksum == 10 else str(checksum))
    return out if is_valid_isbn10(out) else None


def clean_html(raw: str) -> str:
    raw = re.sub(r"(?is)<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->", " ", raw or "")
    raw = re.sub(r"(?i)</(?:p|h[1-6]|li|tr|div|section|blockquote)>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    return re.sub(r"[ \t\r\f\v]+", " ", raw).strip()


def heading_texts(raw: str) -> list[str]:
    out = []
    for m in re.finditer(r"(?is)<h[1-4]\b[^>]*>(.*?)</h[1-4]>", raw or ""):
        out.append(clean_html(m.group(1)))
    return out


def has_shelf(raw: str) -> bool:
    return bool(re.search(r'(?is)<section\b[^>]*\bid=["\']sard360-[^"\']*(?:shelf|khizana)[^"\']*["\']', raw or ""))


def credentials() -> tuple[str, str]:
    user, password = os.getenv("SARD360_WP_USERNAME"), os.getenv("SARD360_WP_APPLICATION_PASSWORD")
    if not user or not password:
        raise RuntimeError("WordPress credentials unavailable in this environment")
    return user, password


def api_session() -> requests.Session:
    s = requests.Session()
    s.auth = credentials()
    s.headers.update({"User-Agent": UA, "Accept": "application/json"})
    return s


def fetch_published(s: requests.Session) -> list[dict]:
    posts, page = [], 1
    while True:
        r = s.get(f"{WP_BASE}/posts", params={"context": "edit", "status": "publish", "per_page": 100, "page": page}, timeout=60)
        if r.status_code == 400 and page > 1:
            break
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return posts


def update_registry_from_posts(registry: dict, posts: list[dict]) -> None:
    for post in posts:
        pid = str(post["id"])
        item = registry.setdefault(pid, {})
        item["title"] = (post.get("title") or {}).get("raw") or (post.get("title") or {}).get("rendered") or item.get("title", "")
        item["slug"] = post.get("slug", item.get("slug", ""))
        item["link"] = post.get("link", item.get("link", ""))
        if has_shelf((post.get("content") or {}).get("raw", "")):
            item["status"] = "treated"
            item.pop("last_error", None)
        elif item.get("status") == "treated":
            item["status"] = "pending"
            item["note"] = "Registry was treated but no Micro-Khizana shelf is present in current WordPress content."
        else:
            item["status"] = "pending"
        item["cinema_video"] = item.get("cinema_video") or {"status": "unmatched", "id": None, "title": None}
    atomic_json(REGISTRY_PATH, registry)


def article_evidence(post: dict) -> tuple[str, str, list[str]]:
    raw = (post.get("content") or {}).get("raw", "")
    text = clean_html(raw)
    headings = heading_texts(raw)
    # Keep full article text up to a safe input size; prioritize cited sources at the end.
    body = text[:10000]
    tail = text[-6000:] if len(text) > 10000 else ""
    bibliography_markers = ["المراجع والمصادر", "المراجع", "المصادر", "References", "Bibliography"]
    bib = ""
    for marker in bibliography_markers:
        idx = text.rfind(marker)
        if idx >= 0:
            bib = text[idx:idx + 4500]
            break
    evidence = f"ARTICLE TEXT (excerpt):\n{body}\n"
    if tail:
        evidence += f"\nARTICLE END (contains likely bibliography):\n{tail}\n"
    if bib:
        evidence += f"\nBIBLIOGRAPHY EXTRACT:\n{bib}\n"
    return evidence, raw, headings


def llm_recommendations(title: str, evidence: str, headings: list[str]) -> dict:
    api_key, base = os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_API_BASE", "").rstrip("/")
    if not api_key or not base:
        raise RuntimeError("LLM proxy credentials unavailable")
    prompt = f"""For this Sard360 Arabic article, propose only real, reputable published books suitable for its Micro-Khizana shelf. First select books explicitly cited in its bibliography if those citations are real and relevant. Otherwise choose well-established primary sources, biographies, academic presses, or respected scholarly/popular-science works. Do not invent a title, author, ISBN, publisher, or edition. I will independently verify the edition in library records and on Amazon; if unsure, return fewer books rather than fabricate.

For ordinary topical essays, return exactly two primary books plus up to three alternate candidates (alternates are fallbacks only, not extra published cards). Use books explicitly named in the bibliography whenever possible. `title` MUST be the exact title in the published edition's original language (use the Latin-script English title for English editions); `author` MUST be the commonly used Latin-script author name. Never place an Arabic translation, transliteration, note, or guess in those two search fields. Put the Arabic display title and author only in `title_ar` and `author_ar`. If a bibliography lists only Arabic translations, identify the actual original-language edition/title if known; if uncertain, offer another verified candidate. Never add notes or alternates inside a title field. If fewer than two suitable cited books exist, choose canonical real books whose publication you are certain of, then put them in alternates if less certain. For an article that is explicitly a list/selection of BOOKS or novels (not a list of people, experiments, films, or concepts), return one product per actual listed work and set is_book_list=true; otherwise set false and return two topical books. The article already processed as an eight-novel list is not included. For a non-book list, do not pretend that the list items are books. No recommendation may be off-topic. Give concise Arabic titles/authors/kind and a distinctive, factually cautious Arabic editorial summary, without making unsupported claims. For a book-list response, leave alternates empty.

Article title: {title}
Section headings: {json.dumps(headings, ensure_ascii=False)}
{evidence}
"""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a cautious bibliographic editor. Accuracy and verifiability outrank completion; never invent books."},
            {"role": "user", "content": prompt},
        ],
        "max_completion_tokens": 4500,
        "reasoning": {"effort": "minimal"},
        "response_format": {"type": "json_schema", "json_schema": {"name": "khizana_recommendations", "strict": True, "schema": SCHEMA}},
    }
    r = requests.post(base + "/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    content = data["choices"][0]["message"].get("content")
    if not content:
        raise RuntimeError(f"LLM returned empty content (finish={data['choices'][0].get('finish_reason')})")
    result = json.loads(content)
    if not isinstance(result.get("books"), list):
        raise RuntimeError("LLM response did not contain a books list")
    return result


def resolve_book(session: requests.Session, proposal: dict, max_editions: int = 5, max_queries: int = 6) -> dict:
    title, author = proposal["title"].strip(), proposal["author"].strip()
    if not title or not author:
        raise ValueError("Missing title or author")
    title_words = [w for w in re.findall(r"[A-Za-z0-9]+", title) if len(w) > 3 and w.lower() not in STOP]
    author_words = [w for w in re.findall(r"[A-Za-z0-9]+", author) if len(w) > 2 and w.lower() not in STOP]
    focused = " ".join((author_words[-1:] + title_words[:3]))
    params_list = [
        {"title": title, "author": author},
        {"title": title},
        {"q": f"{title} {author}"},
        {"q": focused},
    ]
    if author_words:
        params_list.extend([{"author": author}, {"author": author_words[-1]}])
    docs_by_key = {}
    for search_params in params_list[:max_queries]:
        search_params.update({"fields": "title,author_name,isbn,publisher,first_publish_year", "limit": 30})
        r = session.get(OPENLIBRARY_SEARCH, params=search_params, timeout=35)
        r.raise_for_status()
        for d in r.json().get("docs", []):
            found_title = d.get("title", "")
            authors = "; ".join(d.get("author_name", []))
            # Symmetric overlap tolerates a library title without the subtitle
            # or an author listing that omits initials.
            title_forward = overlap(title, found_title)
            title_reverse = overlap(found_title, title)
            ts = max(title_forward, title_reverse)
            au = max(overlap(author, authors), overlap(authors, author))
            score = ts + (0.5 * au)
            title_match = (title_forward >= 0.45 and au >= 0.25) or (title_reverse >= 0.85 and au >= 0.55) or title_forward >= 0.75
            if title_match:
                key = d.get("key") or f"{found_title}|{authors}"
                old = docs_by_key.get(key)
                if old is None or score > old[0]:
                    docs_by_key[key] = (score, d, ts, au)
        time.sleep(0.6)
    if not docs_by_key:
        raise ValueError(f"Open Library could not confirm title/author: {title} — {author}")
    matches = sorted(docs_by_key.values(), key=lambda x: x[0], reverse=True)
    editions, seen = [], set()
    for _, d, ts, au in matches:
        isbns = d.get("isbn", []) or []
        candidates = []
        for n in isbns:
            n = re.sub(r"[^0-9Xx]", "", n).upper()
            if is_valid_isbn10(n): candidates.append(n)
            elif len(n) == 13:
                x = isbn13_to_10(n)
                if x: candidates.append(x)
        for isbn in dict.fromkeys(candidates):
            if isbn in seen:
                continue
            seen.add(isbn)
            time.sleep(0.25)
            ed = session.get(f"https://openlibrary.org/isbn/{isbn}.json", timeout=30)
            if ed.status_code != 200:
                continue
            edata = ed.json()
            exact_title = edata.get("title", d.get("title", ""))
            edition_similarity = max(overlap(title, exact_title), overlap(exact_title, title))
            if edition_similarity < 0.38:
                continue
            editions.append({
                **proposal,
                "isbn": isbn,
                "verified_title": exact_title,
                "verified_author": authors_from_doc(d),
                "publisher": (d.get("publisher") or [""])[0],
                "year": d.get("first_publish_year"),
                "openlibrary_record": f"https://openlibrary.org/isbn/{isbn}",
            })
            if len(editions) >= max_editions:
                return {"verified_editions": editions}
    if editions:
        return {"verified_editions": editions}
    raise ValueError(f"No resolvable ISBN-10 edition found for {title} — {author}")


def authors_from_doc(d: dict) -> str:
    return ", ".join(d.get("author_name", []))


def same_book(a: dict, b: dict) -> bool:
    if a.get("isbn") == b.get("isbn"):
        return True
    ta, tb = tokens(a.get("verified_title", "")), tokens(b.get("verified_title", ""))
    aa, ab = tokens(a.get("verified_author", "")), tokens(b.get("verified_author", ""))
    same_title = ta == tb or (overlap(" ".join(ta), " ".join(tb)) >= 0.95 and overlap(" ".join(tb), " ".join(ta)) >= 0.95)
    same_author = not aa or not ab or max(overlap(" ".join(aa), " ".join(ab)), overlap(" ".join(ab), " ".join(aa))) >= 0.75
    return same_title and same_author


def amazon_url(isbn: str) -> str:
    return f"https://www.amazon.com/dp/{isbn}?tag={AMAZON_TAG}"


def verify_amazon(page, book: dict, quick: bool = False) -> dict:
    url = amazon_url(book["isbn"])
    last = None
    # Amazon.com may serve an anti-automation interstitial with HTTP 200.
    # Validate the exact same ASIN against Amazon's AU catalog as a fallback,
    # but always publish the requested amazon.com affiliate URL.
    checks = [
        (f"https://www.amazon.com.au/dp/{book['isbn']}", "amazon.com.au"),
        (url, "amazon.com"),
    ]
    attempts = 1 if quick else 2
    timeout_ms = 20000 if quick else 35000
    for check_url, marketplace in checks:
      for attempt in range(attempts):
        try:
            response = page.goto(check_url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(700)
            status = response.status if response else None
            title_node = page.locator("#productTitle")
            if title_node.count():
                product_title = title_node.first.inner_text(timeout=6000).strip()
                body = page.locator("body").inner_text(timeout=8000)
                if status and status < 400 and overlap(book["title"], product_title) >= 0.35 and "page not found" not in body.lower():
                    # Make one HTTP request against the exact published .com URL.
                    # A 200 anti-bot page is not treated as the product proof;
                    # the same Amazon ASIN/title must have passed on one catalog.
                    us_response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=35, allow_redirects=True)
                    if us_response.status_code < 400:
                        time.sleep(1.5)
                        return {"url": url, "amazon_title": product_title, "http": us_response.status_code, "validated_marketplace": marketplace}
                last = f"Amazon product title mismatch ({product_title[:120]!r})"
            else:
                body = page.locator("body").inner_text(timeout=6000) if page.locator("body").count() else ""
                low = body.lower()
                if "page not found" in low or "we couldn't find that page" in low or "we could not find that page" in low:
                    last = f"{marketplace} returned its Page Not Found page"
                else:
                    last = f"{marketplace} product page/title unavailable (HTTP {status})"
        except Exception as e:
            last = f"{marketplace} browser validation failed: {str(e)[:180]}"
        if attempt + 1 < attempts:
            page.wait_for_timeout(1500)
    raise ValueError(last or "Amazon product could not be verified")


def cover_src(isbn: str) -> str:
    return f"https://images-na.ssl-images-amazon.com/images/P/{isbn}.01.LZZZZZZZ.jpg"


def build_fragment(post_id: str, title: str, books: list[dict]) -> str:
    sid = SHELF_PREFIX + re.sub(r"[^0-9]", "", post_id)
    cards = []
    for i, b in enumerate(books, 1):
        url = amazon_url(b["isbn"])
        cards.append(f'''<article class="kh-book-card">
  <div class="kh-cover"><img src="{html.escape(cover_src(b['isbn']), quote=True)}" alt="غلاف {html.escape(b['title_ar'])}" loading="lazy" decoding="async"></div>
  <p class="kh-kind">{html.escape(b['kind_ar'])} · {i:02d}</p>
  <h3 class="kh-title">{html.escape(b['title_ar'])}</h3>
  <p class="kh-original" lang="en" dir="ltr">{html.escape(b['verified_title'])}</p>
  <p class="kh-author">{html.escape(b['author_ar'])} <span lang="en" dir="ltr">· {html.escape(b['author'])}</span></p>
  <p class="kh-summary">{html.escape(b['summary_ar'])}</p>
  <a class="kh-cta" href="{url}" target="_blank" rel="sponsored nofollow noopener">اكتشف الكتاب</a>
</article>''')
    css = f'''<style id="{sid}-styles">
#{sid},#{sid} *{{box-sizing:border-box}}
#{sid}{{background:#080505;color:#f5efe2;border:1px solid rgba(212,163,89,.55);border-radius:18px;padding:26px 22px;margin:26px 0 42px;box-shadow:0 18px 45px rgba(0,0,0,.3);font-family:inherit;text-align:right;direction:rtl}}
#{sid} .kh-eyebrow{{margin:0 0 8px!important;color:#d4a359;font-size:12px;letter-spacing:.06em;line-height:1.6}}
#{sid} .kh-heading{{margin:0 0 20px!important;padding:0!important;border:0!important;background:none!important;color:#f3ead8;font-size:clamp(22px,3vw,30px)!important;line-height:1.55!important;text-align:right}}
#{sid} .kh-grid{{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;align-items:stretch;gap:16px}}
#{sid} .kh-book-card{{display:flex!important;flex-direction:column!important;align-items:stretch;min-width:0;height:auto!important;min-height:100%!important;overflow:visible!important;padding:16px 14px;background:#12151b;border:1px solid rgba(212,163,89,.32);border-radius:14px;box-shadow:0 12px 30px rgba(0,0,0,.26);transition:border-color .2s ease,transform .2s ease}}
#{sid} .kh-book-card:hover{{transform:translateY(-2px);border-color:rgba(212,163,89,.72)}}
#{sid} .kh-cover{{display:flex;align-items:center;justify-content:center;width:100%;height:154px;margin:0 0 12px;overflow:hidden}}
#{sid} .kh-cover img{{display:block!important;width:auto!important;max-width:104px!important;height:150px!important;max-height:150px!important;object-fit:contain!important;border:1px solid rgba(212,163,89,.58);border-radius:7px;box-shadow:0 8px 20px rgba(0,0,0,.4)}}
#{sid} .kh-kind{{margin:0 0 5px!important;color:#d4a359;font-size:11px;line-height:1.5;text-align:center}}
#{sid} .kh-title{{display:block!important;margin:0 0 5px!important;padding:0!important;border:0!important;background:none!important;color:#f3ead8;font-size:16px!important;line-height:1.5!important;text-align:center;overflow-wrap:anywhere}}
#{sid} .kh-original{{margin:0 0 5px!important;color:#d8c7a4;font-size:11px;line-height:1.4;text-align:center;direction:ltr;overflow-wrap:anywhere}}
#{sid} .kh-author{{margin:0 0 9px!important;color:#bdb5a8;font-size:12px;line-height:1.5;text-align:center;overflow-wrap:anywhere}}
#{sid} .kh-summary{{flex:1 1 auto;display:block!important;height:auto!important;max-height:none!important;overflow:visible!important;margin:0 0 14px!important;color:#ded7cb;font-size:12px;line-height:1.75;text-align:center;overflow-wrap:anywhere;-webkit-line-clamp:unset!important}}
#{sid} .kh-cta{{display:inline-flex!important;position:static!important;visibility:visible!important;opacity:1!important;align-items:center;justify-content:center;align-self:center;flex:0 0 auto;margin-top:auto!important;min-width:130px;min-height:40px;padding:9px 13px;border:0;border-radius:999px;background:linear-gradient(135deg,#e6c66d,#c99a3a);box-shadow:0 8px 22px rgba(212,163,89,.2);color:#16130d!important;text-decoration:none!important;text-align:center;font-family:inherit;font-size:12px;font-weight:800;line-height:1.4;white-space:normal}}
#{sid} .kh-disclosure{{display:block;width:100%;max-width:76ch;margin:18px auto 0!important;padding:12px 0 0!important;border-top:1px solid rgba(255,255,255,.08);color:#888!important;font-size:11px!important;text-align:center!important;direction:rtl;line-height:1.5!important;text-wrap:pretty;overflow-wrap:normal}}
@media(max-width:560px){{#{sid}{{padding:20px 14px}}#{sid} .kh-grid{{grid-template-columns:1fr!important;gap:13px}}#{sid} .kh-book-card{{display:grid!important;grid-template-columns:84px minmax(0,1fr);grid-template-rows:auto auto auto auto 1fr auto;column-gap:12px;align-items:start;padding:13px;text-align:right}}#{sid} .kh-cover{{grid-column:1;grid-row:1 / span 6;width:84px;height:122px;margin:0;align-self:start}}#{sid} .kh-cover img{{max-width:80px!important;height:118px!important;max-height:118px!important}}#{sid} .kh-kind,#{sid} .kh-title,#{sid} .kh-original,#{sid} .kh-author,#{sid} .kh-summary,#{sid} .kh-cta{{grid-column:2;text-align:right}}#{sid} .kh-kind{{grid-row:1}}#{sid} .kh-title{{grid-row:2}}#{sid} .kh-original{{grid-row:3;text-align:left}}#{sid} .kh-author{{grid-row:4}}#{sid} .kh-summary{{grid-row:5;margin-bottom:10px!important}}#{sid} .kh-cta{{grid-row:6;justify-self:start;min-height:36px;padding:8px 12px}}}}
@media(max-width:360px){{#{sid} .kh-book-card{{grid-template-columns:70px minmax(0,1fr);column-gap:9px}}#{sid} .kh-cover{{width:70px;height:108px}}#{sid} .kh-cover img{{max-width:66px!important;height:104px!important;max-height:104px!important}}}}
</style>'''
    cards_html = "\n".join(cards)
    title_short = "مراجع ومقتنيات لمواصلة التقصّي"
    return f'''{css}\n<section id="{sid}" aria-label="مراجع ومقتنيات من خزانة سرد">
<p class="kh-eyebrow">الخزانة · سرد 360 · {len(books)} مراجع مختارة</p>
<h2 class="kh-heading">{title_short}: {html.escape(title)}</h2>
<div class="kh-grid">\n{cards_html}\n</div>
<p class="kh-disclosure">إفصاح: تتضمن هذه الترشيحات روابط Amazon تابعة؛ وقد تحصل منصّة سرد 360 على عمولة دون كلفة إضافية عليك.</p>
</section>'''


def insertion_index(raw: str) -> int:
    # Insert before the second H3 (after the first major section), with H2 fallback.
    h3 = list(re.finditer(r"(?is)(?:<!--\s*wp:heading\b.*?-->\s*)?<h3\b", raw))
    if len(h3) >= 2:
        return h3[1].start()
    h2 = list(re.finditer(r"(?is)(?:<!--\s*wp:heading\b.*?-->\s*)?<h2\b", raw))
    if len(h2) >= 2:
        return h2[1].start()
    raise ValueError("No safe second H3/H2 insertion anchor; refusing to modify article")


def book_jsonld_script(books: list[dict], pid: str, permalink: str) -> str:
    sid = re.sub(r"[^0-9]", "", pid)
    shelf_id = SHELF_PREFIX + sid
    graph = []
    for index, book in enumerate(books, 1):
        node = {
            "@type": "Book",
            "@id": f"{permalink}#khizana-book-{sid}-{index}",
            "name": book.get("verified_title") or book.get("title") or book.get("title_ar"),
            "url": f"{permalink}#{shelf_id}",
            "author": {"@type": "Person", "name": book.get("verified_author") or book.get("author", "")},
            "isbn": book["isbn"],
            "image": cover_src(book["isbn"]),
            "description": book.get("summary_ar", ""),
            "offers": {"@type": "Offer", "url": amazon_url(book["isbn"])},
        }
        if book.get("title_ar"):
            node["alternateName"] = book["title_ar"]
        graph.append(node)
    payload = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f'<script type="application/ld+json" id="sard360-article-books-{sid}">{payload}</script>'


def make_updated(raw: str, fragment: str, pid: str, books: list[dict], permalink: str) -> str:
    if has_shelf(raw):
        raise ValueError("WordPress content already contains a Micro-Khizana shelf")
    idx = insertion_index(raw)
    updated = raw[:idx] + fragment + "\n\n" + raw[idx:]
    sid = SHELF_PREFIX + re.sub(r"[^0-9]", "", pid)
    if updated.count(f'id="{sid}"') != 1:
        raise ValueError("Shelf ID duplicate/absent after generation")
    links = re.findall(r'<a\b[^>]*class="kh-cta"[^>]*href="([^"]+)"[^>]*target="([^"]+)"[^>]*rel="([^"]+)"', fragment)
    if len(links) != len(books):
        raise ValueError("CTA count does not match book count")
    for href, target, rel in links:
        u = requests.utils.urlparse(href)
        q = dict(__import__("urllib.parse", fromlist=["parse_qsl"]).parse_qsl(u.query))
        if u.hostname != "www.amazon.com" or q.get("tag") != AMAZON_TAG or target != "_blank" or set(rel.split()) != {"sponsored", "nofollow", "noopener"}:
            raise ValueError("An affiliate URL or safe-link attribute failed DOM-source validation")
    schema = book_jsonld_script(books, pid, permalink)
    schema_id = f'sard360-article-books-{re.sub(r"[^0-9]", "", pid)}'
    existing = re.compile(rf'<script\b(?=[^>]*\bid="{re.escape(schema_id)}")[^>]*>.*?</script>', re.I | re.S)
    if existing.search(updated):
        updated = existing.sub(lambda _: schema, updated, count=1)
    else:
        updated = updated.rstrip() + f"\n\n<!-- wp:html -->\n{schema}\n<!-- /wp:html -->\n"
    if schema_id not in updated or len(json.loads(re.search(r"<script[^>]*>({.*?})</script>", schema, re.S).group(1))["@graph"]) != len(books):
        raise ValueError("Book JSON-LD validation failed")
    return updated


def save_result(registry: dict, pid: str, status: str, **fields) -> None:
    item = registry.setdefault(str(pid), {})
    item["status"] = status
    item["last_attempt"] = now_iso()
    if status == "treated":
        item.pop("last_error", None)
        item.pop("partial_books", None)
        item.pop("partial_book_isbns", None)
    item.update(fields)
    atomic_json(REGISTRY_PATH, registry)


def process_one(s: requests.Session, browser_page, registry: dict, post: dict, dry_run: bool, quick: bool = False) -> bool:
    pid = str(post["id"])
    title = (post.get("title") or {}).get("raw") or (post.get("title") or {}).get("rendered") or ""
    permalink = post.get("link", "")
    raw = (post.get("content") or {}).get("raw", "")
    verified = []
    if has_shelf(raw):
        save_result(registry, pid, "treated", title=title, link=permalink, note="Shelf already present; no duplicate created.")
        print("SKIP_ALREADY_TREATED", pid, flush=True)
        return True
    try:
        evidence, raw, headings = article_evidence(post)
        picks = {"is_book_list": False, "listed_work_count": 0, "books": MANUAL_BOOK_SEEDS[pid], "alternates": []} if pid in MANUAL_BOOK_SEEDS else llm_recommendations(title, evidence, headings)
        books = picks["books"]
        need = picks.get("listed_work_count", 0) if picks.get("is_book_list") else 2
        if picks.get("is_book_list") and need < 2:
            raise ValueError("Model flagged a book-list article but did not identify a verifiable list size")
        if len(books) != need:
            raise ValueError(f"Recommendation count mismatch: expected {need} books, received {len(books)}")
        if len({(b["title"].strip().casefold(), b["author"].strip().casefold()) for b in books}) != len(books):
            raise ValueError("Duplicate book recommendation in the same article")
        verified = []
        candidate_pool = books if picks.get("is_book_list") or quick else books + picks.get("alternates", [])
        errors = []
        for proposal in candidate_pool:
            try:
                resolved = resolve_book(s, proposal, max_editions=1 if quick else 5, max_queries=3 if quick else 6)
                for edition in resolved["verified_editions"]:
                    b = edition
                    if any(same_book(x, b) for x in verified):
                        print("BOOK_DUPLICATE_SKIPPED", json.dumps({"post_id": pid, "title": b["verified_title"], "isbn": b["isbn"]}, ensure_ascii=False), flush=True)
                        continue
                    try:
                        amz = verify_amazon(browser_page, b, quick=quick)
                    except Exception as e:
                        edition_error = f"ISBN {b['isbn']}: {str(e)[:180]}"
                        errors.append(f"{proposal.get('title','?')} — {edition_error}")
                        print("EDITION_REJECTED", json.dumps({"post_id": pid, "isbn": b["isbn"], "reason": str(e)[:220]}, ensure_ascii=False), flush=True)
                        continue
                    b["amazon_url"] = amz["url"]
                    b["amazon_title"] = amz["amazon_title"]
                    b["amazon_http"] = amz["http"]
                    b["amazon_validation_marketplace"] = amz["validated_marketplace"]
                    verified.append(b)
                    print("BOOK_VERIFIED", json.dumps({"post_id": pid, "title": b["verified_title"], "isbn": b["isbn"], "amazon_http": b["amazon_http"], "marketplace_check": b["amazon_validation_marketplace"]}, ensure_ascii=False), flush=True)
                    time.sleep(0.5)
                    if len(verified) == need:
                        break
                if len(verified) == need:
                    break
            except Exception as e:
                errors.append(f"{proposal.get('title','?')}: {str(e)[:220]}")
                print("BOOK_REJECTED", json.dumps({"post_id": pid, "title": proposal.get("title", ""), "reason": str(e)[:240]}, ensure_ascii=False), flush=True)
        if len(verified) != need:
            raise ValueError(f"Only {len(verified)}/{need} books passed all checks; candidate failures: {' | '.join(errors)}")
        if len(verified) < 2:
            raise ValueError("Fewer than two fully verified book products")
        fragment = build_fragment(pid, title, verified)
        updated = make_updated(raw, fragment, pid, verified, permalink)
        if dry_run:
            print("DRY_RUN_READY", json.dumps({"id": pid, "link": permalink, "book_count": len(verified), "books": [b["verified_title"] for b in verified]}, ensure_ascii=False), flush=True)
            return True
        # Refresh before writing to avoid overwriting edits made during research.
        latest = s.get(f"{WP_BASE}/posts/{pid}", params={"context": "edit"}, timeout=60)
        latest.raise_for_status()
        fresh = latest.json()
        fresh_raw = (fresh.get("content") or {}).get("raw", "")
        if fresh.get("status") != "publish":
            raise ValueError("Post is no longer published")
        if has_shelf(fresh_raw):
            save_result(registry, pid, "treated", title=title, link=fresh.get("link", permalink), note="Shelf appeared during processing; skipped duplicate write.")
            print("SKIP_RACE_ALREADY_TREATED", pid, flush=True)
            return True
        # Recompute insertion against fresh content and refuse if it materially changed.
        updated = make_updated(fresh_raw, fragment, pid, verified, fresh.get("link", permalink))
        result = s.post(f"{WP_BASE}/posts/{pid}", json={"content": updated}, timeout=90)
        result.raise_for_status()
        saved = result.json()
        saved_raw = (saved.get("content") or {}).get("raw", "")
        schema_id = f'sard360-article-books-{re.sub(r"[^0-9]", "", pid)}'
        if saved.get("id") != int(pid) or (saved_raw and (not has_shelf(saved_raw) or schema_id not in saved_raw)):
            raise RuntimeError("WordPress response did not confirm the new shelf")
        # The exact returned permalink is authoritative.
        link_check = requests.get(saved.get("link", permalink), headers={"User-Agent": "Mozilla/5.0"}, timeout=45, allow_redirects=True)
        if link_check.status_code != 200:
            raise RuntimeError(f"Updated article permalink did not return HTTP 200: {link_check.status_code}")
        save_result(registry, pid, "treated", title=title, slug=saved.get("slug", ""), link=saved.get("link", permalink), books_isbn=[b["isbn"] for b in verified], book_titles=[b["title_ar"] for b in verified], book_count=len(verified), books=[{k: b.get(k) for k in ("verified_title", "verified_author", "title_ar", "author", "author_ar", "summary_ar", "kind_ar", "isbn", "publisher", "year", "amazon_url", "amazon_title", "amazon_http", "amazon_validation_marketplace", "openlibrary_record")} for b in verified], cinema_video=registry.get(pid, {}).get("cinema_video", {"status": "unmatched", "id": None, "title": None}), modified=saved.get("modified"), article_http=link_check.status_code, schema_org_status="published", schema_book_nodes=len(verified), list_exhaustive=bool(picks.get("is_book_list")))
        print("ARTICLE_UPDATED", json.dumps({"id": pid, "link": saved.get("link"), "book_count": len(verified), "http": link_check.status_code}, ensure_ascii=False), flush=True)
        return True
    except Exception as e:
        reason = f"{type(e).__name__}: {str(e)[:500]}"
        fields = {
            "title": title,
            "link": permalink,
            "last_error": reason,
            "partial_book_isbns": [b.get("isbn") for b in verified if b.get("isbn")],
            "partial_books": [{k: b.get(k) for k in ("verified_title", "verified_author", "isbn", "amazon_url", "amazon_title", "amazon_http", "amazon_validation_marketplace")} for b in verified],
        }
        save_result(registry, pid, "pending", **fields)
        print("ARTICLE_PENDING", json.dumps({"id": pid, "title": title, "reason": reason}, ensure_ascii=False), flush=True)
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Process at most N pending articles (0 = all)")
    ap.add_argument("--dry-run", action="store_true", help="Research and verify; do not publish or checkpoint success")
    ap.add_argument("--pause", type=float, default=1.5, help="Seconds to sleep between articles")
    ap.add_argument("--retry-failed", action="store_true", help="Retry entries previously marked pending with last_error")
    ap.add_argument("--quick", action="store_true", help="Use one candidate edition and one Amazon attempt per marketplace; skip unresolved books immediately")
    ap.add_argument("--post-ids", default="", help="Comma-separated WordPress post IDs to process exclusively (maximum four)")
    args = ap.parse_args()
    if args.pause < 1 or args.pause > 10:
        ap.error("--pause must be from 1 to 10 seconds")
    requested_ids = [part.strip() for part in args.post_ids.split(",") if part.strip()]
    if len(requested_ids) > 4 or len(set(requested_ids)) != len(requested_ids):
        ap.error("--post-ids accepts at most four unique IDs")
    s = api_session()
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8")) if REGISTRY_PATH.exists() else {}
    posts = fetch_published(s)
    update_registry_from_posts(registry, posts)
    pending = []
    for post in posts:
        pid = str(post["id"])
        raw = (post.get("content") or {}).get("raw", "")
        if has_shelf(raw):
            continue
        item = registry.get(pid, {})
        if item.get("status") != "pending":
            continue
        if item.get("last_error") and not args.retry_failed:
            continue
        pending.append(post)
    if requested_ids:
        pending_by_id = {str(post["id"]): post for post in pending}
        missing_ids = [pid for pid in requested_ids if pid not in pending_by_id]
        if missing_ids:
            ap.error("requested IDs are not currently pending: " + ",".join(missing_ids))
        pending = [pending_by_id[pid] for pid in requested_ids]
    if args.limit:
        pending = pending[:args.limit]
    print("RUN_START", json.dumps({"published_posts": len(posts), "already_treated": len(posts)-sum(1 for p in posts if not has_shelf((p.get('content') or {}).get('raw',''))), "pending_to_process": len(pending), "dry_run": args.dry_run}, ensure_ascii=False), flush=True)
    success = fail = 0
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(locale="en-US", viewport={"width": 1440, "height": 900})
        page = context.new_page()
        for i, post in enumerate(pending):
            if process_one(s, page, registry, post, args.dry_run, quick=args.quick):
                success += 1
            else:
                fail += 1
            if i + 1 < len(pending):
                time.sleep(args.pause)
        context.close()
        browser.close()
    print("RUN_END", json.dumps({"attempted": len(pending), "ready_or_updated": success, "pending_or_failed": fail, "registry": str(REGISTRY_PATH)}, ensure_ascii=False), flush=True)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
