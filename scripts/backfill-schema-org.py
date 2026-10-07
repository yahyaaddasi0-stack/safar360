#!/usr/bin/env python3
"""Idempotent Schema.org backfill for Sard360 WordPress posts and catalog pages.

Run with --dry-run first. --apply updates only the 35 post IDs in the tracked
registry, the Khizana page, and the Cinema page. Registry checkpoints are
written atomically after every post update.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "scripts/articles_registry.json"
PRODUCTS_PATH = ROOT / "products.json"
CINEMA_PATH = ROOT / "cinema.json"
EMBED_PATH = ROOT / "cinema-wordpress-embed.html"
WP_BASE = "https://sard360.com/wp-json/wp/v2"
AFFILIATE_TAG = "sard360-20"
TARGETS: dict[int, list[dict[str, str]]] = {
    4406: [
        {
            "title_ar": "الحشّاشون: طائفة راديكالية في الإسلام",
            "original": "The Assassins: A Radical Sect in Islam",
            "author_ar": "برنارد لويس",
            "author_en": "Bernard Lewis",
            "isbn": "0465004989",
            "kind": "دراسة تاريخية مرجعية",
            "summary": "دراسة برنارد لويس الكلاسيكية تتتبّع الإسماعيلية النزارية وتاريخ الجماعة في إيران وسورية؛ تُقرأ بوصفها مدخلاً مؤثراً مع موازنتها بالأبحاث الأحدث حول ألموت.",
        },
        {
            "title_ar": "ألموت",
            "original": "Alamut",
            "author_ar": "فلاديمير بارتول · ترجمة مايكل بيغينز",
            "author_en": "Vladimir Bartol · translated by Michael Biggins",
            "isbn": "0972028730",
            "kind": "الرواية الأصلية",
            "summary": "رواية بارتول التي أعادت تخييل قلعة ألموت وحسن الصباح في عمل أدبي عن السلطة والإيمان وصناعة الأسطورة؛ رواية تاريخية لا تُعامل بوصفها مصدراً توثيقياً.",
        },
    ],
    4391: [
        {
            "title_ar": "الفوضى: نشوء علم جديد",
            "original": "Chaos: Making a New Science",
            "author_ar": "جيمس غليك",
            "author_en": "James Gleick",
            "isbn": "0140092501",
            "kind": "تاريخ علمي موثّق",
            "summary": "سرد صحفي موثّق لنشأة علم الفوضى وللأفكار التي غيّرت فهم الأنظمة الحسّاسة للشروط الابتدائية؛ مدخل واضح إلى الخلفية العلمية لأثر الفراشة.",
        },
        {
            "title_ar": "جوهر الفوضى",
            "original": "The Essence of Chaos",
            "author_ar": "إدوارد لورنز",
            "author_en": "Edward N. Lorenz",
            "isbn": "0295975148",
            "kind": "شهادة المؤسّس العلمي",
            "summary": "عرض إدوارد لورنز لمفاهيم الفوضى من منظور العالم الذي أسهم في تأسيسها، مع أمثلة تشرح التنبؤ وحدوده في الأنظمة الطبيعية.",
        },
    ],
    4397: [
        {
            "title_ar": "الدم والإيمان: تطهير إسبانيا المسلمة",
            "original": "Blood and Faith: The Purging of Muslim Spain, 1492–1614",
            "author_ar": "ماثيو كار",
            "author_en": "Matthew Carr",
            "isbn": "1849048010",
            "kind": "دراسة تاريخية حديثة",
            "summary": "دراسة حديثة عن التحوّل القسري والاضطهاد والطرد في إسبانيا، تضع تجربة الموريسكيين في سياق سياسي واجتماعي أوسع.",
        },
        {
            "title_ar": "الموريسكيون في إسبانيا: تنصيرهم وطردهم",
            "original": "The Moriscos of Spain: Their Conversion and Expulsion",
            "author_ar": "هنري تشارلز ليا",
            "author_en": "Henry Charles Lea",
            "isbn": "0766188663",
            "kind": "مرجع تاريخي كلاسيكي · يُقرأ نقدياً",
            "summary": "عمل تاريخي كلاسيكي من مطلع القرن العشرين يعرض مسار التنصير والطرد؛ يُستفاد منه مع قراءة نقدية وبمقارنته بدراسة ماثيو كار الأحدث، لا بوصفه آخر ما توصّل إليه البحث.",
        },
    ],
    4666: [
        {
            "title_ar": "البتراء والمملكة النبطية المفقودة",
            "original": "Petra and the Lost Kingdom of the Nabataeans",
            "author_ar": "جين تايلور",
            "author_en": "Jane Taylor",
            "isbn": "0674008499",
            "kind": "مرجع تاريخي وأثري",
            "summary": "مدخل مصوّر إلى تاريخ البتراء والأنباط وموقع المدينة في طرق التجارة القديمة؛ يوسّع سياق هندسة المياه والعمارة التي يتناولها المقال.",
        },
        {
            "title_ar": "الأنباط: بنّاؤو البتراء",
            "original": "The Nabataeans: Builders of Petra",
            "author_ar": "دان غيبسون",
            "author_en": "Dan Gibson",
            "isbn": "1413427340",
            "kind": "قراءة مكمّلة · إصدار مستقل",
            "summary": "كتاب مستقل يقدّم قراءة مصوّرة للأنباط والبتراء. ناشره Xlibris للنشر الذاتي؛ ندرجه بوصفه منظوراً مكمّلاً لا مرجعاً أكاديمياً مساوياً لكتاب جين تايلور.",
        },
    ],
    4560: [
        {
            "title_ar": "الكندي",
            "original": "Al-Kindi",
            "author_ar": "بيتر آدمسون",
            "author_en": "Peter Adamson",
            "isbn": "0195181433",
            "kind": "دراسة فلسفية أكاديمية",
            "summary": "دراسة أكاديمية من سلسلة Great Medieval Thinkers ترسم مشروع الكندي الفلسفي وصلاته بالعلوم اليونانية وبدايات الفلسفة في العالم الإسلامي.",
        },
        {
            "title_ar": "الأعمال الفلسفية للكندي",
            "original": "The Philosophical Works of al-Kindi",
            "author_ar": "تحرير بيتر إي. بورمان وبيتر آدمسون",
            "author_en": "Edited by Peter E. Pormann and Peter Adamson",
            "isbn": "0199062803",
            "kind": "نصوص فلسفية محقّقة ومترجمة",
            "summary": "مجموعة أكاديمية من نصوص الكندي مع ترجمة ودراسة؛ إصدار متخصص قد يظهر على Amazon في نسخ مستعملة أو بأسعار مقتنين، لذا تحقّق من حالة النسخة قبل الشراء.",
        },
    ],
    4546: [
        {
            "title_ar": "أتلانتس الرمال: البحث عن مدينة أوبار المفقودة",
            "original": "Atlantis of the Sands: The Search for the Lost City of Ubar",
            "author_ar": "رَنُلف فاينز",
            "author_en": "Ranulph Fiennes",
            "isbn": "0747513279",
            "kind": "تحقيق استكشافي",
            "summary": "رواية استكشاف وبحث أثري عن أوبار، تمزج سجل الرحلات بالجدل حول تحديد موقع المدينة المفقودة في جنوب الجزيرة العربية.",
        },
        {
            "title_ar": "الطريق إلى أوبار: العثور على أتلانتس الرمال",
            "original": "The Road to Ubar: Finding the Atlantis of the Sands",
            "author_ar": "نيكولاس كلاب",
            "author_en": "Nicholas Clapp",
            "isbn": "0395957869",
            "kind": "سرد ميداني في الآثار والاستكشاف",
            "summary": "يتابع نيكولاس كلاب مسار البحث الميداني عن أوبار، من الخرائط والنصوص القديمة إلى الاستشعار عن بُعد والبعثات الصحراوية.",
        },
    ],
    4407: [
        {
            "title_ar": "ابن فضلان وأرض الظلمات",
            "original": "Ibn Fadlan and the Land of Darkness: Arab Travellers in the Far North",
            "author_ar": "أحمد بن فضلان · ترجمة بول لوند وكارولاين ستون",
            "author_en": "Ahmad ibn Fadlan · translated by Paul Lunde and Caroline Stone",
            "isbn": "0140455078",
            "kind": "مصدر أولي مترجم · Penguin Classics",
            "summary": "مختارات مترجمة من روايات الرحّالة العرب في الشمال، وفي مركزها وصف ابن فضلان للروس وطقوسهم؛ شهادة تاريخية تُقرأ في سياقها النصّي.",
        },
        {
            "title_ar": "مهمّة إلى نهر الفولغا",
            "original": "Mission to the Volga",
            "author_ar": "أحمد بن فضلان · تحرير وترجمة جيمس إي. مونتغمري",
            "author_en": "Ahmad ibn Fadlan · edited and translated by James E. Montgomery",
            "isbn": "1479899895",
            "kind": "مصدر أولي محقّق · مكتبة الأدب العربي",
            "summary": "طبعة علمية لنص ابن فضلان ضمن Library of Arabic Literature، تجمع النص العربي والترجمة الإنجليزية ومقدّمة نقدية، وتتيح العودة إلى الشهادة الأصلية.",
        },
    ],
}


def safe_json(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def tagged_url(raw: str) -> str:
    parts = urlsplit(raw.strip())
    if parts.scheme != "https" or not parts.netloc:
        raise ValueError(f"Non-HTTPS offer URL: {raw}")
    host = parts.hostname.lower() if parts.hostname else ""
    if host == "amzn.to" or re.search(r"(^|\.)amazon\.[a-z.]+$", host):
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query["tag"] = AFFILIATE_TAG
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    raise ValueError(f"Non-Amazon offer URL: {raw}")


def is_isbn(value: str) -> bool:
    s = re.sub(r"[^0-9Xx]", "", value).upper()
    if len(s) == 10:
        return sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(s)) % 11 == 0
    if len(s) == 13 and s.isdigit():
        total = sum((1 if i % 2 == 0 else 3) * int(c) for i, c in enumerate(s[:12]))
        return (10 - total % 10) % 10 == int(s[-1])
    return False


def get_session() -> requests.Session:
    username = os.environ.get("SARD360_WP_USERNAME", "")
    password = os.environ.get("SARD360_WP_APPLICATION_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("WordPress application credentials are not configured in the environment.")
    s = requests.Session()
    s.auth = (username, password)
    s.headers.update({"User-Agent": "Sard360-SchemaOrg/1.0", "Accept": "application/json"})
    return s


def api_get(session: requests.Session, path: str, params: dict | None = None) -> dict | list:
    last_error = None
    for attempt in range(3):
        try:
            r = session.get(f"{WP_BASE}{path}", params=params, timeout=(12, 35))
            if r.status_code >= 500 and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            raise
    raise last_error or RuntimeError(f"WordPress GET failed: {path}")


def api_update_post(session: requests.Session, post_id: int, content: str) -> dict:
    r = session.post(f"{WP_BASE}/posts/{post_id}", json={"content": content}, timeout=90)
    r.raise_for_status()
    result = r.json()
    if int(result.get("id", -1)) != post_id:
        raise RuntimeError(f"WordPress returned an unexpected post ID after updating {post_id}.")
    return result


def api_update_page(session: requests.Session, page_id: int, content: str) -> dict:
    r = session.post(f"{WP_BASE}/pages/{page_id}", json={"content": content}, timeout=120)
    r.raise_for_status()
    result = r.json()
    if int(result.get("id", -1)) != page_id:
        raise RuntimeError(f"WordPress returned an unexpected page ID after updating {page_id}.")
    return result


class BookCardParser(HTMLParser):
    FIELDS = {
        "kh-kind": "kind", "sard-book-kind": "kind",
        "kh-title": "alt_name", "kh-original": "name",
        "kh-author": "author", "sard-book-author": "author",
        "kh-summary": "description", "sard-book-summary": "description",
        "kh-cta": "url", "sard-book-cta": "url",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[dict] = []
        self.card: dict | None = None
        self.tag_stack: list[str] = []
        self.capture_stack: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = dict(attrs)
        classes = set((attrs_d.get("class") or "").split())
        if tag == "article" and ("kh-book-card" in classes or "sard-book-card" in classes):
            self.card = {"name": "", "alt_name": "", "author": "", "description": "", "kind": "", "url": "", "image": "", "target": "", "rel": "", "isbn": attrs_d.get("data-isbn", "") or ""}
        cap = next((self.FIELDS[c] for c in classes if c in self.FIELDS), None)
        if self.card is not None and tag == "h3" and cap is None:
            cap = "alt_name"
        if self.card is not None and tag == "img" and not self.card["image"]:
            self.card["image"] = attrs_d.get("src", "") or ""
        if self.card is not None and tag == "a" and ("kh-cta" in classes or "sard-book-cta" in classes):
            self.card["url"] = attrs_d.get("href", "") or ""
            self.card["target"] = attrs_d.get("target", "") or ""
            self.card["rel"] = attrs_d.get("rel", "") or ""
        self.tag_stack.append(tag)
        self.capture_stack.append(cap)

    def handle_endtag(self, tag: str) -> None:
        if self.card is not None and tag == "article" and "article" in self.tag_stack:
            self.cards.append(self.card)
            self.card = None
        if self.tag_stack:
            self.tag_stack.pop()
        if self.capture_stack:
            self.capture_stack.pop()

    def handle_data(self, data: str) -> None:
        if self.card is None:
            return
        field = next((name for name in reversed(self.capture_stack) if name), None)
        if field:
            self.card[field] += data


def extract_cards(content: str) -> list[dict]:
    parser = BookCardParser()
    parser.feed(content)
    result = []
    for card in parser.cards:
        card = {k: html.unescape(str(v)).strip() for k, v in card.items()}
        try:
            card["url"] = tagged_url(card["url"])
        except Exception:
            continue
        match = re.search(r"/dp/([A-Z0-9]{10,13})", card["url"], re.I)
        card["asin"] = match.group(1).upper() if match else ""
        # An Amazon ASIN can be a 10-character code that happens to pass the
        # ISBN checksum while referring to a different product. Only use an
        # explicit, verified data-isbn value on the visible card.
        card["isbn"] = re.sub(r"[^0-9Xx]", "", card.get("isbn", "")).upper()
        if not is_isbn(card["isbn"]):
            card["isbn"] = ""
        author = card.get("author", "")
        # Existing Sard360 cards display Arabic and Latin names separated by a middle dot.
        if "·" in author:
            author = author.split("·")[-1].strip()
        elif re.search(r"[A-Za-z]", author):
            latin = re.search(r"[A-Za-z][A-Za-z .,'’()-]*$", author)
            if latin:
                author = latin.group(0).strip()
        card["author_name"] = author
        result.append(card)
    return result


def book_node(card: dict, post_link: str, index: int, post_id: int, anchor_id: str) -> dict:
    name = card.get("name") or card.get("alt_name") or ""
    node = {
        "@type": "Book",
        "@id": f"{post_link}#khizana-book-{post_id}-{index}",
        "name": name,
        "url": f"{post_link}#{anchor_id}",
    }
    if not card.get("schema_offer_excluded"):
        node["offers"] = {"@type": "Offer", "url": tagged_url(card["url"])}
    alt = card.get("alt_name")
    if alt and alt != name:
        node["alternateName"] = alt
    if card.get("author_name"):
        node["author"] = {"@type": "Person", "name": card["author_name"]}
    if card.get("isbn"):
        node["isbn"] = card["isbn"]
    image = card.get("image", "")
    if image and "rare-books.jpg" not in image:
        node["image"] = image
    if card.get("description"):
        node["description"] = card["description"]
    return node


def schema_script(graph: list[dict], script_id: str) -> str:
    return f'<script type="application/ld+json" id="{html.escape(script_id, quote=True)}">{safe_json({"@context": "https://schema.org", "@graph": graph})}</script>'


def inline_schema(content: str, graph: list[dict], script_id: str) -> str:
    block = schema_script(graph, script_id)
    pat = re.compile(rf"""<script\b(?=[^>]*\bid=["']{re.escape(script_id)}["'])[^>]*>.*?</script>""", re.I | re.S)
    if pat.search(content):
        return pat.sub(lambda _: block, content, count=1)
    return content.rstrip() + f"\n\n<!-- wp:html -->\n{block}\n<!-- /wp:html -->\n"


def load_template_css(session: requests.Session) -> str:
    post = api_get(session, "/posts/4553", {"context": "edit"})
    raw = post["content"]["raw"]
    match = re.search(r"<style[^>]*>([\s\S]*?)</style>", raw, re.I)
    if not match:
        raise RuntimeError("Could not find the validated Micro-Khizana style in the template article.")
    return match.group(1).replace("#sard360-khizana-article-4553", "#sard360-khizana-article-__POST__")


def amazon_product_url(isbn: str) -> str:
    if not is_isbn(isbn):
        raise ValueError(f"Invalid ISBN supplied for an editorial book: {isbn}")
    return f"https://www.amazon.com/dp/{isbn}?tag={AFFILIATE_TAG}"


def verify_amazon_url(session: requests.Session, url: str, expected_title: str) -> dict:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if query.get("tag") != AFFILIATE_TAG or parts.hostname != "www.amazon.com":
        raise ValueError(f"Affiliate tag or Amazon host invalid: {url}")
    # The exact 14 Amazon product pages were checked through live product-page
    # extraction during editorial review. Repeat an HTTP GET here; hard-fail on
    # a real Not Found/410 response, but record transient Amazon bot/5xx limits.
    try:
        # Deliberately use a fresh unauthenticated request: the authenticated
        # WordPress session must never send its Basic Auth header to Amazon.
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36"}, timeout=10, allow_redirects=True)
        body = response.text[:350000].lower() if "text" in response.headers.get("content-type", "") else ""
        if response.status_code in (404, 410) or "we couldn't find that page" in body or "we could not find that page" in body:
            raise ValueError(f"Amazon product page returned not found: {url} (HTTP {response.status_code})")
        if response.status_code >= 500 or response.status_code in (403, 429):
            return {"url": url, "http": response.status_code, "result": "transient/robot response; editorial product page was independently verified"}
        return {"url": url, "http": response.status_code, "result": "reachable"}
    except requests.RequestException as exc:
        return {"url": url, "http": None, "result": f"network-inconclusive: {exc.__class__.__name__}; product page independently verified"}


def build_book_data(book: dict) -> dict:
    url = amazon_product_url(book["isbn"])
    return {
        **book,
        "url": url,
        "image": (f"https://covers.openlibrary.org/b/isbn/{book['isbn']}-M.jpg" if book["isbn"] == "0747513279" else f"https://images-na.ssl-images-amazon.com/images/P/{book['isbn']}.01.LZZZZZZZ.jpg"),
    }


def build_shelf(post_id: int, post_title: str, books: list[dict], template_css: str) -> str:
    shelf_id = f"sard360-khizana-article-{post_id}"
    css = template_css.replace("__POST__", str(post_id))
    cards = []
    for index, book in enumerate(books, 1):
        title_ar = html.escape(book["title_ar"])
        original = html.escape(book["original"])
        author_ar = html.escape(book["author_ar"])
        author_en = html.escape(book["author_en"])
        kind = html.escape(book["kind"])
        summary = html.escape(book["summary"])
        image = html.escape(book["image"], quote=True)
        url = html.escape(book["url"], quote=True)
        isbn = html.escape(book["isbn"], quote=True)
        cards.append(f'''<article class="kh-book-card" data-isbn="{isbn}">
  <div class="kh-cover"><img src="{image}" alt="غلاف {title_ar}" loading="lazy" decoding="async"></div>
  <p class="kh-kind">{kind} · {index:02d}</p>
  <h3 class="kh-title">{title_ar}</h3>
  <p class="kh-original" lang="en" dir="ltr">{original}</p>
  <p class="kh-author">{author_ar} <span lang="en" dir="ltr">· {author_en}</span></p>
  <p class="kh-summary">{summary}</p>
  <a class="kh-cta" href="{url}" target="_blank" rel="sponsored nofollow noopener">اكتشف الكتاب</a>
</article>''')
    head = html.escape(post_title)
    return f'''<style id="{shelf_id}-style">{css}</style>
<section id="{shelf_id}" aria-label="مراجع ومقتنيات من خزانة سرد" dir="rtl">
<p class="kh-eyebrow">الخزانة · سرد 360 · مرجعان مختاران</p>
<h2 class="kh-heading">مراجع ومقتنيات لمواصلة التقصّي: {head}</h2>
<div class="kh-grid">\n{''.join(cards)}\n</div>
<p class="kh-disclosure">إفصاح: تحتوي هذه الترشيحات على روابط Amazon تابعة؛ وقد تحصل سرد360 على عمولة دون تكلفة إضافية عليك.</p>
</section>'''


def insert_shelf(content: str, shelf: str) -> str:
    # Honor the established placement: before the second H3 when present;
    # otherwise before the second H2, after the opening section.
    h3 = list(re.finditer(r"<h3\b[^>]*>", content, re.I))
    matches = h3 if len(h3) >= 2 else list(re.finditer(r"<h2\b[^>]*>", content, re.I))
    if len(matches) >= 2:
        at = matches[1].start()
        # Include the Gutenberg heading-block opener where it immediately precedes the heading.
        prefix = content[:at]
        block = prefix.rfind("<!-- wp:heading")
        if block >= 0 and at - block < 250:
            at = block
        return content[:at] + f"<!-- wp:html -->\n{shelf}\n<!-- /wp:html -->\n\n" + content[at:]
    # If an unusual article has no usable headings, put the block after the first paragraph.
    p = re.search(r"</p>", content, re.I)
    at = p.end() if p else len(content)
    return content[:at] + f"\n<!-- wp:html -->\n{shelf}\n<!-- /wp:html -->\n" + content[at:]


def find_shelf(content: str, post_id: int) -> str:
    m = re.search(rf"""<section\b[^>]*id=["']sard360-khizana-article-{post_id}["'][\s\S]*?</section>""", content, re.I)
    if m:
        return m.group(0)
    for section in re.finditer(r"<section\b[^>]*>[\s\S]*?</section>", content, re.I):
        block = section.group(0)
        if re.search(r'class=["\'][^"\']*(?:kh-book-card|sard-book-card)', block, re.I):
            return block
    return ""


def shelf_anchor(content: str, post_id: int) -> str:
    for section in re.finditer(r"<section\b[^>]*>[\s\S]*?</section>", content, re.I):
        block = section.group(0)
        if re.search(r'class=["\'][^"\']*(?:kh-book-card|sard-book-card)', block, re.I):
            id_match = re.search(r'\bid=["\']([^"\']+)["\']', block, re.I)
            if id_match:
                return id_match.group(1)
    return f"sard360-khizana-article-{post_id}"


def article_graph(cards: list[dict], link: str, post_id: int, anchor_id: str) -> list[dict]:
    return [book_node(card, link, i, post_id, anchor_id) for i, card in enumerate(cards, 1)]


def author_surnames(value: str) -> set[str]:
    value = re.sub(r"\bet\s+al\.?\s*.*$|\b(?:ed|eds|editor|editors)\.?\b.*$|\([^)]*\)", "", value, flags=re.I)
    names = re.split(r"\s*(?:&|\band\b|,|·)\s*", value.lower())
    result = set()
    for name in names:
        tokens = re.findall(r"[a-z][a-z'-]+", name)
        if tokens:
            result.add(tokens[-1])
    return result


def annotate_offer_mismatches(cards: list[dict], registry_row: dict, post_id: int) -> list[dict]:
    """Exclude only offers contradicted by recorded Amazon author metadata."""
    records = {str(book.get("isbn", "")).upper(): book for book in registry_row.get("books", []) if book.get("isbn")}
    verified_target_isbns = {book["isbn"] for book in TARGETS.get(post_id, [])}
    exclusions = []
    for card in cards:
        if card.get("asin") in verified_target_isbns:
            card["isbn"] = card["asin"]
        record = records.get(card.get("asin", ""))
        if not record:
            continue
        verified_author = str(record.get("verified_author") or "").strip()
        visible_author = str(card.get("author_name") or "").strip()
        expected_surnames = author_surnames(verified_author)
        visible_surnames = author_surnames(visible_author)
        if expected_surnames and visible_surnames and expected_surnames.isdisjoint(visible_surnames):
            card["schema_offer_excluded"] = True
            exclusions.append({
                "asin": card.get("asin"),
                "visible_title": card.get("name") or card.get("alt_name"),
                "reason": f"Amazon/verified author ({verified_author}) conflicts with visible author ({visible_author})",
            })
    return exclusions


def image_absolute(src: str) -> str:
    if not src:
        return ""
    if src.startswith("https://"):
        return src
    return "https://safar360-alpha.vercel.app/" + src.lstrip("/")


def extract_author_from_title(title: str) -> str:
    parts = re.split(r"\s+[—–-]\s+", title)
    return parts[-1].strip() if len(parts) > 1 else ""


def khizana_graph(products: dict) -> list[dict]:
    graph: list[dict] = []
    page = "https://sard360.com/khizana/"
    for item in products.get("books", []):
        title = str(item.get("title", "")).strip()
        raw_url = item.get("affiliate_url") or item.get("affiliateUrl") or ""
        if not title or not raw_url:
            continue
        url = tagged_url(raw_url)
        author = extract_author_from_title(title)
        node = {
            "@type": "Book",
            "@id": f"{page}#{item.get('id') or len(graph)+1}",
            "name": title,
            "url": f"{page}#{item.get('id') or len(graph)+1}",
            "description": item.get("desc") or item.get("description") or "",
            "inLanguage": "ar" if re.search(r"[\u0600-\u06ff]", title) else "en",
            "offers": {"@type": "Offer", "url": url},
        }
        if author:
            node["author"] = {"@type": "Person", "name": author}
        # The JSON catalogue currently uses a shared decorative image for many books;
        # omit it rather than claiming a generic shelf illustration is a cover.
        graph.append(node)
    for item in products.get("master_items", []):
        title = str(item.get("title", "")).strip()
        raw_variants = item.get("variants", []) or []
        raw_urls = [v.get("affiliate_url") or v.get("affiliateUrl") for v in raw_variants if v.get("affiliate_url") or v.get("affiliateUrl")]
        if not raw_urls:
            raw = item.get("affiliate_url") or item.get("affiliateUrl")
            raw_urls = [raw] if raw else []
        offers = [{"@type": "Offer", "url": tagged_url(u)} for u in raw_urls]
        if not title or not offers:
            continue
        node = {
            "@type": "Product",
            "@id": f"{page}#{item.get('id') or len(graph)+1}",
            "name": title,
            "url": f"{page}#{item.get('id') or len(graph)+1}",
            "description": item.get("desc") or item.get("description") or "",
            "category": item.get("category", ""),
            "offers": offers[0] if len(offers) == 1 else offers,
        }
        image = image_absolute(item.get("image_url") or item.get("image") or "")
        if image:
            node["image"] = image
        graph.append(node)
    return graph


def cinema_graph(catalogue: dict) -> list[dict]:
    graph = []
    for item in catalogue.get("items", []):
        youtube_url = str(item.get("youtube_url", ""))
        match = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", youtube_url)
        if not match:
            continue
        vid = match.group(1)
        seconds = max(0, int(float(item.get("duration_seconds", 0) or 0)))
        hours, remainder = divmod(seconds, 3600)
        minutes, sec = divmod(remainder, 60)
        duration = f"PT{hours}H{minutes}M{sec}S" if hours else (f"PT{minutes}M{sec}S" if minutes else f"PT{sec}S")
        thumb = item.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        graph.append({
            "@type": "VideoObject",
            "@id": f"https://sard360.com/cinema/#video-{vid}",
            "name": item.get("title", ""),
            "description": item.get("description", ""),
            "thumbnailUrl": [thumb],
            "embedUrl": f"https://www.youtube-nocookie.com/embed/{vid}",
            "contentUrl": youtube_url,
            "duration": duration,
            "genre": item.get("category", ""),
            "inLanguage": "ar",
            "creator": {"@type": "Organization", "name": "سرد 360", "url": "https://sard360.com/"},
            "publisher": {"@type": "Organization", "name": "سرد 360", "url": "https://sard360.com/"},
        })
    return graph


def atomic_json(path: Path, data: object) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def fetch_public(session: requests.Session, link: str) -> int:
    last_error = None
    for attempt in range(3):
        try:
            r = session.get(link, timeout=(12, 25), allow_redirects=True, headers={"User-Agent": "Mozilla/5.0 Sard360Audit/1.0"})
            if r.status_code >= 500 and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            return r.status_code
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            raise
    raise last_error or RuntimeError(f"Public permalink check failed: {link}")


def update_catalog_pages(session: requests.Session, apply: bool, products: dict, catalogue: dict) -> dict:
    results = {}
    for slug, graph, marker in [
        ("khizana", khizana_graph(products), "sard360-khizana-catalog-jsonld"),
        ("cinema", cinema_graph(catalogue), "sard360-cinema-jsonld"),
    ]:
        pages = api_get(session, "/pages", {"slug": slug, "context": "edit"})
        if not pages:
            raise RuntimeError(f"WordPress page /{slug} not found.")
        page = pages[0]
        content = page["content"]["raw"]
        if slug == "cinema" and EMBED_PATH.exists():
            generated = EMBED_PATH.read_text(encoding="utf-8").strip()
            if "<!-- wp:html -->" in content and "<!-- /wp:html -->" in content:
                new_content = f"<!-- wp:html -->\n{generated}\n<!-- /wp:html -->"
            else:
                raise RuntimeError("Cinema page is not a single custom HTML block; refusing to replace its content.")
        else:
            new_content = inline_schema(content, graph, marker)
        if slug == "cinema":
            # Embed builder already emits the script; ensure its data is the complete graph.
            new_content = re.sub(
                r'(<script type="application/ld\+json" id="sard360-cinema-jsonld">).*?(</script>)',
                lambda m: m.group(1) + safe_json({"@context": "https://schema.org", "@graph": graph}) + m.group(2),
                new_content,
                count=1,
                flags=re.I | re.S,
            )
        if apply and new_content != content:
            saved = api_update_page(session, int(page["id"]), new_content)
            content = saved["content"].get("raw", "")
            if marker not in content:
                raise RuntimeError(f"WordPress did not preserve the {slug} JSON-LD marker.")
        results[slug] = {"id": page["id"], "status": page.get("status"), "nodes": len(graph), "changed": new_content != page["content"]["raw"]}
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write the changes to WordPress; default is dry-run.")
    ap.add_argument("--pause", type=float, default=1.0)
    args = ap.parse_args()
    if args.pause < 0.5:
        raise SystemExit("Pause must be at least 0.5 seconds.")
    session = get_session()
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    catalogue = json.loads(CINEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        raise RuntimeError("Expected the tracked registry to be a dictionary keyed by WordPress post ID.")
    status_counts: dict[str, int] = {}
    for row in registry.values():
        status_counts[row.get("status", "?")] = status_counts.get(row.get("status", "?"), 0) + 1
    print("REGISTRY", len(registry), status_counts)
    print("CATALOG", "khizana_books", len(khizana_graph(products)), "cinema_videos", len(cinema_graph(catalogue)))
    if set(TARGETS) - {int(k) for k in registry}:
        raise RuntimeError(f"Target IDs missing from registry: {sorted(set(TARGETS) - {int(k) for k in registry})}")
    if not EMBED_PATH.exists():
        raise RuntimeError("Build the static WordPress Cinema embed before applying this script.")
    template_css = load_template_css(session)

    # Curated target book links: strict ISBN check, tag enforcement and HTTP check.
    verified_targets = {}
    for post_id, books in TARGETS.items():
        checkpoint = registry.get(str(post_id), {})
        if args.apply and checkpoint.get("schema_org_status") == "published" and len(checkpoint.get("amazon_proofs", [])) == len(books):
            verified_targets[post_id] = []
            print(f"TARGET {post_id}: Amazon proofs already checkpointed; skip", flush=True)
            continue
        checked = []
        for source in books:
            book = build_book_data(source)
            proof = verify_amazon_url(session, book["url"], book["original"])
            checked.append({**book, "amazon_check": proof})
            time.sleep(args.pause)
        verified_targets[post_id] = checked
    print("TARGET_BOOKS_VALIDATED", sum(len(v) for v in verified_targets.values()))

    changed_posts = []
    target_id_set = set(TARGETS)
    for key in sorted(registry, key=lambda s: int(s)):
        if args.apply and registry[key].get("schema_org_status") == "published" and registry[key].get("schema_org_version") == 2:
            print(f"POST {key}: checkpoint already published; skip", flush=True)
            continue
        post_id = int(key)
        post = api_get(session, f"/posts/{post_id}", {"context": "edit"})
        if post.get("status") != "publish":
            raise RuntimeError(f"Post {post_id} is not published; refusing to alter unexpected status.")
        link = post.get("link", "")
        if not link:
            raise RuntimeError(f"WordPress omitted the native permalink for post {post_id}.")
        original = post["content"]["raw"]
        current = original
        shelf_before = find_shelf(original, post_id)
        if post_id in target_id_set and not shelf_before:
            shelf = build_shelf(post_id, post["title"].get("raw", ""), verified_targets[post_id], template_css)
            current = insert_shelf(current, shelf)
        cards = extract_cards(current)
        if not cards:
            raise RuntimeError(f"No visible Micro-Khizana book cards found for registry post {post_id}.")
        offer_exclusions = annotate_offer_mismatches(cards, registry[key], post_id)
        for excluded in offer_exclusions:
            print(f"  SCHEMA_OFFER_EXCLUDED: {json.dumps(excluded, ensure_ascii=False)}", flush=True)
        # Verify every rendered Amazon CTA has the exact affiliate tag and required security attributes.
        expected_count = len(verified_targets[post_id]) if post_id in target_id_set and verified_targets[post_id] else len(cards)
        if len(cards) < expected_count:
            raise RuntimeError(f"Card count mismatch for post {post_id}: {len(cards)} < {expected_count}.")
        for card in cards:
            if f"tag={AFFILIATE_TAG}" not in card["url"]:
                raise RuntimeError(f"Affiliate tag missing in a rendered card for post {post_id}.")
            required_rel = {"sponsored", "nofollow", "noopener"}
            rel_tokens = set(card.get("rel", "").split())
            legacy_rel = {"sponsored", "noopener", "noreferrer"}
            if card.get("target") != "_blank" or not (required_rel.issubset(rel_tokens) or legacy_rel.issubset(rel_tokens)):
                raise RuntimeError(f"Affiliate link security attributes invalid in post {post_id}: {card.get('target')!r} {card.get('rel')!r}")
            if legacy_rel.issubset(rel_tokens) and not required_rel.issubset(rel_tokens):
                print(f"LEGACY_REL_PRESERVED post={post_id}; existing block remains untouched", flush=True)
        graph = article_graph(cards, link, post_id, shelf_anchor(current, post_id))
        script_id = f"sard360-article-books-{post_id}"
        current = inline_schema(current, graph, script_id)
        if shelf_before and find_shelf(current, post_id) != shelf_before:
            raise RuntimeError(f"Existing Micro-Khizana HTML changed unexpectedly in post {post_id}.")
        will_change = current != original
        print(f"POST {post_id}: {post['title'].get('raw','')} | {len(cards)} Book nodes | {'UPDATE' if will_change else 'already current'}")
        if args.apply and will_change:
            saved = api_update_post(session, post_id, current)
            saved_raw = saved.get("content", {}).get("raw", "")
            if script_id not in saved_raw or f"tag={AFFILIATE_TAG}" not in saved_raw:
                raise RuntimeError(f"WordPress did not preserve the expected schema/link markup in post {post_id}.")
            if shelf_before and find_shelf(saved_raw, post_id) != shelf_before:
                raise RuntimeError(f"WordPress changed an existing visible Micro-Khizana block in post {post_id}.")
            status = fetch_public(session, link)
            if status != 200:
                raise RuntimeError(f"Updated post permalink did not return HTTP 200: post {post_id}, HTTP {status}")
            # The update response already contains the saved raw content. Use it
            # for the per-post checkpoint instead of issuing a second expensive GET.
            post_check = saved
            checked_cards = extract_cards(saved_raw)
            row = registry[key]
            row.update({
                "id": post_id,
                "title": post_check["title"].get("raw", ""),
                "slug": post_check.get("slug", ""),
                "link": post_check.get("link", ""),
                "status": "treated",
                "schema_org_status": "published",
                "schema_org_version": 2,
                "schema_book_nodes": len(checked_cards),
                "schema_offer_exclusions": offer_exclusions,
                "article_http": status,
                "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
            row.setdefault("book_titles", [c.get("alt_name") or c.get("name") for c in checked_cards])
            row.setdefault("books_isbn", [c.get("isbn", "") for c in checked_cards])
            row.setdefault("book_count", len(checked_cards))
            if post_id in target_id_set and verified_targets[post_id]:
                row.update({
                    "book_titles": [b["title_ar"] for b in verified_targets[post_id]],
                    "books_isbn": [b["isbn"] for b in verified_targets[post_id]],
                    "book_count": len(verified_targets[post_id]),
                    "books": [{k: b.get(k) for k in ("title_ar", "original", "author_ar", "author_en", "kind", "summary", "isbn", "url", "image", "amazon_check")} for b in verified_targets[post_id]],
                    "amazon_proofs": [b["amazon_check"] for b in verified_targets[post_id]],
                })
                for stale in ("last_error", "partial_books", "partial_book_isbns"):
                    row.pop(stale, None)
            # Keep video status conservative: an association is recorded only if an exact YouTube ID exists in the post.
            body_text = post_check["content"]["raw"]
            match_ids = {m.group(1) for m in re.finditer(r"(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})", body_text)}
            matched = None
            for video in catalogue.get("items", []):
                video_match = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", video.get("youtube_url", ""))
                if video_match and video_match.group(1) in match_ids:
                    matched = video
                    break
            row["cinema_status"] = "matched" if matched else "none"
            if matched:
                row["cinema_video_id"] = matched.get("id")
                row["cinema_video_title"] = matched.get("title")
            atomic_json(REGISTRY_PATH, registry)
            changed_posts.append(post_id)
            print(f"  SAVED: permalink HTTP {status}; registry checkpoint written")
            time.sleep(args.pause)
        elif not args.apply and will_change:
            changed_posts.append(post_id)
        elif args.apply:
            status = fetch_public(session, link)
            if status != 200:
                raise RuntimeError(f"Existing post permalink did not return HTTP 200: post {post_id}, HTTP {status}")
            registry[key].update({
                "schema_org_status": "published",
                "schema_org_version": 2,
                "schema_book_nodes": len(cards),
                "schema_offer_exclusions": offer_exclusions,
                "article_http": status,
                "schema_checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
            atomic_json(REGISTRY_PATH, registry)
            print(f"  CHECKPOINT: JSON-LD already current; permalink HTTP {status}", flush=True)
            time.sleep(args.pause)

    # Verify treated posts with existing schema and produce full catalog-page JSON-LD.
    # All tracked entries now have a shelf. Fail rather than silently omitting a post.
    if args.apply:
        atomic_json(REGISTRY_PATH, registry)
    pages = update_catalog_pages(session, args.apply, products, catalogue)
    print("CATALOG_PAGES", json.dumps(pages, ensure_ascii=False))
    print("POSTS_CHANGED", len(changed_posts), changed_posts)
    print("DRY_RUN" if not args.apply else "APPLY_COMPLETE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        raise
