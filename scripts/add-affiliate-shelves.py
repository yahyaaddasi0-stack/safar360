#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import requests
from pathlib import Path

# Configuration
WP_BASE = 'https://sard360.com/wp-json/wp/v2'
USERNAME = os.environ.get('SARD360_WP_USERNAME')
PASSWORD = os.environ.get('SARD360_WP_APPLICATION_PASSWORD')

if not USERNAME or not PASSWORD:
    print("Error: Missing WordPress credentials in environment variables SARD360_WP_USERNAME and SARD360_WP_APPLICATION_PASSWORD")
    sys.exit(1)

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers['Accept'] = 'application/json'

# Data for the 5 articles and their books
SHELVES_DATA = {
    4610: {
        "slug": "ubar-the-lost-atlantis-of-the-sands-empty-quarter",
        "style_slug": "ubar",
        "title": "لمواصلة التقصّي: مقتنيات من خزانة سرد حول أوبار وأتلانتس الرمال",
        "anchor_header": "أسطورة \"أوبار\" أو \"أتلانتس الصحراء\": نداء من غياهب الماضي",
        "books": [
            {
                "kind": "المرجع الأثري والرحلة",
                "title": "الطريق إلى أوبار",
                "author": "نيكولاس كلاب <span dir=\"ltr\">Nicholas Clapp</span>",
                "summary": "القصة الكاملة للرحلة المثيرة التي قادها نيكولاس كلاب للعثور على مدينة أوبار الضائعة، بالاستعانة بالتكنولوجيا الفضائية وتحليل خرائط الأقمار الصناعية لوكالة ناسا وبقايا المسالك الصحراوية القديمة.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0395957869.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0395957869?tag=sard360-20"
            },
            {
                "kind": "مذكرات الاستكشاف",
                "title": "أتلانتس الرمال",
                "author": "السير رانولف فاينز <span dir=\"ltr\">Sir Ranulph Fiennes</span>",
                "summary": "مذكرات وشهادة حية ومثيرة يرويها السير رانولف فاينز، أحد أعظم المغامرين في العصر الحديث، يستعرض فيها العقبات الجغرافية والظروف الجوية القاسية التي واجهت البعثة الميدانية في رمال الربع الخالي الشاسعة.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0451175778.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0451175778?tag=sard360-20"
            }
        ]
    },
    4585: {
        "slug": "hasan-sabbah-alamut-assassins-history-secrets",
        "style_slug": "hasan-sabbah",
        "title": "لمواصلة التقصّي: مقتنيات من خزانة سرد حول قلعة ألموت وحسن الصبّاح",
        "anchor_header": "ألموت: عش النسر الذي تحدى السلاطين",
        "books": [
            {
                "kind": "الرواية الأدبية",
                "title": "رواية ألموت",
                "author": "فلاديمير بارتول <span dir=\"ltr\">Vladimir Bartol</span>",
                "summary": "الرواية الكلاسيكية الشهيرة التي صاغت أسطورة الحشاشين وحسن الصباح؛ رحلة أدبية مذهلة تأخذك إلى داخل جدران القلعة لتكشف آليات التوجيه العقائدي وصناعة الفدائيين بأسلوب سردي بارع.",
                "cta": "اقتنِ الرواية من Amazon",
                "image": "https://www.northatlanticbooks.com/wp-content/uploads/books/alamut.png",
                "url": "https://www.amazon.com/dp/1588340732?tag=sard360-20"
            },
            {
                "kind": "الدراسة التاريخية",
                "title": "الحشاشون: طائفة إسماعيلية متطرفة في تاريخ الإسلام",
                "author": "برنارد لويس <span dir=\"ltr\">Bernard Lewis</span>",
                "summary": "الدراسة الأكاديمية والتاريخية الأبرز والموثقة التي تتناول أصول وجذور جماعة الحشاشين، مستعرضةً تنظيمهم السري الدقيق، وعلاقاتهم السياسية، وحقائق الاغتيالات التي زلزلت عروش الملوك والسلاطين.",
                "cta": "اقتنِ الدراسة من Amazon",
                "image": "https://www.hachettebookgroup.com/wp-content/uploads/2025/06/9780465004980.jpg",
                "url": "https://www.amazon.com/dp/0465004981?tag=sard360-20"
            }
        ]
    },
    4625: {
        "slug": "omar-ibn-said-arabic-manuscript-slavery-america",
        "style_slug": "omar",
        "title": "لمواصلة التقصّي: مقتنيات من خزانة سرد حول سيرة عمر بن سعيد وتاريخ المستعبدين",
        "anchor_header": "الجذور: من مجالس العلم في السنغال إلى غياهب المجهول",
        "books": [
            {
                "kind": "السيرة الذاتية (مصدر رئيسي)",
                "title": "مستعبد مسلم في أمريكا: سيرة ذاتية بقلم عمر بن سعيد",
                "author": "عمر بن سعيد (ترجمة وتحرير: علا العجيز) <span dir=\"ltr\">Omar Ibn Said (Ed: Ala Alryyes)</span>",
                "summary": "الوثيقة التاريخية الوحيدة المتبقية باللغة العربية التي كتبها مستعبد في أمريكا يروي فيها سيرته بنفسه. سيرة ذاتية نادرة ومؤثرة تقدم منظوراً حياً ومختلفاً يتحدى الرواية التقليدية للاستعباد.",
                "cta": "اقتنِ السيرة من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0299249549.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0299249549?tag=sard360-20"
            },
            {
                "kind": "دراسة تاريخية موثقة",
                "title": "عباد الرحمن: المسلمون الأفارقة المستعبدون في الأمريكيتين",
                "author": "سيلفيان أ. ديوف <span dir=\"ltr\">Sylviane A. Diouf</span>",
                "summary": "دراسة تاريخية شاملة ورائعة تكشف تفاصيل حياة وعقيدة وتأثير المسلمين الأفارقة الذين استُعبدوا في القارة الأمريكية، مبرزة كفاحهم المستميت للحفاظ على هويتهم الإسلامية وعلومهم في ظروف قاهرة.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/1479847119.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/1479847119?tag=sard360-20"
            }
        ]
    },
    4598: {
        "slug": "andalusias-cry-barbarossa-algerian-fleet-mediterranean",
        "style_slug": "barbarossa",
        "title": "لمواصلة التقصّي: مقتنيات من خزانة سرد حول أمجاد خير الدين بربروس وصراع المتوسط",
        "anchor_header": "بزوغ الفجر الأحمر: خير الدين وتلبية النداء",
        "books": [
            {
                "kind": "السيرة والتاريخ الملاحي",
                "title": "أمير البحر لدى السلطان: حياة خير الدين بربروس",
                "author": "إيرنل برادفورد <span dir=\"ltr\">Ernle Bradford</span>",
                "summary": "سيرة ذاتية تاريخية مشوقة ومفصلة تستعرض حياة القائد البحري الأسطوري خير الدين بربروس، منذ نشأته كبحار مغامر في بحر إيجة حتى صعوده كأعظم أدميرال في الأسطول العثماني وخصم مهيب للقوى الأوروبية.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/184511793X.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/184511793X?tag=sard360-20"
            },
            {
                "kind": "التاريخ العام والجيوسياسي",
                "title": "إمبراطوريات البحر: المعركة الختامية للسيادة على المتوسط",
                "author": "روجر كراولي <span dir=\"ltr\">Roger Crowley</span>",
                "summary": "كتاب مذهل يسرد تفاصيل الصراع الملحمي والشرس بين الدولة العثمانية والتحالفات المسيحية للسيطرة على البحر الأبيض المتوسط خلال القرن السادس عشر، مع تسليط الضوء على المعارك البحرية وحصار القلاع المنيعة.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0812977645.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0812977645?tag=sard360-20"
            }
        ]
    },
    4618: {
        "slug": "roald-amundsen-the-last-viking-south-pole-survival",
        "style_slug": "amundsen",
        "title": "لمواصلة التقصّي: مقتنيات من خزانة سرد حول رحلات القطب الجنوبي وروال أموندسن",
        "anchor_header": "التحول الكبير: خيانة الحلم وتوجيه البوصلة نحو المجهول",
        "books": [
            {
                "kind": "السيرة التاريخية",
                "title": "آخر الفايكنغ: حياة المغامر روال أموندسن",
                "author": "ستيفن ر. باون <span dir=\"ltr\">Stephen R. Bown</span>",
                "summary": "سيرة ذاتية عميقة وموثقة تكشف الجوانب النفسية والمهنية لروال أموندسن، وتستعرض ببراعة كيف مكّنه تخطيطه العسكري الصارم وانضباطه الشديد من هزم ظروف الطبيعة القاتلة وتحقيق إنجازات استكشافية فريدة.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0306820676.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0306820676?tag=sard360-20"
            },
            {
                "kind": "يوميات البعثة (مصدر رئيسي)",
                "title": "القطب الجنوبي: يوميات البعثة النرويجية على متن السفينة فرام",
                "author": "روال أموندسن <span dir=\"ltr\">Roald Amundsen</span>",
                "summary": "اليوميات والشهادة المباشرة لروال أموندسن نفسه، يسرد فيها تفاصيل الإعداد والمسار الشاق لعبور الحواجز الجليدية للوصول إلى النقطة الجغرافية الأقصى جنوب الأرض، كاشفاً تفاصيل الحياة اليومية للبعثة.",
                "cta": "اقتنِ الكتاب من Amazon",
                "image": "https://images-na.ssl-images-amazon.com/images/P/0815411278.01.LZZZZZZZ.jpg",
                "url": "https://www.amazon.com/dp/0815411278?tag=sard360-20"
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
#sard360-{style_slug}-shelf .sard-book-content h3:before,#sard360-{style_slug}-shelf .sard-book-content h3:after{{display:none!important;content:none!important}}
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
    
    # 1. Check if the shelf is already present. If yes, strip any existing style + section block to prevent duplicates.
    pattern_existing = rf'(?is)<style id="sard360-{style_slug}-shelf-styles">.*?</style>\s*<section id="sard360-{style_slug}-shelf".*?</section>'
    clean_content, count = re.subn(pattern_existing, '', raw_content)
    if count > 0:
        print(f"  [POST {pid}] Found and removed {count} pre-existing shelf/style block(s).")
    
    # Generate new block
    style_block = generate_style(style_slug)
    markup_block = generate_markup(style_slug, data["title"], data["books"])
    new_shelf_code = f"<!-- wp:html -->\n{style_block}\n{markup_block}\n<!-- /wp:html -->"
    
    # 2. Locate insertion anchor using robust heading matching (stripping <strong> etc)
    anchor = data["anchor_header"]
    blocks = list(re.finditer(r'(<!--\s*wp:heading\b.*?-->\s*)?<h3\b[^>]*>(.*?)</h3>(\s*<!--\s*/wp:heading\s*-->)?', clean_content, re.I | re.S))
    insert_pos = None
    for m in blocks:
        full_text = m.group(2)
        # strip all HTML tags like <strong> inside the h3 content
        cleaned_text = re.sub(r'<[^>]+>', '', full_text).strip()
        if cleaned_text == anchor:
            insert_pos = m.start()
            break
            
    if insert_pos is None:
        print(f"  [POST {pid}] Error: Could not find anchor heading: '{anchor}' in content.")
        return None
            
    updated_content = clean_content[:insert_pos] + new_shelf_code + "\n\n" + clean_content[insert_pos:]
    print(f"  [POST {pid}] Successfully injected new shelf block at character position {insert_pos}.")
    return updated_content

def main():
    print("--- STARTING AFFILIATE SHELVES INJECTION ---")
    for pid, data in SHELVES_DATA.items():
        print(f"\nProcessing Post {pid} ({data['slug']})...")
        try:
            # Fetch post
            r = session.get(f"{WP_BASE}/posts/{pid}?context=edit", timeout=30)
            if r.status_code != 200:
                print(f"  [POST {pid}] Error: HTTP {r.status_code} while fetching.")
                print(r.text[:500])
                continue
                
            post_data = r.json()
            raw_content = post_data.get('content', {}).get('raw', '')
            
            # Inject
            updated_content = inject_shelf(raw_content, pid, data)
            if updated_content is None:
                continue
                
            # Update post
            update_payload = {"content": updated_content}
            r_update = session.post(f"{WP_BASE}/posts/{pid}", json=update_payload, timeout=60)
            if r_update.status_code == 200:
                d = r_update.json()
                print(f"  [POST {pid}] Success! Post updated. Slug: '{d.get('slug')}', Chars: {len(updated_content)}")
            else:
                print(f"  [POST {pid}] Error during update: HTTP {r_update.status_code}")
                print(r_update.text[:800])
                
        except Exception as e:
            print(f"  [POST {pid}] Exception: {type(e).__name__}: {str(e)}")

if __name__ == '__main__':
    main()
