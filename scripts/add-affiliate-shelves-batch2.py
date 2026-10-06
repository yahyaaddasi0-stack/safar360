#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import requests
import json
from pathlib import Path

# Configuration
WP_BASE = 'https://sard360.com/wp-json/wp/v2'
USERNAME = os.environ.get('SARD360_WP_USERNAME')
PASSWORD = os.environ.get('SARD360_WP_APPLICATION_PASSWORD')

if not USERNAME or not PASSWORD:
    print("Error: Missing WordPress credentials.")
    sys.exit(1)

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers['Accept'] = 'application/json'

SHELVES_DATA = {
    4684: {
        "slug": "100-years-of-solitude-macondo-epic-time-oblivion",
        "style_slug": "solitude",
        "title": "لمواصلة التقصّي: مقتنيات من خزانة سرد حول مائة عام من العزلة",
        "anchor_header": "التأسيس.. هروباً من أشباح الماضي إلى متاهة العزلة",
        "anchor_level": 3,
        "books": [
            {
                "kind": "الرواية الأصلية",
                "title": "مائة عام من العزلة",
                "author": "غابرييل غارسيا ماركيز <span dir=\"ltr\">Gabriel García Márquez</span>",
                "summary": "التحفة الأدبية التي صاغت مفهوم الواقعية السحرية؛ ملحمة عائلة بوينديا في قرية ماكوندو، حيث يتداخل الخيال بالتاريخ والقدر بالعزلة في سرد لا ينسى.",
                "cta": "اقتنِ الرواية من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0060883286.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0060883286?tag=sard360-20"
            },
            {
                "kind": "السيرة الذاتية للكاتب",
                "title": "غابرييل غارسيا ماركيز: سيرة حياة",
                "author": "جيرالد مارتن <span dir=\"ltr\">Gerald Martin</span>",
                "summary": "السيرة الأشمل والموثقة لحياة ماركيز، تستعرض الجذور الواقعية والسياسية التي شكلت مخيلته وأدت إلى ولادة رائعته العالمية.",
                "cta": "اقتنِ السيرة من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0307271626.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0307271626?tag=sard360-20"
            }
        ]
    },
    4913: {
        "slug": "decline-of-arab-mind-from-house-of-wisdom-to-digital-triviality",
        "style_slug": "house-of-wisdom",
        "title": "لمواصلة التقصّي: مقتنيات من خزانة سرد حول بيت الحكمة والعقل العربي",
        "anchor_header": "إشعاع الأندلس وتكامل الفنون والعلوم",
        "anchor_level": 3,
        "books": [
            {
                "kind": "تاريخ العلوم",
                "title": "بيت الحكمة: كيف صنع العلم العربي عالمنا الغربي",
                "author": "جيم الخليلي <span dir=\"ltr\">Jim Al-Khalili</span>",
                "summary": "رحلة تاريخية وعلمية توثق عصر العصر الذهبي للعلوم الإسلامية، وكيف ساهمت الترجمة والابتكار في بغداد في وضع أسس النهضة العلمية الحديثة.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0143120565.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0143120565?tag=sard360-20"
            },
            {
                "kind": "دراسة فكرية",
                "title": "تاريخ المغرب: مقال تفسيري",
                "author": "عبد الله العروي <span dir=\"ltr\">Abdallah Laroui</span>",
                "summary": "دراسة نقدية وتاريخية عميقة للعقل العربي والتحولات الاجتماعية والسياسية، تقدم رؤية تفسيرية لمسارات التاريخ والهوية.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/1597402583.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/1597402583?tag=sard360-20"
            }
        ]
    },
    4719: {
        "slug": "zyryab-andalusia-inventor-of-etiquette-music-pioneer",
        "style_slug": "zyryab",
        "title": "لمواصلة التقصّي: مقتنيات من خزانة سرد حول زرياب والأندلس",
        "anchor_header": "تأسيس أول معهد موسيقي في العالم (الكونسرفتوار)",
        "anchor_level": 3,
        "books": [
            {
                "kind": "تاريخ وحضارة",
                "title": "جوهرة العالم: كيف صنع المسلمون واليهود والنصارى ثقافة التسامح في الأندلس",
                "author": "ماريا روزا مينوكال <span dir=\"ltr\">Maria Rosa Menocal</span>",
                "summary": "كتاب يبرز العصر الذهبي للأندلس وتمازج الثقافات الذي أثمر نهضة فنية واجتماعية، كان لزرياب دور مركزي في صياغة ذوقها العام.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0316168718.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0316168718?tag=sard360-20"
            },
            {
                "kind": "سيرة فنية",
                "title": "زرياب: ملاح الأندلس",
                "author": "خيسوس غريوس <span dir=\"ltr\">Jesús Greus</span>",
                "summary": "سيرة روائية تاريخية تتناول حياة زرياب وانتقاله من بغداد إلى قرطبة، مستعرضةً تأثيره الطاغي على الموسيقى، الأزياء، وفنون الطعام.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://covers.openlibrary.org/b/isbn/8493181827-M.jpg",
                "url": "https://www.amazon.com/dp/8493181827?tag=sard360-20"
            }
        ]
    },
    4716: {
        "slug": "%d8%a8%d8%b7%d8%a7%d8%b1%d9%8a%d8%a9-%d8%a8%d8%ba%d8%af%d8%a7%d8%af-%d9%87%d9%84-%d8%a7%d9%85%d8%aa%d9%84%d9%83%d8%aa-%d8%a7%d9%84%d8%ad%d8%b6%d8%a7%d8%b1%d8%a7%d8%aa-%d8%a7%d9%84%d9%82%d8%af",
        "style_slug": "baghdad-battery",
        "title": "لمواصلة التقصّي: مقتنيات من خزانة سرد حول بطارية بغداد والعلوم القديمة",
        "anchor_header": "مكونات الأداة الغامضة وتصميمها المعقد",
        "anchor_level": 3,
        "books": [
            {
                "kind": "تاريخ الاختراعات",
                "title": "الاختراعات القديمة",
                "author": "بيتر جيمس ونيك ثورب <span dir=\"ltr\">Peter James & Nick Thorpe</span>",
                "summary": "مسح شامل للاختراعات التقنية في العالم القديم، يضع بطارية بغداد في سياق تطور المعرفة الإنسانية بالتكنولوجيا والمواد.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0345401026.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0345401026?tag=sard360-20"
            },
            {
                "kind": "آثار وتاريخ",
                "title": "أعظم 70 اختراعاً في العالم القديم",
                "author": "برايان م. فاغان <span dir=\"ltr\">Brian M. Fagan</span>",
                "summary": "كتاب مصور يوثق أعظم المنجزات الهندسية والتقنية للحضارات الغابرة، مبيناً عبقرية القدماء في حل المشكلات التقنية.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0500051269.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0500051269?tag=sard360-20"
            }
        ]
    },
    4820: {
        "slug": "8-profound-short-books",
        "style_slug": "short-books",
        "title": "لمواصلة التقصّي: مقتنيات من خزانة سرد من روائع الروايات القصيرة",
        "anchor_header": "1. موت إيفان إيليتش (ليو تولستوي)",
        "anchor_level": 2,
        "books": [
            {
                "kind": "كلاسيكيات عالمية",
                "title": "الشيخ والبحر",
                "author": "إرنست همنغواي <span dir=\"ltr\">Ernest Hemingway</span>",
                "summary": "رواية فلسفية مكثفة تتأمل في معنى الكفاح، الهزيمة، والكرامة الإنسانية من خلال قصة صياد عجوز في مواجهة البحر.",
                "cta": "اقتنِ الرواية من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0684801221.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0684801221?tag=sard360-20"
            },
            {
                "kind": "أدب خالد",
                "title": "الأمير الصغير",
                "author": "أنطوان دي سانت أكزوبيري <span dir=\"ltr\">Antoine de Saint-Exupéry</span>",
                "summary": "واحدة من أكثر الكتب ترجمة في التاريخ؛ حكاية رمزية تخاطب الطفل الكامن فينا وتعيد تعريف القيم الإنسانية الجوهرية.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0156012197.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0156012197?tag=sard360-20"
            }
        ]
    }
}

def generate_style(style_slug):
    return f"""<style id="sard360-{style_slug}-shelf-styles">
#sard360-{style_slug}-shelf,#sard360-{style_slug}-shelf *{{box-sizing:border-box}}
#sard360-{style_slug}-shelf{{background:#080505;color:#f5efe2;border:1px solid rgba(212,163,89,.55);border-radius:18px;padding:24px 20px;margin:24px 0 40px;box-shadow:0 18px 45px rgba(0,0,0,.3);font-family:inherit;text-align:right;direction:rtl}}
#sard360-{style_slug}-shelf .sard-book-grid{{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;grid-auto-rows:1fr;align-items:stretch;gap:18px}}
#sard360-{style_slug}-shelf .sard-book-card{{display:flex!important;flex-direction:column!important;justify-content:space-between!important;align-items:stretch;height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important;min-width:0;padding:16px;background:#12151b;border:1px solid rgba(212,163,89,.34);border-radius:14px;box-shadow:0 12px 30px rgba(0,0,0,.28)}}
#sard360-{style_slug}-shelf .sard-book-cover-wrap{{display:flex;align-items:center;justify-content:center;flex:0 0 142px;width:100%;height:142px;min-width:0}}
#sard360-{style_slug}-shelf img.sard-book-cover{{display:block!important;width:94px!important;min-width:94px!important;max-width:94px!important;height:138px!important;min-height:138px!important;max-height:138px!important;object-fit:contain!important;border:1px solid rgba(212,163,89,.65);border-radius:8px;box-shadow:0 9px 22px rgba(0,0,0,.45)}}
#sard360-{style_slug}-shelf .sard-book-content{{display:flex!important;flex:1 1 auto;flex-direction:column!important;justify-content:space-between!important;align-items:stretch;height:auto!important;min-height:0!important;max-height:none!important;min-width:0;width:100%;overflow:visible!important;text-align:center}}
#sard360-{style_slug}-shelf .sard-book-kind{{margin:0 0 4px!important;padding:0!important;color:#d4a359;font-size:11px;line-height:1.5;text-align:center}}
#sard360-{style_slug}-shelf .sard-book-content h3{{display:block!important;height:auto!important;max-height:none!important;margin:0 0 5px!important;padding:0!important;border:0!important;box-shadow:none!important;background:none!important;color:#f3ead8;font-size:18px!important;line-height:1.45;text-align:center;overflow-wrap:anywhere}}
#sard360-{style_slug}-shelf .sard-book-author{{margin:0 0 8px!important;padding:0!important;color:#bdb5a8;font-size:12px;line-height:1.6;text-align:center;overflow-wrap:anywhere}}
#sard360-{style_slug}-shelf .sard-book-author [dir="ltr"]{{display:block;max-width:100%;margin-top:3px;font-size:11px;line-height:1.5;overflow-wrap:anywhere}}
#sard360-{style_slug}-shelf .sard-book-summary{{display:block!important;height:auto!important;max-height:none!important;overflow:visible!important;margin:0 0 14px!important;padding:0!important;color:#ded7cb;font-size:13px;line-height:1.8;text-align:center;overflow-wrap:anywhere;-webkit-line-clamp:unset!important}}
#sard360-{style_slug}-shelf .sard-book-cta{{display:inline-flex!important;position:static!important;visibility:visible!important;opacity:1!important;align-items:center;justify-content:center;align-self:center;flex:0 0 auto;margin-top:auto!important;min-width:154px;min-height:42px;padding:10px 16px;border:0;border-radius:999px;background:linear-gradient(135deg,#e6c66d,#c99a3a);box-shadow:0 8px 22px rgba(212,163,89,.2);color:#16130d;text-decoration:none;text-align:center;font-family:inherit;font-size:13px;font-weight:800;line-height:1.4;white-space:normal;transition:filter .2s ease,transform .2s ease}}
#sard360-{style_slug}-shelf .sard-book-cta:hover,#sard360-{style_slug}-shelf .sard-book-cta:focus-visible{{filter:brightness(1.08);transform:translateY(-1px)}}
#sard360-{style_slug}-shelf .sard-affiliate-disclosure{{display:block;width:100%;max-width:76ch;margin:18px auto 0!important;padding:12px 0 0!important;border-top:1px solid rgba(255,255,255,.08);color:#888!important;font-size:11px!important;text-align:center!important;direction:rtl;line-height:1.5!important;text-wrap:pretty;overflow-wrap:normal}}
@media(max-width:680px){{#sard360-{style_slug}-shelf .sard-book-grid{{grid-template-columns:1fr!important;grid-auto-rows:auto;gap:14px}}#sard360-{style_slug}-shelf .sard-book-card{{height:auto!important;min-height:0!important}}#sard360-{style_slug}-shelf .sard-book-content{{height:auto!important}}}}
@media(max-width:420px){{#sard360-{style_slug}-shelf{{padding:19px 14px}}#sard360-{style_slug}-shelf .sard-book-card{{padding:14px}}#sard360-{style_slug}-shelf img.sard-book-cover{{width:88px!important;min-width:88px!important;max-width:88px!important;height:132px!important;min-height:132px!important;max-height:132px!important}}#sard360-{style_slug}-shelf .sard-book-content h3{{font-size:17px!important}}#sard360-{style_slug}-shelf .sard-book-summary{{font-size:12px}}}}
</style>"""

def generate_markup(style_slug, shelf_title, books):
    articles_html = ""
    for b in books:
        articles_html += f"""
    <article class="sard-book-card" style="display:flex!important;box-sizing:border-box!important;flex-direction:column!important;justify-content:space-between!important;height:auto!important;min-height:unset!important;max-height:none!important;overflow:visible!important;">
      <div class="sard-book-cover-wrap" style="display:flex!important;align-items:center!important;justify-content:center!important;flex:0 0 auto!important;height:auto!important;min-height:unset!important;max-height:none!important;overflow:visible!important;">
        <img class="sard-book-cover" src="{b['image']}" alt="غلاف {b['title']}" loading="lazy" decoding="async">
      </div>
      <div class="sard-book-content">
        <p class="sard-book-kind">{b['kind']}</p>
        <h3>{b['title']}</h3>
        <p class="sard-book-author">{b['author']}</p>
        <p class="sard-book-summary">{b['summary']}</p>
        <a class="sard-book-cta" href="{b['url']}" target="_blank" rel="sponsored nofollow noopener">{b['cta']}</a>
      </div>
    </article>"""

    return f"""<section id="sard360-{style_slug}-shelf" aria-label="{shelf_title}" style="display:block!important;box-sizing:border-box!important;height:auto!important;min-height:unset!important;max-height:none!important;overflow:visible!important;">
  <p style="margin:0 0 8px;color:#d4a359;font-size:13px;letter-spacing:.06em;">الخزانة · سرد 360</p>
  <h2 style="margin:0 0 18px;color:#f3ead8;font-size:clamp(22px,3vw,30px);line-height:1.5;">{shelf_title}</h2>
  <div class="sard-book-grid" style="display:grid!important;box-sizing:border-box!important;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr))!important;grid-auto-rows:1fr!important;align-items:stretch!important;height:auto!important;min-height:unset!important;max-height:none!important;overflow:visible!important;">{articles_html}
  </div>
  <p class="sard-affiliate-disclosure">إفصاح: تحتوي هذه الترشيحات على روابط Amazon تابعة؛ قد تحصل منصّة سرد 360 على عمولة بسيطة عند الشراء من خلال هذه الروابط دون أي كلفة إضافية عليك. هذه الاختيارات تتبع بدقة معاييرنا الثقافية لخدمة القارئ المتلقي.</p>
</section>"""

def inject_shelf(raw_content, pid, data):
    style_slug = data["style_slug"]
    clean_content = re.sub(rf'(?is)<style id="sard360-{style_slug}-shelf-styles">.*?</style>\s*<section id="sard360-{style_slug}-shelf".*?</section>', '', raw_content)
    
    new_shelf_code = f"<!-- wp:html -->\n{generate_style(style_slug)}\n{generate_markup(style_slug, data['title'], data['books'])}\n<!-- /wp:html -->"
    anchor = data["anchor_header"]
    level = data["anchor_level"]
    
    pattern = rf'(<!--\s*wp:heading.*?-->\s*)?<h{level}\b[^>]*>(.*?)</h{level}>(\s*<!--\s*/wp:heading\s*-->)?'
    blocks = list(re.finditer(pattern, clean_content, re.I | re.S))
    insert_pos = None
    for m in blocks:
        if anchor in re.sub(r'<[^>]+>', '', m.group(2)).replace('\u00a0', ' ').strip():
            insert_pos = m.start()
            break
            
    if insert_pos is None:
        print(f"  [POST {pid}] Error: Could not find anchor heading: '{anchor}'")
        return None
    return clean_content[:insert_pos] + new_shelf_code + "\n\n" + clean_content[insert_pos:]

def main():
    registry_path = Path('scripts/articles_registry.json')
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    for pid, data in SHELVES_DATA.items():
        print(f"Processing Post {pid}...")
        r = session.get(f"{WP_BASE}/posts/{pid}?context=edit", timeout=30)
        if not r.ok: continue
        updated = inject_shelf(r.json().get('content', {}).get('raw', ''), pid, data)
        if not updated: continue
        r_update = session.post(f"{WP_BASE}/posts/{pid}", json={"content": updated}, timeout=60)
        if r_update.ok:
            print(f"  [POST {pid}] Success!")
            registry[str(pid)]["status"] = "treated"
            registry[str(pid)]["books_isbn"] = [b["url"].split('/dp/')[1].split('?')[0] for b in data["books"]]
        else: print(f"  [POST {pid}] Error: {r_update.status_code}")
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding='utf-8')

if __name__ == '__main__': main()
