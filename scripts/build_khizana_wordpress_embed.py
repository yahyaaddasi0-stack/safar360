#!/usr/bin/env python3
"""Extract the standalone Khizana app as a paste-ready Elementor HTML widget."""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'khizana.html').read_text(encoding='utf-8')
style = re.search(r'<style\b[^>]*>.*?</style>', source, re.I | re.S)
main = re.search(r'<main\b[^>]*>.*?</main>', source, re.I | re.S)
scripts = re.findall(r'<script\b[^>]*>.*?</script>', source, re.I | re.S)
if not style or not main or len(scripts) != 1:
    raise SystemExit('Expected one style block, one main element, and one inline application script.')
if 'https://safar360-alpha.vercel.app/' not in scripts[0]:
    raise SystemExit('The WordPress catalog origin is not configured in the application script.')

embed = '\n'.join([
    '<!-- Sard360 Khizana: paste this complete fragment into an Elementor HTML widget. -->',
    style.group(0),
    main.group(0),
    scripts[0],
    ''
])
out = ROOT / 'wordpress' / 'khizana-main-embed.html'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(embed, encoding='utf-8')
print(f'Generated {out} ({len(embed.encode("utf-8"))} bytes)')
