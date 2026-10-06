#!/usr/bin/env python3
"""Enrich cinema.json with evidence-backed Micro-Khizana book references.

The script intentionally uses sequential batches (default 8) rather than agent fan-out.
It asks the LLM only for search phrases and candidate selection; every selected title,
author, publisher and ISBN must come from Open Library records verified by ISBN.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests
from openai import OpenAI
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "cinema.json"
AUDIT_PATH = Path("/tmp/safar360-khizana-audit.json")
MODEL = "gpt-5-mini"
BATCH_SIZE_DEFAULT = 8
AMBIENT_CATEGORY = "أجواء وموسيقى"
AFFILIATE_TAG = "sard360-20"
BOOK_TYPES = ["الرواية الأصلية", "المرجع التاريخي", "سيرة الكاتب", "دراسة موثقة", "مرجع علمي"]

# Previously verified/approved editorial records. These are never guessed by the model.
SEEDS: dict[str, list[dict[str, str]]] = {
    "video-mHUWXmz9QiI": [{
        "type": "مرجع علمي",
        "title": "Komodo Dragons: Biology and Conservation — James B. Murphy, Claudio Ciofi, Colomba de La Panouse, Trooper Walsh",
        "url": "https://www.amazon.com/dp/1588340732?tag=sard360-20",
    }],
    "video-w4bqC-F1xO0": [
        {"type": "الرواية الأصلية", "title": "ألموت — فلاديمير بارتول (ترجمة مايكل بيغينز)", "url": "https://amzn.to/3VRSBIC?tag=sard360-20"},
        {"type": "المرجع التاريخي", "title": "الحشاشون: طائفة راديكالية في الإسلام — برنارد لويس", "url": "https://amzn.to/3VqI72U?tag=sard360-20"},
    ],
    "video-aGI8iiCyM0Y": [{
        "type": "دراسة موثقة",
        "title": "The Serengeti Lion: A Study of Predator-Prey Relations — George B. Schaller",
        "url": "https://www.amazon.com/dp/B01JXSQJK4?tag=sard360-20",
    }],
    "video-3H15cPUDB6g": [{
        "type": "مرجع علمي",
        "title": "The Migration Ecology of Birds, 2nd Edition — Ian Newton",
        "url": "https://www.amazon.com/dp/0128237511?tag=sard360-20",
    }],
    # No sufficiently strong, directly relevant book was found for the cassowary video; avoid a geographic mismatch.
    "video-ihbgXvjqlB0": [],
    "video-SMx54LlWnog": [{
        "type": "مرجع علمي",
        "title": "Penguins: Natural History and Conservation — Pablo Garcia Borboroglu & P. Dee Boersma",
        "url": "https://www.amazon.com/dp/0295992840?tag=sard360-20",
    }],
    "video-QaVs-KD8R-w": [{
        "type": "مرجع علمي",
        "title": "Seahorses — Sara A. Lourie",
        "url": "https://www.amazon.com/dp/022633841X?tag=sard360-20",
    }],
    "video-QTxK1QuIdBA": [{
        "type": "مرجع علمي",
        "title": "Biology of Coccinellidae — Ivo Hodek",
        "url": "https://www.amazon.com/dp/9061932467?tag=sard360-20",
    }],
    "video-2FunfE7YiXk": [{
        "type": "مرجع علمي",
        "title": "Kangaroos: Biology of the Largest Marsupials — Terence J. Dawson",
        "url": "https://www.amazon.com/dp/0801482623?tag=sard360-20",
    }],
    "video-RjKBgNHPIgo": [{
        "type": "مرجع علمي",
        "title": "Megalodon and Other Prehistoric Sharks — Jack Cooper",
        "url": "https://www.amazon.com/dp/069129447X?tag=sard360-20",
    }],
    "video-Ru8z4dpsOZE": [{
        "type": "مرجع علمي",
        "title": "Marine Mammals: Evolutionary Biology, 3rd Edition — Annalisa Berta et al.",
        "url": "https://www.amazon.com/dp/0123970024?tag=sard360-20",
    }],
    "dolphin-alliances": [{
        "type": "دراسة موثقة",
        "title": "Cetacean Societies: Field Studies of Dolphins and Whales — Janet Mann et al.",
        "url": "https://www.amazon.com/dp/0226503410?tag=sard360-20",
    }],
    "video-8P-r9EU6Z44": [{
        "type": "مرجع علمي",
        "title": "The Return of the Unicorns — Eric Dinerstein",
        "url": "https://www.amazon.com/dp/023108451X?tag=sard360-20",
    }],
    "video-4d4dWDK2g3Q": [{
        "type": "مرجع علمي",
        "title": "Polar Bears: A Complete Guide to Their Biology and Behavior — Andrew E. Derocher",
        "url": "https://www.amazon.com/dp/1421403056?tag=sard360-20",
    }],
    "video-D5c8wOYCh1Q": [{
        "type": "مرجع علمي",
        "title": "Jellyfish: A Natural History — Lisa-ann Gershwin",
        "url": "https://www.amazon.com/dp/022628767X?tag=sard360-20",
    }],
    "video-LGIn_8fAik0": [{
        "type": "دراسة موثقة",
        "title": "Are Dolphins Really Smart? — Justin Gregg",
        "url": "https://www.amazon.com/dp/019966045X?tag=sard360-20",
    }],
    "video-_Z4QO74fKI8": [{
        "type": "دراسة موثقة",
        "title": "Wolves: Behavior, Ecology, and Conservation — L. David Mech & Luigi Boitani",
        "url": "https://www.amazon.com/dp/0226516970?tag=sard360-20",
    }],
    "blind-sunflowers-novel": [{
        "type": "الرواية الأصلية",
        "title": "Los girasoles ciegos (The Blind Sunflowers) — Alberto Méndez",
        "url": "https://www.amazon.com/dp/8447360881?tag=sard360-20",
    }],
    "video-ZYtn59RDz4E": [{
        "type": "مرجع علمي",
        "title": "Sea Turtles: A Complete Guide to Their Biology, Behavior, and Conservation — James R. Spotila",
        "url": "https://www.amazon.com/dp/0801880076?tag=sard360-20",
    }],
    "video-1SYUhlczH8g": [{
        "type": "دراسة موثقة",
        "title": "Hannibal: A Hellenistic Life — Eve MacDonald",
        "url": "https://www.amazon.com/dp/0300240309?tag=sard360-20",
    }],
    "video-2rAF9VGMjJY": [{
        "type": "مرجع علمي",
        "title": "Giant Pandas: Biology and Conservation — edited by Donald Lindburg & Karen Baragona",
        "url": "https://www.amazon.com/dp/0520238672?tag=sard360-20",
    }],
    "cleopatra-queen-nile": [{
        "type": "دراسة موثقة",
        "title": "Cleopatra: A Life — Stacy Schiff",
        "url": "https://www.amazon.com/dp/0316001945?tag=sard360-20",
    }],
    "zorba-freedom": [{
        "type": "الرواية الأصلية",
        "title": "Zorba the Greek — Nikos Kazantzakis (translated by Peter Bien)",
        "url": "https://www.amazon.com/dp/1476782814?tag=sard360-20",
    }],
    "one-hundred-years-solitude": [{
        "type": "الرواية الأصلية",
        "title": "One Hundred Years of Solitude (Cien años de soledad) — Gabriel García Márquez, translated by Gregory Rabassa",
        "url": "https://www.amazon.com/dp/0060883286?tag=sard360-20",
    }],
    "wolf-and-predators": [{
        "type": "مرجع علمي",
        "title": "Canids of the World — José R. Castelló",
        "url": "https://www.amazon.com/dp/069117685X?tag=sard360-20",
    }],
}


def atomic_json_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
        tmp = Path(f.name)
    tmp.replace(path)


def load_audit() -> dict[str, Any]:
    if AUDIT_PATH.exists():
        try:
            with AUDIT_PATH.open("r", encoding="utf-8") as f:
                value = json.load(f)
            if isinstance(value, dict):
                return value
        except (OSError, json.JSONDecodeError):
            pass
    return {"records": {}}


def load_catalog() -> dict[str, Any]:
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def isbn_is_valid(value: str) -> bool:
    value = re.sub(r"[^0-9Xx]", "", value).upper()
    if len(value) == 10:
        if not re.fullmatch(r"\d{9}[\dX]", value):
            return False
        total = sum((10 - i) * (10 if char == "X" else int(char)) for i, char in enumerate(value))
        return total % 11 == 0
    if len(value) == 13 and value.isdigit():
        total = sum((1 if i % 2 == 0 else 3) * int(char) for i, char in enumerate(value[:12]))
        return (10 - total % 10) % 10 == int(value[-1])
    return False


def candidate_query(phrase: str, session: requests.Session) -> list[dict[str, Any]]:
    fields = "key,title,author_name,publisher,first_publish_year,isbn,subject,edition_count,ratings_average,ratings_count,first_sentence"
    params = {"q": phrase, "limit": 15, "fields": fields}
    response = session.get("https://openlibrary.org/search.json", params=params, timeout=25)
    response.raise_for_status()
    payload = response.json()
    candidates: list[dict[str, Any]] = []
    for n, doc in enumerate(payload.get("docs", [])):
        raw_isbns = doc.get("isbn") or []
        isbn10 = next((x for x in raw_isbns if len(re.sub(r"[^0-9Xx]", "", x)) == 10 and isbn_is_valid(x)), "")
        isbn13 = next((x for x in raw_isbns if len(re.sub(r"[^0-9Xx]", "", x)) == 13 and isbn_is_valid(x)), "")
        if not (isbn10 or isbn13):
            continue
        key = str(doc.get("key") or "")
        first_sentence = doc.get("first_sentence") or []
        if isinstance(first_sentence, str):
            first_sentence = [first_sentence]
        candidates.append({
            "candidate_id": key or f"candidate-{n}",
            "title": str(doc.get("title") or "").strip(),
            "subtitle": "",
            "authors": doc.get("author_name") or [],
            "publisher": doc.get("publisher") or [],
            "published_date": doc.get("first_publish_year") or "",
            "description": re.sub(r"\s+", " ", " ".join(str(x) for x in first_sentence))[:700],
            "categories": doc.get("subject") or [],
            "average_rating": doc.get("ratings_average"),
            "ratings_count": doc.get("ratings_count", 0),
            "edition_count": doc.get("edition_count", 0),
            "isbn_10": isbn10,
            "isbn_13": isbn13,
            "source_url": f"https://openlibrary.org{key}" if key.startswith("/") else "",
        })
    return candidates


def isbn10_to_13(value: str) -> str:
    clean = re.sub(r"[^0-9Xx]", "", value).upper()
    if not isbn_is_valid(clean) or len(clean) != 10:
        return ""
    stem = "978" + clean[:9]
    check = (10 - sum((1 if i % 2 == 0 else 3) * int(char) for i, char in enumerate(stem)) % 10) % 10
    return stem + str(check)


def isbn13_to_10(value: str) -> str:
    clean = re.sub(r"[^0-9Xx]", "", value).upper()
    if not isbn_is_valid(clean) or len(clean) != 13 or not clean.startswith("978"):
        return ""
    stem = clean[3:12]
    total = sum((10 - i) * int(char) for i, char in enumerate(stem))
    check = (11 - total % 11) % 11
    return stem + ("X" if check == 10 else str(check))


def verify_openlibrary_edition(isbn: str, session: requests.Session) -> dict[str, Any]:
    response = session.get(f"https://openlibrary.org/isbn/{isbn}.json", timeout=25)
    response.raise_for_status()
    edition = response.json()
    recorded = (edition.get("isbn_10") or []) + (edition.get("isbn_13") or [])
    clean_recorded = {re.sub(r"[^0-9Xx]", "", x).upper() for x in recorded}
    clean_requested = re.sub(r"[^0-9Xx]", "", isbn).upper()
    equivalents = {clean_requested, isbn10_to_13(clean_requested), isbn13_to_10(clean_requested)}
    if not (equivalents & clean_recorded) or not edition.get("title"):
        raise ValueError(f"ISBN {isbn} did not resolve to a matching Open Library edition.")
    return {"title": edition.get("title"), "publishers": edition.get("publishers", []), "edition_url": response.url}


def chat_json(client: OpenAI, schema_name: str, schema: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_completion_tokens=4000,
        response_format={"type": "json_schema", "json_schema": {"name": schema_name, "strict": True, "schema": schema}},
    )
    choice = response.choices[0]
    content = choice.message.content
    if not content:
        raise RuntimeError(f"The LLM returned empty content for {schema_name}; finish_reason={choice.finish_reason}; "
                           f"refusal={getattr(choice.message, 'refusal', None)!r}; usage={response.usage}.")
    return json.loads(content)


def plan_searches(client: OpenAI, batch: list[dict[str, Any]]) -> dict[str, Any]:
    schema = {
        "type": "object", "properties": {"items": {"type": "array", "items": {
            "type": "object", "properties": {
                "video_id": {"type": "string"},
                "queries": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
                "empty_reason": {"type": "string"},
            }, "required": ["video_id", "queries", "empty_reason"], "additionalProperties": False,
        }}}, "required": ["items"], "additionalProperties": False,
    }
    items = [{"video_id": x.get("id", x.get("youtube_id", "")), "title": x.get("title", ""),
              "category": x.get("category", ""), "description": x.get("description", ""),
              "playlist": x.get("source_playlists", [])} for x in batch]
    return chat_json(client, "khizana_search_plan", schema, [
        {"role": "system", "content": (
            "You create compact Open Library search phrases for an Arabic documentary catalogue. "
            "Infer the actual subject from each title; do not invent books or citations. Return 2-3 short English queries per item, each with at most 5 meaningful words. "
            "Open Library treats many query words as required, so avoid long phrases, parentheses, and Latin binomials. "
            "For animals, query 1 must be the common species/group name; query 2 may add natural history or biology; query 3 should be a reputable field guide or taxonomic-group monograph. "
            "For history, include the person/place/event in short phrases and try one scholarly biography or history query; for named novels, search the exact work and author. "
            "Use [] only for genuinely contemplative/music items with no direct intellectual book connection. Preserve each video_id exactly."
        )},
        {"role": "user", "content": json.dumps(items, ensure_ascii=False)},
    ])


def choose_books(client: OpenAI, batch: list[dict[str, Any]], candidates_by_video: dict[str, list[dict[str, Any]]], used_titles: list[str]) -> dict[str, Any]:
    schema = {
        "type": "object", "properties": {"items": {"type": "array", "items": {
            "type": "object", "properties": {
                "video_id": {"type": "string"},
                "books": {"type": "array", "items": {
                    "type": "object", "properties": {
                        "candidate_id": {"type": "string"}, "type": {"type": "string", "enum": BOOK_TYPES}, "reason": {"type": "string"}
                    }, "required": ["candidate_id", "type", "reason"], "additionalProperties": False
                }, "maxItems": 2},
                "empty_reason": {"type": "string"},
            }, "required": ["video_id", "books", "empty_reason"], "additionalProperties": False,
        }}}, "required": ["items"], "additionalProperties": False,
    }
    payload = []
    for item in batch:
        vid = item.get("id", item.get("youtube_id", ""))
        payload.append({"video_id": vid, "title": item.get("title", ""), "category": item.get("category", ""),
                       "candidates": candidates_by_video.get(vid, [])})
    return chat_json(client, "khizana_book_selection", schema, [
        {"role": "system", "content": (
            "You are an exacting Arabic-language cultural and science editor for Sard 360. Select 0-2 real books ONLY from the supplied Open Library candidates. "
            "Never invent or rewrite titles, authors, publishers, ISBNs, or candidate IDs. Choose primary sources, reputable scholarship, original novels, or respected science books with direct relevance. "
            "Reject children's picture books, school readers, novelty trivia, generic low-quality works, and fiction except the exact original novel being discussed. "
            "For animals, a substantial field guide or taxonomic-group monograph is acceptable when a species-specific scholarly book does not surface. "
            "Prefer a single excellent book over a weak two-book kit. Do not force books onto ambience/music. Do not repeat these already-used works unless indispensable: "
            + json.dumps(used_titles, ensure_ascii=False) + ". Each reason must state the specific fit briefly. Use type labels from the schema. If candidates are weak, return books=[] and explain why."
        )},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ])


def normalized_key(title: str, authors: list[str] | None = None) -> str:
    text = unicodedata.normalize("NFKD", title + " " + " ".join(authors or []))
    return re.sub(r"[^a-z0-9\u0600-\u06ff]+", " ", text.casefold()).strip()


def tag_url(url: str) -> str:
    from urllib.parse import urlsplit, urlunsplit, parse_qsl
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["tag"] = AFFILIATE_TAG
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def seed_verified_records(catalogue: dict[str, Any]) -> None:
    for item in catalogue.get("items", []):
        vid = item.get("id", "")
        if vid in SEEDS:
            item["khizana_books"] = [dict(book) for book in SEEDS[vid]]
        elif not isinstance(item.get("khizana_books"), list):
            item["khizana_books"] = []
        for book in item.get("khizana_books", []):
            if book.get("url", "").startswith("https://amzn.to/") or "amazon." in book.get("url", ""):
                book["url"] = tag_url(book["url"])


SEED_EMPTY_REASONS = {
    "video-ihbgXvjqlB0": "No sufficiently strong, directly relevant book was found for cassowaries; a geographic mismatch or weak children's title was intentionally avoided."
}


def sync_seed_audit(audit: dict[str, Any]) -> None:
    records = audit.setdefault("records", {})
    for vid, books in SEEDS.items():
        records[vid] = {
            "status": "done",
            "queries": [],
            "candidates_considered": 0,
            "books": [{"title": book["title"], "url": book["url"], "source": "manually verified seed"} for book in books],
            "errors": [],
            "empty_reason": SEED_EMPTY_REASONS.get(vid, "") if not books else "",
        }


def update_batch(catalogue: dict[str, Any], batch: list[dict[str, Any]], plans: dict[str, Any], client: OpenAI,
                 session: requests.Session, audit: dict[str, Any]) -> None:
    plan_by_id = {x.get("video_id"): x for x in plans.get("items", []) if isinstance(x, dict)}
    candidates_by_video: dict[str, list[dict[str, Any]]] = {}
    errors_by_video: dict[str, list[str]] = {}
    for item in batch:
        vid = item.get("id", item.get("youtube_id", ""))
        if item.get("category") == AMBIENT_CATEGORY:
            candidates_by_video[vid] = []
            continue
        phrases = plan_by_id.get(vid, {}).get("queries", [])
        found: list[dict[str, Any]] = []
        seen: set[str] = set()
        for phrase in phrases[:2]:
            try:
                for candidate in candidate_query(phrase, session):
                    key = normalized_key(candidate["title"], candidate["authors"])
                    if candidate["title"] and key not in seen:
                        seen.add(key)
                        found.append(candidate)
            except (requests.RequestException, ValueError) as exc:
                print(f"  Open Library query failed for {vid}: {exc}", file=sys.stderr)
                errors_by_video.setdefault(vid, []).append(str(exc))
            time.sleep(1.0)
        candidates_by_video[vid] = found[:12]
    used_titles = []
    for item in catalogue.get("items", []):
        for book in item.get("khizana_books", []):
            used_titles.append(book.get("title", ""))
    selections = choose_books(client, batch, candidates_by_video, used_titles)
    selection_by_id = {x.get("video_id"): x for x in selections.get("items", []) if isinstance(x, dict)}
    candidate_maps = {vid: {x["candidate_id"]: x for x in candidates} for vid, candidates in candidates_by_video.items()}
    for item in batch:
        vid = item.get("id", item.get("youtube_id", ""))
        selected = selection_by_id.get(vid, {"books": [], "empty_reason": "Aucune sélection structurée."})
        books: list[dict[str, str]] = []
        evidence: list[dict[str, Any]] = []
        verification_errors: list[str] = []
        for pick in selected.get("books", [])[:2]:
            candidate = candidate_maps.get(vid, {}).get(pick.get("candidate_id"))
            if not candidate:
                continue
            asin = candidate.get("isbn_10") or candidate.get("isbn_13")
            if not asin or not isbn_is_valid(asin):
                continue
            try:
                edition = verify_openlibrary_edition(asin, session)
            except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
                print(f"  Edition verification failed for {vid} ({asin}): {exc}", file=sys.stderr)
                verification_errors.append(str(exc))
                continue
            author_text = ", ".join(candidate.get("authors") or [])
            display_title = candidate["title"] + (f" — {author_text}" if author_text else "")
            books.append({"type": pick["type"], "title": display_title, "url": f"https://www.amazon.com/dp/{asin}?tag={AFFILIATE_TAG}"})
            evidence.append({"title": display_title, "publisher": candidate.get("publisher"), "published_date": candidate.get("published_date"),
                             "isbn": asin, "openlibrary_work_url": candidate.get("source_url"), "openlibrary_edition_url": edition.get("edition_url"),
                             "verified_edition_title": edition.get("title"), "editorial_fit": pick.get("reason", "")})
        item["khizana_books"] = books
        retryable_failure = bool((errors_by_video.get(vid) or verification_errors) and not books)
        reason = selected.get("empty_reason", "")
        if retryable_failure:
            reason = "; ".join(errors_by_video.get(vid, []) + verification_errors)
        audit["records"][vid] = {"status": "retry" if retryable_failure else "done", "queries": plan_by_id.get(vid, {}).get("queries", []),
                                 "candidates_considered": len(candidates_by_video.get(vid, [])), "books": evidence,
                                 "errors": errors_by_video.get(vid, []) + verification_errors, "empty_reason": reason}
        print(f"  {vid}: {len(books)} book(s) from {len(candidates_by_video.get(vid, []))} verified candidate(s)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE_DEFAULT, help="Items per local batch (5-10).")
    parser.add_argument("--max-batches", type=int, default=0, help="Optional limit for a controlled trial; 0 processes all pending batches.")
    parser.add_argument("--seed-only", action="store_true", help="Write only already verified/approved seed references and normalized arrays.")
    parser.add_argument("--reset-audit", action="store_true", help="Discard the local checkpoint before processing.")
    args = parser.parse_args()
    if not 5 <= args.batch_size <= 10:
        parser.error("--batch-size must be between 5 and 10.")

    catalogue = load_catalog()
    audit = {"records": {}} if args.reset_audit else load_audit()
    seed_verified_records(catalogue)
    sync_seed_audit(audit)
    if args.seed_only:
        atomic_json_write(CATALOG_PATH, catalogue)
        atomic_json_write(AUDIT_PATH, audit)
        print(f"Wrote verified seed references to {CATALOG_PATH} using UTF-8.")
        return 0

    if args.reset_audit:
        for item in catalogue.get("items", []):
            if item.get("id") not in SEEDS:
                item["khizana_books"] = []

    done = {vid for vid, record in audit.get("records", {}).items() if record.get("status") == "done"}
    pending = [item for item in catalogue.get("items", []) if item.get("id") not in done and item.get("id") not in SEEDS]
    for item in catalogue.get("items", []):
        if item.get("category") == AMBIENT_CATEGORY and item.get("id") not in done and item.get("id") not in SEEDS:
            item["khizana_books"] = []
            audit.setdefault("records", {})[item["id"]] = {"status": "done", "queries": [], "candidates_considered": 0, "books": [],
                                                              "empty_reason": "محتوى موسيقي/تأملي بلا مرجع كتابي مباشر؛ تُرك بلا ترشيح."}
    pending = [item for item in pending if item.get("category") != AMBIENT_CATEGORY]
    if not pending:
        atomic_json_write(CATALOG_PATH, catalogue)
        atomic_json_write(AUDIT_PATH, audit)
        print("No pending videos; catalogue and checkpoint are current.")
        return 0

    client = OpenAI()
    session = requests.Session()
    retry = Retry(total=5, connect=5, read=5, backoff_factor=0.7,
                  status_forcelist=(429, 500, 502, 503, 504), allowed_methods=frozenset(["GET"]))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "Sard360-KhizanaResearch/1.0 (+https://sard360.com)"})
    total_batches = (len(pending) + args.batch_size - 1) // args.batch_size
    processed = 0
    for offset in range(0, len(pending), args.batch_size):
        if args.max_batches and processed >= args.max_batches:
            break
        batch = pending[offset:offset + args.batch_size]
        batch_no = processed + 1
        print(f"Batch {batch_no}/{total_batches}: {len(batch)} videos", flush=True)
        plans = plan_searches(client, batch)
        update_batch(catalogue, batch, plans, client, session, audit)
        atomic_json_write(CATALOG_PATH, catalogue)
        atomic_json_write(AUDIT_PATH, audit)
        processed += 1
        print(f"  checkpoint saved after batch {batch_no}; pending batches remain: {total_batches - processed}", flush=True)
    print(f"Done: {sum(bool(x.get('khizana_books')) for x in catalogue.get('items', []))} videos now have at least one book reference; {len(catalogue.get('items', []))} total.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
