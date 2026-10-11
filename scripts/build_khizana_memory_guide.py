#!/usr/bin/env python3
"""Build the standalone WordPress/Elementor HTML for the Khizana memory-cabinet guide."""
from __future__ import annotations
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'products.json').read_text(encoding='utf-8'))
PUBLIC_ASSET_BASE = 'https://safar360-alpha.vercel.app/'
PAGE_URL = 'https://sard360.com/khizana/memory-cabinet-10-classic-objects/'
TITLE = 'خزانة الذاكرة: 10 مقتنيات كلاسيكية تمنح مكتبتك روح العصور التاريخية'
DESCRIPTION = 'جولة تحريرية في عشرة كتب وأدوات ومقتنيات للقراءة والكتابة، مع معلومات منتجات مضبوطة وصور حقيقية وروابط المتجر.'

EDITORIAL = {
    'master-astrolabe': ('الأسطرلاب النحاسي العربي الطابع', 'بين الأرفف الخشبية، يقف هذا الأسطرلاب الزخرفي استلهاماً لتوق الإنسان القديم إلى فك طلاسم السماء. يلتقط النحاس ضوء الغرفة الخافت، وتستدعي نقوشه رحلة الفكر في الكون؛ حضوره يحوّل المكتبة إلى مرصد فلسفي في المخيلة، ويذكّرنا بأننا ذرات عابرة تتأمل ليل السماء. إنها قطعة للعرض والإلهام، لا أثر أندلسي موثّق ولا أداة معايرة عملية.', 'نسخة نحاسية للعرض؛ ارتفاع يقارب 8.5 بوصة مع الحلقة وخمس صفائح قابلة للفك بحسب وصف القائمة.'),
    'master-leather-journal': ('دفتر اليوميات الجلدي المجلّد يدوياً', 'يستحضر هذا الدفتر عمق درجات المغرة الترابية ودفء المخطوطات القديمة. صفحاته غير المسطّرة تترك فسحة لانسكاب الحبر والهوامش والأفكار التي لا تستعجل اكتمالها. ملمس الغلاف الجلدي وصفحات القطن والجوت، كما يصفها المصنّع، يحوّلان الكتابة اليومية إلى طقس من البطء؛ وعند تدوين الخواطر يصير الدفتر وعاءً حميماً للذاكرة الشخصية ومقاومة النسيان.', '240 صفحة؛ يصف المصنّع الورق بأنه من القطن والجوت وخالٍ من الأحماض، ولا يحدد وزناً له.'),
    'books-15': ('التأملات — ماركوس أوريليوس', 'أن تضع كلمات الإمبراطور الرواقي في مكتبتك هو أن تستدعي الحكمة الصارمة وسط فوضى العالم الحديث. نصوص دوّنها أوريليوس لنفسه عن الواجب والرزانة وتقلب الحياة؛ وجودها على الطاولة يوجّه بوصلة العقل نحو الداخل، حيث تتشكل القوة بعيداً عن صخب الزائل. هذه طبعة فاخرة باللغة الإنجليزية، ولا ننسب إليها نوع تجليد غير مثبت.', 'الطبعة المعروضة باللغة الإنجليزية؛ تحقّق من وصف مادة التجليد لدى البائع قبل الطلب.'),
    'master-hourglass-black-sand': ('الساعة الرملية الخشبية ذات الرمال السوداء', 'سقوط ذرات الرمل الأسود بإيقاع منتظم يخلق مشهداً بصرياً يجسّد انقضاء اللحظة. هيكلها الخشبي، كما يصفه البائع، يضفي على المكتب دفئاً ظليلاً؛ وتصبح الساعة تذكيراً فلسفياً بالحاضر ورفيقة لجلسة قراءة أو كتابة. إنها تمنح الوقت هيئةً مرئية، لكن مدتها الاسمية لا تجعلها أداة توقيت دقيقة.', 'إطار خشبي ورمل أسود ومدة اسمية قدرها 60 دقيقة وفق قائمة المنتج.'),
    'master-pilot-falcon-pen': ('قلم الحبر السائل ذو الريشة الذهبية', 'هناك سحر في انزلاق الريشة على الورق، تاركةً وراءها نهراً دقيقاً من الحبر. يستدعي القلم الأسود هيئة أدوات الروائيين الكلاسيكيين، ويمنح فعل الكتابة حضوراً أبطأ من التدوين الآلي؛ عند إمساكه تصبح الرسالة أو الخاطرة طقساً إبداعياً له إيقاعه الخاص. تصف مواصفات هذا الطراز جسمه المعدني المطلي وريشته المرنة من الذهب عيار 14 قيراطاً.', 'جسم معدني مطلي وريشة Pilot مرنة من ذهب 14 قيراطاً بحسب صفحة بائع الأقلام.'),
    'master-vintage-globe': ('مجسم الكرة الأرضية بخريطة سيبيا ذات طابع عتيق', 'بدرجات السيبيا والبني الدافئ، تقف الكرة الأرضية كنافذة مصغّرة على الجغرافيا وحكايات الرحلة. تدويرها يفتح أفق الكاتب على اتساع العالم، ويستفز المخيلة لنسج حكايات تعبر المحيطات والقارات. الخريطة ذات مظهر كلاسيكي، لكن المجسم منتج حديث؛ لذلك نورد مادته وأبعادَه وفق وصف البائع، لا بوصفها وثيقة من عصر الاستكشافات.', 'قطر الكرة نحو 8 بوصات والارتفاع الكلي قرابة 14 بوصة؛ يذكر البائع كرة بلاستيكية وحاملاً بمواد متعددة.'),
    'master-roorkee-magnifier': ('عدسة مكبرة بمقبض بلون النحاس', 'تمنح هذه القطعة هيئة المحقق التاريخي الذي ينقّب بين السطور بحثاً عن حقيقة غائبة. وضعها فوق خريطة أو صفحة يقرّب العين من التفاصيل، ويضيف إلى المكتب لمسة تستحضر مشاهد التحقيق الفيكتورية. إنها تدرب العين على ملاحظة الجزئيات وتحيل القراءة إلى فعل استكشافي؛ ومقبضها بلون النحاس كما يورده وصف المنتج، لا من العظم الطبيعي.', 'عدسة بتكبير 5× ومقبض بلون النحاس وفق قائمة المنتج.'),
    'master-sujun-candelabra': ('شمعدان نحاسي ثلاثي الأذرع', 'لا تكتمل طقوس القراءة المسائية من دون ضوء دافئ. يمنح هذا الشمعدان الثلاثي زوايا المكتبة ظلالاً تتراقص على ظهور الكتب؛ ومع الشموع المناسبة، يصير المشهد أقرب إلى لوحة مسرحية صغيرة. المنتج من الحديد بتشطيب بلون النحاس المعتّق، لا من النحاس الصلب، ولا ننسب إلى تصميمه تاريخاً محدداً.', 'شمعدان حديدي بثلاثة أذرع وتشطيب بلون النحاس المعتّق بحسب وصف القائمة.'),
    'books-16': ('دون كيشوت — ميغيل دي ثيربانتس', 'أن تستقر قصة فارس لامانشا على الرف هو انحيازٌ للحالمين. يجاور الحلمُ السخريةَ والواقعَ اليومي في مغامرات دون كيشوت وسانشو بانثا؛ ويحضر العمل بطاقة التمرد النبيل على العالم الرمادي، مذكّراً القارئ، كلما اختلس النظر إلى غلافه، بضرورة الإيمان بالخيال. هذه نسخة قماشية من Penguin باللغة الإنجليزية، بترجمة John Rutherford.', 'Penguin Clothbound Classics؛ إصدار 2018، 1056 صفحة، باللغة الإنجليزية.'),
    'master-wax-seal-a': ('ختم شمعي كلاسيكي بحرف A', 'ذوبان الشمع العنابي وسقوطه على الورق يمنح المراسلة لحظة حسية تحتفظ بها الذاكرة. يعيد الختم للرسالة شيئاً من هيبتها القديمة؛ وحين يُستخدم مع شمع مناسب، لا يغلق ورقة فحسب، بل يترك بصمة شخصية على أثر الكلمات. هذا العرض لختم مفرد بحرف A ومقبض خشبي بحسب القائمة، ولا نفترض وجود شمع أو رؤوس قابلة للتبديل.', 'ختم مفرد بحرف A بمقبض خشبي ورأس معدني وفق وصف المنتج.'),
}

ORDER = [
    'master-astrolabe', 'master-leather-journal', 'books-15',
    'master-hourglass-black-sand', 'master-pilot-falcon-pen', 'master-vintage-globe',
    'master-roorkee-magnifier', 'master-sujun-candelabra', 'books-16', 'master-wax-seal-a'
]
all_items = {item['id']: item for item in [*CATALOG['master_items'], *CATALOG['books']]}
assert len(ORDER) == 10 and set(ORDER) == set(EDITORIAL)
assert all(key in all_items for key in ORDER), 'Missing catalog item'


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def absolute_image(item: dict) -> str:
    value = item['image_url']
    if value.startswith(('https://', 'http://')):
        return value
    return PUBLIC_ASSET_BASE + value.lstrip('/')


def product_schema(item: dict) -> dict:
    kind = 'Book' if item['id'].startswith('books-') else 'Product'
    url = item['affiliate_url']
    if 'tag=sard360-20' not in url:
        raise ValueError(f"Missing affiliate tag: {item['id']}")
    node = {
        '@type': kind,
        '@id': PAGE_URL + '#' + item['id'],
        'name': item['title'],
        'description': EDITORIAL[item['id']][1],
        'image': absolute_image(item),
        'url': url,
        'offers': {'@type': 'Offer', 'url': url, 'availability': 'https://schema.org/InStock'}
    }
    if kind == 'Book':
        node['author'] = {'@type': 'Person', 'name': item['author']}
        node['isbn'] = item['isbn']
        node['inLanguage'] = item.get('language', 'en')
        node['publisher'] = {'@type': 'Organization', 'name': item.get('publisher', '')}
    else:
        node['category'] = item['category']
    return node


def card(item_id: str, index: int) -> str:
    item = all_items[item_id]
    narrative_title, narrative, specs = EDITORIAL[item_id]
    image = absolute_image(item)
    url = item['affiliate_url']
    if 'tag=sard360-20' not in url:
        raise ValueError(f"Missing tag on {item_id}")
    label = 'اقتنِ النسخة' if item_id.startswith('books-') else 'اكتشف لدى Amazon'
    language = ' lang="en"' if item_id.startswith('books-') else ''
    return f'''<article class="skm-card{' skm-book' if item_id.startswith('books-') else ''}" id="{esc(item_id)}" aria-labelledby="{esc(item_id)}-title">
      <div class="skm-card-copy">
        <p class="skm-card-kicker">{index:02d} <span aria-hidden="true">/</span> {esc(item['category'])}</p>
        <h2 id="{esc(item_id)}-title"{language}>{esc(narrative_title)}</h2>
        <p class="skm-story">{esc(narrative)}</p>
        <p class="skm-fact"><span>تفاصيل الانتقاء</span>{esc(specs)}</p>
        <a class="skm-button" href="{esc(url)}" target="_blank" rel="sponsored nofollow noopener noreferrer" aria-label="{esc(label)}: {esc(narrative_title)}">
          <span>{label}</span><span aria-hidden="true">↗</span>
        </a>
      </div>
      <div class="skm-product-image"><img src="{esc(image)}" alt="{esc(narrative_title)}" width="800" height="800" loading="lazy" decoding="async"></div>
    </article>'''

items_html = []
for i, item_id in enumerate(ORDER, start=1):
    items_html.append(card(item_id, i))
    if i == 4:
        items_html.append('''<figure class="skm-interlude">
          <img src="https://sard360.com/wp-content/uploads/2026/10/books_on_library_shelves_2k_20261010194410.jpg" alt="رفوف كتب تمتد في مكتبة دافئة الإضاءة" loading="lazy" decoding="async">
          <figcaption><span>ذاكرة تُرتّب على الرف</span><blockquote>تكتسب المكتبة شخصيتها من الكتب التي نعود إليها، ومن الأشياء التي تمنح القراءة مكاناً وزمناً.</blockquote></figcaption>
        </figure>''')
    if i == 7:
        items_html.append('''<figure class="skm-interlude skm-interlude--desk">
          <img src="https://sard360.com/wp-content/uploads/2026/10/journal_and_hourglass_on_desk_2k_20261010194317.jpg" alt="دفتر وساعة رملية على مكتب للكتابة" loading="lazy" decoding="async">
          <figcaption><span>طقسٌ صغير للكتابة</span><blockquote>قلمٌ وورقٌ ووقتٌ محدد: تفاصيل بسيطة تساعد على أن يصبح التدوين عادةً قابلة للعودة.</blockquote></figcaption>
        </figure>''')
    if i == 9:
        items_html.append('''<figure class="skm-interlude skm-interlude--typewriter">
          <img src="https://sard360.com/wp-content/uploads/2026/10/antique_typewriter_on_rustic_workbench_2k_20261010194412.jpg" alt="آلة كاتبة عتيقة على منضدة خشبية" loading="lazy" decoding="async">
          <figcaption><span>أثرٌ يبقى بعد الحكاية</span><blockquote>رسالة مختومة أو سطر مكتوب بعناية؛ لكل فكرة طريقة مادية تترك لها أثراً.</blockquote></figcaption>
        </figure>''')

article_node = {
    '@type': 'Article',
    '@id': PAGE_URL + '#article',
    'headline': TITLE,
    'description': DESCRIPTION,
    'inLanguage': 'ar',
    'mainEntityOfPage': {'@id': PAGE_URL},
    'author': {'@type': 'Organization', 'name': 'Sard360', 'url': 'https://sard360.com/'},
    'publisher': {'@type': 'Organization', 'name': 'Sard360', 'url': 'https://sard360.com/'},
    'image': ['https://sard360.com/wp-content/uploads/2026/10/brass_compass_on_sea_chart_2k_20261010194411.jpg']
}
item_list = {
    '@type': 'ItemList',
    '@id': PAGE_URL + '#curated-items',
    'name': 'عشرة مقتنيات وكتب من الخزانة',
    'numberOfItems': 10,
    'itemListElement': [
        {'@type': 'ListItem', 'position': i, 'item': product_schema(all_items[item_id])}
        for i, item_id in enumerate(ORDER, start=1)
    ]
}
schema = {'@context': 'https://schema.org', '@graph': [article_node, item_list]}
schema_text = json.dumps(schema, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')

html_doc = f'''<style>
#sard360-khizana-memory{{--skm-bg:#101112;--skm-panel:#17191b;--skm-gold:#d4af62;--skm-cream:#f1eadc;--skm-text:#f3f0e8;--skm-muted:#b7b6b1;position:relative;left:50%;width:100vw;max-width:100vw;transform:translateX(-50%);overflow:hidden;background:radial-gradient(ellipse at 14% 4%,rgba(174,125,48,.16),transparent 36rem),radial-gradient(ellipse at 92% 33%,rgba(57,83,94,.12),transparent 34rem),var(--skm-bg);color:var(--skm-text);font-family:Tahoma,Arial,"Noto Sans Arabic",sans-serif;line-height:1.85;-webkit-font-smoothing:antialiased}}
#sard360-khizana-memory *{{box-sizing:border-box}}
#sard360-khizana-memory a{{color:inherit}}
.skm-shell{{width:min(100% - 40px,1260px);margin-inline:auto;padding:28px 0 64px}}
.skm-nav{{display:flex;justify-content:space-between;align-items:center;gap:16px;padding-bottom:17px;border-bottom:1px solid rgba(212,175,98,.25);font-size:11px;color:var(--skm-muted)}}
.skm-nav a{{text-decoration:none;color:var(--skm-gold)}}
.skm-hero{{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(300px,.95fr);align-items:center;gap:clamp(26px,5vw,72px);padding:clamp(38px,7vw,88px) 0 48px}}
.skm-kicker{{display:flex;align-items:center;gap:10px;margin:0 0 14px;color:var(--skm-gold);font-size:11px;font-weight:700;letter-spacing:.08em}}
.skm-kicker:before{{content:"";width:28px;height:1px;background:var(--skm-gold)}}
.skm-hero h1{{max-width:720px;margin:0;font-family:Georgia,"Times New Roman",serif;font-size:clamp(38px,6vw,74px);font-weight:400;line-height:1.25;letter-spacing:-.025em}}
.skm-hero h1 em{{color:#e1c886;font-style:normal}}
.skm-lead{{max-width:690px;margin:22px 0 0;color:#d1cec6;font-size:15px;line-height:2.1}}
.skm-hero-visual{{position:relative;min-height:320px;overflow:hidden;border:1px solid rgba(212,175,98,.28);border-radius:22px;background:#28231b;box-shadow:0 25px 70px rgba(0,0,0,.38)}}
.skm-hero-visual:after{{content:"";position:absolute;inset:35% 0 0;background:linear-gradient(transparent,rgba(9,10,11,.72));pointer-events:none}}
.skm-hero-visual img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center}}
.skm-hero-caption{{position:absolute;z-index:1;right:22px;bottom:18px;color:#f3ead6;font-size:11px}}
.skm-intro{{max-width:890px;margin:0 auto 54px;padding:22px 26px;border-right:2px solid var(--skm-gold);background:linear-gradient(90deg,rgba(212,175,98,.045),rgba(212,175,98,.105));color:#cfccc4;font-family:Georgia,"Times New Roman",serif;font-size:17px;line-height:2.05}}
.skm-section-head{{display:flex;justify-content:space-between;align-items:end;gap:20px;margin:0 0 22px;padding-bottom:13px;border-bottom:1px solid rgba(212,175,98,.22)}}
.skm-section-head h2{{margin:0;font-family:Georgia,"Times New Roman",serif;font-size:clamp(24px,3vw,34px);font-weight:400}}
.skm-section-head p{{margin:0;color:var(--skm-muted);font-size:11px}}
.skm-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
.skm-card{{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(145px,.8fr);min-height:310px;overflow:hidden;border:1px solid rgba(255,255,255,.08);border-radius:18px;background:linear-gradient(145deg,rgba(29,31,32,.97),rgba(20,21,22,.98));box-shadow:0 16px 38px rgba(0,0,0,.2);transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease}}
.skm-card:hover{{transform:translateY(-3px);border-color:rgba(212,175,98,.45);box-shadow:0 22px 44px rgba(0,0,0,.3),0 0 25px rgba(212,175,98,.05)}}
.skm-card-copy{{display:flex;flex-direction:column;align-items:flex-start;padding:22px 22px 20px}}
.skm-card-kicker{{margin:0 0 7px;color:var(--skm-gold);font-size:10px;font-weight:700}}
.skm-card-kicker span{{padding-inline:5px;color:#77766f}}
.skm-card h2{{margin:0 0 10px;font-family:Georgia,"Times New Roman",serif;font-size:clamp(19px,2vw,24px);font-weight:400;line-height:1.55}}
.skm-story{{margin:0 0 12px;color:#c0bfb9;font-size:12px;line-height:1.95}}
.skm-fact{{margin:0 0 17px;color:#9e9d97;font-size:10px;line-height:1.75}}
.skm-fact span{{display:block;margin-bottom:2px;color:#dbc47d;font-weight:700}}
.skm-button{{display:inline-flex;align-items:center;justify-content:space-between;gap:16px;width:100%;min-height:43px;margin-top:auto;border:1px solid rgba(212,175,98,.66);border-radius:9px;padding:10px 13px;background:linear-gradient(110deg,#c49a4d,#e0c77f);color:#17140d!important;font-size:11px;font-weight:700;text-decoration:none;transition:filter .2s ease,transform .2s ease}}
.skm-button:hover{{filter:brightness(1.08);transform:translateY(-1px)}}
.skm-button span:last-child{{font-size:17px;line-height:1}}
.skm-product-image{{display:flex;align-items:center;justify-content:center;min-width:0;min-height:100%;padding:14px;background:#eee9dd}}
.skm-product-image img{{display:block;width:100%;height:100%;max-height:290px;object-fit:contain}}
.skm-book .skm-product-image img{{max-height:300px}}
.skm-interlude{{position:relative;grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1.2fr) minmax(240px,.8fr);align-items:center;gap:28px;min-height:250px;margin:8px 0;overflow:hidden;border:1px solid rgba(212,175,98,.22);border-radius:18px;background:#17191a}}
.skm-interlude img{{display:block;width:100%;height:260px;object-fit:cover}}
.skm-interlude figcaption{{padding:22px 26px}}
.skm-interlude figcaption span{{color:var(--skm-gold);font-size:10px;font-weight:700}}
.skm-interlude blockquote{{margin:9px 0 0;font-family:Georgia,"Times New Roman",serif;font-size:clamp(18px,2.3vw,25px);line-height:1.75;color:#e0ddd5}}
.skm-interlude--desk img{{object-position:center 52%}}
.skm-interlude--typewriter img{{object-position:center 56%}}
.skm-truth-note{{margin:28px 0 0;padding:14px 17px;border:1px solid rgba(212,175,98,.18);border-radius:12px;color:#aaa9a3;background:rgba(255,255,255,.025);font-size:10px;line-height:1.8}}
.skm-end{{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-top:46px;padding-top:18px;border-top:1px solid rgba(212,175,98,.22);color:#85847f;font-size:10px}}
.skm-end a{{color:var(--skm-gold);text-decoration:none}}
.skm-disclosure{{margin:14px 0 0;text-align:center;color:#777773;font-size:10px;line-height:1.7}}
@media(max-width:900px){{.skm-hero{{grid-template-columns:1fr;gap:28px}}.skm-hero-visual{{min-height:280px}}.skm-grid{{grid-template-columns:1fr}}.skm-card{{min-height:280px}}}}
@media(max-width:620px){{.skm-shell{{width:min(100% - 28px,1260px);padding-top:16px}}.skm-nav{{font-size:10px}}.skm-hero{{padding:42px 0 32px}}.skm-lead{{font-size:14px}}.skm-hero-visual{{min-height:220px}}.skm-intro{{margin-bottom:38px;padding:17px 18px;font-size:15px}}.skm-section-head{{align-items:flex-start;flex-direction:column;gap:5px}}.skm-card{{display:flex;flex-direction:column-reverse;min-height:0}}.skm-product-image{{width:100%;height:230px;min-height:230px;padding:12px}}.skm-product-image img{{max-height:210px}}.skm-card-copy{{padding:18px}}.skm-card h2{{font-size:22px}}.skm-interlude{{grid-template-columns:1fr;gap:0}}.skm-interlude img{{height:200px}}.skm-interlude figcaption{{padding:17px 18px 20px}}.skm-interlude blockquote{{font-size:19px}}.skm-end{{align-items:flex-start;flex-direction:column;gap:8px}}}}
@media(prefers-reduced-motion:reduce){{#sard360-khizana-memory *,#sard360-khizana-memory *:before,#sard360-khizana-memory *:after{{scroll-behavior:auto!important;transition-duration:.01ms!important;animation-duration:.01ms!important}}}}
</style>
<main id="sard360-khizana-memory" dir="rtl" lang="ar">
  <div class="skm-shell">
    <nav class="skm-nav" aria-label="التنقل داخل الخزانة"><a href="https://sard360.com/khizana/">← الخزانة</a><span>دليل مقتنيات · سرد360</span></nav>
    <header class="skm-hero">
      <div><p class="skm-kicker">من مقتنيات الخزانة</p><h1>خزانة الذاكرة:<br><em>10 مقتنيات كلاسيكية</em> تمنح مكتبتك روح العصور التاريخية</h1><p class="skm-lead">جولة بين أدوات الرصد والكتابة والقراءة، وكتبٍ تصحب أسئلة الفلسفة والخيال. لكل قطعة حكايتها، ولكل اختيار حدوده ومواصفاته كما يوردها ناشره أو بائعه.</p></div>
      <figure class="skm-hero-visual"><img src="https://sard360.com/wp-content/uploads/2026/10/brass_compass_on_sea_chart_2k_20261010194411.jpg" alt="بوصلة نحاسية فوق خريطة بحرية قديمة" width="1200" height="900" fetchpriority="high"><figcaption class="skm-hero-caption">من الرحلة تبدأ الحكاية</figcaption></figure>
    </header>
    <p class="skm-intro">في زاوية الغرفة، حيث يتسلل ضوء الظهيرة ليخلق تبايناً درامياً بين النور والعتمة، تقف المكتبة كحارس صامت للزمن. هنا، لا تقتصر الأشياء على وظيفتها المادية؛ بل تتحول إلى بوابات تعبر بنا نحو حيوات مضت. رائحة الورق المعتّق، ملمس الجلد المتشقق، ولمعان النحاس الذي كسته أكسدة الأيام بلون الصدأ والمغرة، كلها تهمس بقصص لم تُروَ. الإنسان والمكان يلتحمان في طقس تأملي، حيث كل قطعة عتيقة تعيد هندسة الفراغ، لتجعل من العزلة ملاذاً يفيض بالسكينة، ومن الخزانة ذاكرة حية تنبض بروح العصور.</p>
    <section aria-labelledby="skm-items-title"><div class="skm-section-head"><h2 id="skm-items-title">عشرة اختيارات من الخزانة</h2><p>كتب وأدوات ومقتنيات لركن القراءة</p></div>
      <div class="skm-grid">{''.join(items_html)}</div>
    </section>
    <p class="skm-truth-note">تُذكر الخامات والمقاسات والميزات وفق بيانات الناشر أو البائع المتاحة وقت إعداد الدليل، وقد تتغير بين الإصدارات أو تحديثات القائمة. تحقّق من تفاصيل النسخة المعروضة قبل الشراء. بعض العناصر نسخ زخرفية وليست أدوات أثرية أو قياساً مهنياً.</p>
    <footer class="skm-end"><a href="https://sard360.com/khizana/">العودة إلى الخزانة</a><span>الخزانة — من سرد360</span></footer>
    <p class="skm-disclosure">إفصاح: تحتوي هذه الصفحة على روابط Amazon تابعة؛ قد تحصل سرد360 على عمولة عند الشراء من دون تكلفة إضافية عليك.</p>
  </div>
</main>
<script type="application/ld+json">{schema_text}</script>
'''

out = ROOT / 'wordpress' / 'khizana-memory-cabinet.html'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html_doc, encoding='utf-8')
print(json.dumps({'output': str(out), 'cards': len(ORDER), 'schema_types': ['Article', 'ItemList', 'Product', 'Book'], 'bytes': out.stat().st_size}, ensure_ascii=False))
