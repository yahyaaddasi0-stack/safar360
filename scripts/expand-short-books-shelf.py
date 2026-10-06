#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace the short-novels article's two-book shelf with its complete 8-title list.

Usage: python3 scripts/expand-short-books-shelf.py [--dry-run]
WordPress credentials are read only from SARD360_WP_USERNAME and
SARD360_WP_APPLICATION_PASSWORD environment variables.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

WP_BASE = "https://sard360.com/wp-json/wp/v2"
POST_ID = 4820
SHELF_ID = "sard360-short-books-shelf"
REGISTRY_PATH = Path(__file__).with_name("articles_registry.json")

# All eight titles follow the actual numbered list in the article.
# These Amazon product pages and cover URLs were opened and checked in Chromium.
BOOKS = [
    {
        "title": "موت إيفان إيليتش وقصص أخرى",
        "original": "The Death of Ivan Ilyich and Other Stories",
        "author_ar": "ليو تولستوي",
        "author_en": "Leo Tolstoy",
        "isbn": "0140449612",
        "kind": "كلاسيكية روسية",
        "summary": "رواية مكثفة تواجه القارئ بسؤال المعنى حين يكتشف قاضٍ على فراش الموت أن حياته لم تكن كما ظن.",
    },
    {
        "title": "الغريب",
        "original": "The Stranger",
        "author_ar": "ألبير كامو",
        "author_en": "Albert Camus",
        "isbn": "0679720200",
        "kind": "أدب وفلسفة",
        "summary": "رواية العبث الشهيرة؛ محاكمة ميرسو تكشف صدام الفرد مع أعراف المجتمع وصمته أمام كون لا يفسّر نفسه.",
    },
    {
        "title": "الشيخ والبحر",
        "original": "The Old Man and the Sea",
        "author_ar": "إرنست همنغواي",
        "author_en": "Ernest Hemingway",
        "isbn": "0684801221",
        "kind": "أدب خالد",
        "summary": "حكاية الصياد سانتياغو في مواجهة البحر، وتأمل أدبي في الكرامة والصبر وحدود الهزيمة.",
    },
    {
        "title": "المسخ",
        "original": "The Metamorphosis",
        "author_ar": "فرانتس كافكا",
        "author_en": "Franz Kafka",
        "isbn": "0553213695",
        "kind": "كلاسيكية حداثية",
        "summary": "استيقاظ غريغور سامسا إلى تحوّل مستحيل يفتح باباً لقراءة الاغتراب والمنفعة والروابط الأسرية.",
    },
    {
        "title": "رسائل من تحت الأرض",
        "original": "Notes from Underground",
        "author_ar": "فيودور دوستويفسكي",
        "author_en": "Fyodor Dostoevsky",
        "isbn": "067973452X",
        "kind": "رواية نفسية",
        "summary": "صوت رجل القبو الساخر يفكك الثقة بالعقلانية المطلقة ويكشف تناقضات الإرادة الإنسانية.",
    },
    {
        "title": "مزرعة الحيوان",
        "original": "Animal Farm",
        "author_ar": "جورج أورويل",
        "author_en": "George Orwell",
        "isbn": "0451526341",
        "kind": "رواية رمزية",
        "summary": "حكاية سياسية موجزة عن الثورة والسلطة وكيف يمكن للشعارات المساواتية أن تنقلب إلى استبداد.",
    },
    {
        "title": "الأمير الصغير",
        "original": "The Little Prince",
        "author_ar": "أنطوان دو سانت إكزوبيري",
        "author_en": "Antoine de Saint-Exupéry",
        "isbn": "0156012197",
        "kind": "حكاية فلسفية",
        "summary": "رحلة الأمير بين الكواكب تعيد النظر في الحب والصداقة، وفي ما يغفله عالم الكبار المنشغل بالأرقام.",
    },
    {
        "title": "قصة موت معلن",
        "original": "Chronicle of a Death Foretold",
        "author_ar": "غابرييل غارسيا ماركيز",
        "author_en": "Gabriel García Márquez",
        "isbn": "140003471X",
        "kind": "رواية لاتينية",
        "summary": "جريمة يعرف الجميع أنها ستقع؛ تحقيق روائي في الشرف والتواطؤ والقدر الذي يصنعه مجتمع كامل.",
    },
]


def amazon_url(isbn: str) -> str:
    return f"https://www.amazon.com/dp/{isbn}?tag=sard360-20"


def image_url(isbn: str) -> str:
    return f"https://images-na.ssl-images-amazon.com/images/P/{isbn}.01.LZZZZZZZ.jpg"


def style_block() -> str:
    return """<style id="sard360-short-books-shelf-styles">
#sard360-short-books-shelf,#sard360-short-books-shelf *{box-sizing:border-box}
#sard360-short-books-shelf{background:#080505;color:#f5efe2;border:1px solid rgba(212,163,89,.55);border-radius:18px;padding:26px 22px;margin:26px 0 42px;box-shadow:0 18px 45px rgba(0,0,0,.3);font-family:inherit;text-align:right;direction:rtl}
#sard360-short-books-shelf .sard-shelf-eyebrow{margin:0 0 8px!important;color:#d4a359;font-size:12px;letter-spacing:.06em;line-height:1.6}
#sard360-short-books-shelf .sard-shelf-title{margin:0 0 20px!important;padding:0!important;border:0!important;background:none!important;color:#f3ead8;font-size:clamp(22px,3vw,30px)!important;line-height:1.55!important;text-align:right}
#sard360-short-books-shelf .sard-book-grid{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;align-items:stretch;gap:16px}
#sard360-short-books-shelf .sard-book-card{display:flex!important;flex-direction:column!important;align-items:stretch;min-width:0;height:auto!important;min-height:100%!important;max-height:none!important;overflow:visible!important;padding:16px 14px;background:#12151b;border:1px solid rgba(212,163,89,.32);border-radius:14px;box-shadow:0 12px 30px rgba(0,0,0,.26);transition:border-color .2s ease,transform .2s ease}
#sard360-short-books-shelf .sard-book-card:hover{transform:translateY(-2px);border-color:rgba(212,163,89,.72)}
#sard360-short-books-shelf .sard-book-cover-wrap{display:flex;align-items:center;justify-content:center;width:100%;height:154px;margin:0 0 12px;overflow:hidden}
#sard360-short-books-shelf img.sard-book-cover{display:block!important;width:auto!important;max-width:104px!important;height:150px!important;max-height:150px!important;object-fit:contain!important;border:1px solid rgba(212,163,89,.58);border-radius:7px;box-shadow:0 8px 20px rgba(0,0,0,.4)}
#sard360-short-books-shelf .sard-book-kind{margin:0 0 5px!important;color:#d4a359;font-size:11px;line-height:1.5;text-align:center}
#sard360-short-books-shelf .sard-book-title{display:block!important;margin:0 0 5px!important;padding:0!important;border:0!important;background:none!important;color:#f3ead8;font-size:16px!important;line-height:1.5!important;text-align:center;overflow-wrap:anywhere}
#sard360-short-books-shelf .sard-book-original{margin:0 0 5px!important;color:#d8c7a4;font-size:11px;line-height:1.4;text-align:center;direction:ltr;overflow-wrap:anywhere}
#sard360-short-books-shelf .sard-book-author{margin:0 0 9px!important;color:#bdb5a8;font-size:12px;line-height:1.5;text-align:center;overflow-wrap:anywhere}
#sard360-short-books-shelf .sard-book-summary{flex:1 1 auto;display:block!important;height:auto!important;max-height:none!important;overflow:visible!important;margin:0 0 14px!important;color:#ded7cb;font-size:12px;line-height:1.75;text-align:center;overflow-wrap:anywhere;-webkit-line-clamp:unset!important}
#sard360-short-books-shelf .sard-book-cta{display:inline-flex!important;position:static!important;visibility:visible!important;opacity:1!important;align-items:center;justify-content:center;align-self:center;flex:0 0 auto;margin-top:auto!important;min-width:130px;min-height:40px;padding:9px 13px;border:0;border-radius:999px;background:linear-gradient(135deg,#e6c66d,#c99a3a);box-shadow:0 8px 22px rgba(212,163,89,.2);color:#16130d!important;text-decoration:none!important;text-align:center;font-family:inherit;font-size:12px;font-weight:800;line-height:1.4;white-space:normal;transition:filter .2s ease,transform .2s ease}
#sard360-short-books-shelf .sard-book-cta:hover,#sard360-short-books-shelf .sard-book-cta:focus-visible{filter:brightness(1.08);transform:translateY(-1px)}
#sard360-short-books-shelf .sard-affiliate-disclosure{display:block;width:100%;max-width:76ch;margin:18px auto 0!important;padding:12px 0 0!important;border-top:1px solid rgba(255,255,255,.08);color:#888!important;font-size:11px!important;text-align:center!important;direction:rtl;line-height:1.5!important;text-wrap:pretty;overflow-wrap:normal}
@media(max-width:1100px){#sard360-short-books-shelf .sard-book-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:14px}}
@media(max-width:560px){#sard360-short-books-shelf{padding:20px 14px}#sard360-short-books-shelf .sard-book-grid{grid-template-columns:1fr!important;gap:13px}#sard360-short-books-shelf .sard-book-card{display:grid!important;grid-template-columns:84px minmax(0,1fr);grid-template-rows:auto auto auto 1fr auto;column-gap:12px;align-items:start;padding:13px;text-align:right}#sard360-short-books-shelf .sard-book-cover-wrap{grid-column:1;grid-row:1 / span 5;width:84px;height:122px;margin:0;align-self:start}#sard360-short-books-shelf img.sard-book-cover{max-width:80px!important;height:118px!important;max-height:118px!important}#sard360-short-books-shelf .sard-book-kind,#sard360-short-books-shelf .sard-book-title,#sard360-short-books-shelf .sard-book-original,#sard360-short-books-shelf .sard-book-author,#sard360-short-books-shelf .sard-book-summary,#sard360-short-books-shelf .sard-book-cta{grid-column:2;text-align:right}#sard360-short-books-shelf .sard-book-kind{grid-row:1}#sard360-short-books-shelf .sard-book-title{grid-row:2;font-size:16px!important}#sard360-short-books-shelf .sard-book-original{grid-row:3;text-align:left}#sard360-short-books-shelf .sard-book-author{grid-row:4}#sard360-short-books-shelf .sard-book-summary{grid-row:5;margin-bottom:10px!important}#sard360-short-books-shelf .sard-book-cta{grid-row:6;justify-self:start;min-height:36px;padding:8px 12px}}
@media(max-width:360px){#sard360-short-books-shelf .sard-book-card{grid-template-columns:70px minmax(0,1fr);column-gap:9px}#sard360-short-books-shelf .sard-book-cover-wrap{width:70px;height:108px}#sard360-short-books-shelf img.sard-book-cover{max-width:66px!important;height:104px!important;max-height:104px!important}}
</style>"""


def section_block() -> str:
    cards = []
    for i, book in enumerate(BOOKS, 1):
        url = amazon_url(book["isbn"])
        cards.append(f'''    <article class="sard-book-card">
      <div class="sard-book-cover-wrap"><img class="sard-book-cover" src="{image_url(book['isbn'])}" alt="غلاف {html.escape(book['title'])}" loading="lazy" decoding="async"></div>
      <p class="sard-book-kind">{html.escape(book['kind'])} · {i:02d}</p>
      <h3 class="sard-book-title">{html.escape(book['title'])}</h3>
      <p class="sard-book-original" lang="en" dir="ltr">{html.escape(book['original'])}</p>
      <p class="sard-book-author">{html.escape(book['author_ar'])} <span lang="en" dir="ltr">· {html.escape(book['author_en'])}</span></p>
      <p class="sard-book-summary">{html.escape(book['summary'])}</p>
      <a class="sard-book-cta" href="{url}" target="_blank" rel="sponsored nofollow noopener">اكتشف الكتاب</a>
    </article>''')
    return f'''<section id="{SHELF_ID}" aria-label="مقتنيات ومراجع الروايات القصيرة">
  <p class="sard-shelf-eyebrow">الخزانة · سرد 360 · 8 أعمال مختارة</p>
  <h2 class="sard-shelf-title">لمواصلة التقصّي: ثماني روايات قصيرة تعيد النظر في معنى الحياة</h2>
  <div class="sard-book-grid">
{chr(10).join(cards)}
  </div>
  <p class="sard-affiliate-disclosure">إفصاح: تحتوي هذه الترشيحات على روابط Amazon تابعة؛ قد تحصل منصّة سرد 360 على عمولة بسيطة عند الشراء من خلال هذه الروابط دون أي كلفة إضافية عليك. هذه الاختيارات تتبع معاييرنا الثقافية لخدمة القارئ.</p>
</section>'''


def build_shelf_fragment() -> str:
    return style_block() + "\n" + section_block()


def get_raw(post: dict) -> str:
    return (post.get("content") or {}).get("raw", "")


def update_post(session: requests.Session, dry_run: bool) -> dict:
    r = session.get(f"{WP_BASE}/posts/{POST_ID}", params={"context": "edit"}, timeout=40)
    r.raise_for_status()
    post = r.json()
    if post.get("status") != "publish":
        raise RuntimeError(f"Post {POST_ID} is not published")
    raw = get_raw(post)
    pattern = re.compile(rf'(?is)<style id="{re.escape(SHELF_ID)}-styles">.*?</style>\s*<section id="{re.escape(SHELF_ID)}".*?</section>')
    matches = list(pattern.finditer(raw))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one existing shelf, found {len(matches)}; refusing to modify post")
    updated = pattern.sub(lambda _: build_shelf_fragment(), raw, count=1)
    if updated == raw:
        raise RuntimeError("Replacement did not change content")
    if updated.count(f'id="{SHELF_ID}"') != 1:
        raise RuntimeError("New content does not contain exactly one shelf")
    if dry_run:
        print("DRY_RUN", json.dumps({"id": post["id"], "link": post["link"], "title": post["title"].get("raw"), "book_count": len(BOOKS), "content_length_before": len(raw), "content_length_after": len(updated)}, ensure_ascii=False))
    else:
        result = session.post(f"{WP_BASE}/posts/{POST_ID}", json={"content": updated}, timeout=60)
        result.raise_for_status()
        saved = result.json()
        print("UPDATED", json.dumps({"id": saved["id"], "link": saved["link"], "modified": saved.get("modified"), "book_count": len(BOOKS)}, ensure_ascii=False))
    return post


def walk_shelves(content: str) -> tuple[bool, list[str], list[str]]:
    shelf_pattern = re.compile(r'(?is)<section id="sard360-[^"]+-shelf".*?</section>')
    shelves = shelf_pattern.findall(content or "")
    is_treated = bool(shelves)
    isbns: list[str] = []
    titles: list[str] = []
    for shelf in shelves:
        for isbn in re.findall(r'/dp/([A-Z0-9]{10})(?:\?tag=sard360-20)?', shelf, re.I):
            if isbn not in isbns:
                isbns.append(isbn)
        for title in re.findall(r'<h3\b[^>]*>(.*?)</h3>', shelf, re.I | re.S):
            value = re.sub(r'<[^>]+>', '', title)
            value = html.unescape(re.sub(r'\s+', ' ', value)).strip()
            if value:
                titles.append(value)
    return is_treated, isbns, titles


def fetch_all_published(session: requests.Session) -> list[dict]:
    posts: list[dict] = []
    page = 1
    while True:
        r = session.get(f"{WP_BASE}/posts", params={"context": "edit", "status": "publish", "per_page": 100, "page": page}, timeout=45)
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


def regenerate_registry(session: requests.Session) -> None:
    old = {}
    if REGISTRY_PATH.exists():
        old = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    cinema_path = Path(__file__).resolve().parents[1] / "cinema.json"
    try:
        cinema = json.loads(cinema_path.read_text(encoding="utf-8"))
        video_items = cinema.get("items", [])
    except Exception:
        video_items = []

    fresh = {}
    for post in fetch_all_published(session):
        pid = str(post["id"])
        previous = old.get(pid, {})
        title_obj = post.get("title") or {}
        title = html.unescape(title_obj.get("raw") or title_obj.get("rendered") or "")
        content = get_raw(post) or (post.get("content") or {}).get("rendered", "")
        treated, isbns, book_titles = walk_shelves(content)
        # A match is asserted only when the article embeds a catalogued YouTube
        # ID. Similarity between unrelated titles is not strong enough evidence.
        matched = [
            item for item in video_items
            if item.get("youtube_id") and str(item["youtube_id"]) in content
        ]
        video = {"status": "matched", "id": matched[0].get("id"), "title": matched[0].get("title")} if len(matched) == 1 else {"status": "unmatched", "id": None, "title": None}
        fresh[pid] = {
            "title": title,
            "slug": post.get("slug", ""),
            "link": post.get("link", ""),
            "status": "treated" if treated else "pending",
            "books_isbn": isbns if treated else previous.get("books_isbn", []),
            "book_titles": book_titles if treated else previous.get("book_titles", []),
            "book_count": len(isbns) if treated else len(previous.get("books_isbn", [])),
            "cinema_video": video,
            "modified": post.get("modified", ""),
        }
    REGISTRY_PATH.write_text(json.dumps(fresh, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("REGISTRY_REBUILT", json.dumps({"published_posts": len(fresh), "treated": sum(v['status']=='treated' for v in fresh.values()), "pending": sum(v['status']=='pending' for v in fresh.values()), "article_4820_books": fresh.get(str(POST_ID), {}).get("book_count")}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--registry-only", action="store_true", help="Rebuild the registry without updating the WordPress article")
    args = parser.parse_args()
    username = os.environ.get("SARD360_WP_USERNAME")
    password = os.environ.get("SARD360_WP_APPLICATION_PASSWORD")
    if not username or not password:
        raise SystemExit("WordPress credentials are not available in environment")
    if len(BOOKS) != 8 or len({b['isbn'] for b in BOOKS}) != 8:
        raise SystemExit("Expected eight unique works")
    for book in BOOKS:
        if "tag=sard360-20" not in amazon_url(book["isbn"]):
            raise SystemExit("Amazon affiliate tag missing")

    session = requests.Session()
    session.auth = (username, password)
    session.headers.update({"Accept": "application/json", "User-Agent": "Sard360-MicroKhizana/1.0"})
    if args.registry_only:
        regenerate_registry(session)
        return
    post = update_post(session, args.dry_run)
    if not args.dry_run:
        # Verify the official permalink and the public article after the write.
        public = requests.get(post["link"], headers={"User-Agent": "Mozilla/5.0"}, timeout=40, allow_redirects=True)
        public.raise_for_status()
        print("PUBLIC_ARTICLE", json.dumps({"url": post["link"], "http": public.status_code, "final_url": public.url}, ensure_ascii=False))
        regenerate_registry(session)


if __name__ == "__main__":
    main()
