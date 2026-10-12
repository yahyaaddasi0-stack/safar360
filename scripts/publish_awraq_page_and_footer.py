#!/usr/bin/env python3
"""Publish the reviewed Awraq Sard shortcode and canonical global footer navigation."""
import argparse, hashlib, json, os
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
BASE='https://sard360.com/wp-json'
PAGE_ID=2964
SHORTCODE_ID=19
FOOTER_NAME='Sard360 Footer — canonical Awraq and Cinema categories'
SHORTCODE_FILE=ROOT/'wordpress/awraq-sard-shortcode.php'
FOOTER_FILE=ROOT/'wordpress/sard360-footer-categories.php'

parser=argparse.ArgumentParser()
parser.add_argument('--dry-run',action='store_true')
args=parser.parse_args()
for path in (SHORTCODE_FILE,FOOTER_FILE):
    if not path.is_file() or path.stat().st_size<1000: raise SystemExit(f'Missing or incomplete source: {path.name}')
shortcode=SHORTCODE_FILE.read_text(encoding='utf-8')
footer=FOOTER_FILE.read_text(encoding='utf-8')
if "add_shortcode('awraq_sard_main_page'" not in shortcode: raise SystemExit('Shortcode registration missing.')
if 'footer-sard-root' not in footer or 'cat-awraq/history' not in footer or 'sard360.com/cinema/?category=' not in footer: raise SystemExit('Footer route mapping failed local verification.')
if any(line.strip().startswith('تتجدّد هذه الترشيحات عشوائياً') for line in shortcode.splitlines()): raise SystemExit('Internal rotation note must never be public.')

session=requests.Session()
session.auth=(os.environ['SARD360_WP_USERNAME'],os.environ['SARD360_WP_APPLICATION_PASSWORD'])
session.headers.update({'User-Agent':'Sard360-Awraq-Publisher/1.0','Cache-Control':'no-cache'})

def get_json(url,**kwargs):
    r=session.get(url,timeout=35,**kwargs);r.raise_for_status();return r.json()

page=get_json(f'{BASE}/wp/v2/pages/{PAGE_ID}',params={'context':'edit'})
raw=(page.get('content') or {}).get('raw','')
if page.get('slug')!='awraq-sard' or '[awraq_sard_main_page]' not in raw:
    raise SystemExit('Awraq page no longer calls the expected shortcode; refusing to publish.')
current=get_json(f'{BASE}/code-snippets/v1/snippets/{SHORTCODE_ID}')
if current.get('name')!='[awraq_sard_main_page]' or not current.get('active'):
    raise SystemExit('Expected active shortcode snippet not found.')
old_code=current.get('code','')
if not old_code or 'add_shortcode' not in old_code:
    raise SystemExit('Shortcode source baseline is not valid.')
old_hash=hashlib.sha256(old_code.encode()).hexdigest()
all_snippets=get_json(f'{BASE}/code-snippets/v1/snippets')
footer_existing=next((x for x in all_snippets if x.get('name')==FOOTER_NAME),None)

archive_urls=[
 'https://sard360.com/cat-awraq/afaq/','https://sard360.com/cat-awraq/athar/',
 'https://sard360.com/cat-awraq/artsl/','https://sard360.com/cat-awraq/history/',
 'https://sard360.com/cat-awraq/anthropology/','https://sard360.com/cat-awraq/philosophy/',
 'https://sard360.com/cat-awraq/musicology/',
]
preflight=[]
for url in archive_urls:
    r=requests.get(url,timeout=28,headers={'Cache-Control':'no-cache'})
    preflight.append({'url':url,'status':r.status_code})
    if r.status_code!=200: raise SystemExit(f'Category archive did not return 200: {url} ({r.status_code})')

summary={'dry_run':args.dry_run,'page_id':PAGE_ID,'page_slug':page['slug'],'page_permalink':page['link'],'shortcode_id':SHORTCODE_ID,'posts_rendered_server_side':True,'official_awraq_categories':7,'cinema_categories':6,'footersnippet_existing':footer_existing.get('id') if footer_existing else None,'source_bytes':{'awraq':SHORTCODE_FILE.stat().st_size,'footer':FOOTER_FILE.stat().st_size},'archives_http':preflight,'original_shortcode_sha256':old_hash}
if args.dry_run:
    print(json.dumps(summary,ensure_ascii=False));raise SystemExit(0)

# Re-read the shortcode to avoid replacing another editor's later changes.
latest=get_json(f'{BASE}/code-snippets/v1/snippets/{SHORTCODE_ID}')
if hashlib.sha256(latest.get('code','').encode()).hexdigest()!=old_hash:
    raise SystemExit('Shortcode changed after review; refusing to overwrite newer edits.')
updated=session.post(f'{BASE}/code-snippets/v1/snippets/{SHORTCODE_ID}',json={'code':shortcode},timeout=50)
updated.raise_for_status()
check=get_json(f'{BASE}/code-snippets/v1/snippets/{SHORTCODE_ID}')
if check.get('code')!=shortcode or not check.get('active'):
    raise SystemExit('Awraq shortcode update did not persist as active.')

footer_payload={'name':FOOTER_NAME,'desc':'Canonical footer links for the seven Awraq subjects and six Cinema playlists; supports direct category selection.','code':footer,'tags':['Sard360','footer','navigation'],'scope':'global','condition_id':0,'active':True,'priority':20,'network':False,'shared_network':False}
if footer_existing:
    foot_id=int(footer_existing['id'])
    fresh=get_json(f'{BASE}/code-snippets/v1/snippets/{foot_id}')
    if fresh.get('name')!=FOOTER_NAME: raise SystemExit('Footer snippet identity changed; refusing to update.')
    saved=session.post(f'{BASE}/code-snippets/v1/snippets/{foot_id}',json={'code':footer,'active':True},timeout=50);saved.raise_for_status()
else:
    saved=session.post(f'{BASE}/code-snippets/v1/snippets',json=footer_payload,timeout=50);saved.raise_for_status()
    created=saved.json();foot_id=int(created['id'])
    if not created.get('active'):
        activate=session.post(f'{BASE}/code-snippets/v1/snippets/{foot_id}/activate',timeout=45);activate.raise_for_status()
foot=get_json(f'{BASE}/code-snippets/v1/snippets/{foot_id}')
if foot.get('code')!=footer or not foot.get('active'):
    raise SystemExit('Footer route snippet is not saved and active.')

# Verify the live page is serving the new component and all category/archive links still load.
page_public=requests.get('https://sard360.com/awraq-sard/?release=awraq-redesign',timeout=40,headers={'Cache-Control':'no-cache'})
page_public.raise_for_status()
html=page_public.text
checks={'page_http':page_public.status_code,'hero_present':'مساحة للبحث الهادئ' in html,'library_present':'المكتبة الكاملة' in html,'filter_controls':'data-as-filter' in html,'article_cards':'data-as-grid' in html,'old_shortcode_output_removed':'awraq-grid' not in html}
if not all(checks[k] for k in ('hero_present','library_present','filter_controls','article_cards')):
    raise SystemExit('Live page did not render the new Awraq component: '+json.dumps(checks,ensure_ascii=False))
summary.update({'published':True,'footer_snippet_id':foot_id,'footer_snippet_active':foot.get('active'),'live_page_checks':checks})
print(json.dumps(summary,ensure_ascii=False))
