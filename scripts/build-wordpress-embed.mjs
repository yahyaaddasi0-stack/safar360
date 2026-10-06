import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const root = process.cwd();
const source = readFileSync(join(root, 'cinema.html'), 'utf8');
const catalogue = JSON.parse(readFileSync(join(root, 'cinema.json'), 'utf8'));
const logo = readFileSync(join(root, 'assets/images/sard360-logo-embed.png')).toString('base64');
const outputPath = join(root, 'cinema-wordpress-embed.html');
const rootSelector = '#sard360-cinema-root';

const styleMatch = source.match(/<style>([\s\S]*?)<\/style>/i);
const bodyMatch = source.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
if (!styleMatch || !bodyMatch) throw new Error('Could not extract the source page styles and body.');

const scriptMatches = [...bodyMatch[1].matchAll(/<script>([\s\S]*?)<\/script>/gi)];
if (scriptMatches.length !== 1) throw new Error(`Expected one application script, found ${scriptMatches.length}.`);
const appScript = scriptMatches[0][1].trim();
const standaloneAppScript = appScript.replace(
  /const inlineData = document\.getElementById\('sard360-cinema-inline-data'\);[\s\S]*?catalogue = await response\.json\(\);\s*\}/,
  "const inlineData = document.getElementById('sard360-cinema-inline-data');\n          if (!inlineData) throw new Error('The embedded Cinema catalogue is missing.');\n          const catalogue = JSON.parse(inlineData.textContent);"
);
if (standaloneAppScript === appScript || standaloneAppScript.includes("fetch('/cinema.json'")) {
  throw new Error('Could not produce a self-contained inline-catalogue script.');
}
let bodyMarkup = bodyMatch[1].replace(scriptMatches[0][0], '').trim();
bodyMarkup = bodyMarkup.replace(/<main\b/, '<main id="sard360-cinema-app"');
bodyMarkup = bodyMarkup.replace('src="/assets/images/sard360-logo.png"', `src="data:image/png;base64,${logo}"`);
if (bodyMarkup.includes('/assets/images/sard360-logo.png')) throw new Error('The official logo was not converted to an inline data URI.');

function findOpeningBrace(text, start) {
  let quote = '';
  let inComment = false;
  for (let i = start; i < text.length; i++) {
    const c = text[i], next = text[i + 1];
    if (inComment) {
      if (c === '*' && next === '/') { inComment = false; i++; }
      continue;
    }
    if (quote) {
      if (c === '\\') { i++; continue; }
      if (c === quote) quote = '';
      continue;
    }
    if (c === '/' && next === '*') { inComment = true; i++; continue; }
    if (c === '"' || c === "'") { quote = c; continue; }
    if (c === '{') return i;
  }
  return -1;
}

function findClosingBrace(text, opening) {
  let depth = 1;
  let quote = '';
  let inComment = false;
  for (let i = opening + 1; i < text.length; i++) {
    const c = text[i], next = text[i + 1];
    if (inComment) {
      if (c === '*' && next === '/') { inComment = false; i++; }
      continue;
    }
    if (quote) {
      if (c === '\\') { i++; continue; }
      if (c === quote) quote = '';
      continue;
    }
    if (c === '/' && next === '*') { inComment = true; i++; continue; }
    if (c === '"' || c === "'") { quote = c; continue; }
    if (c === '{') depth++;
    else if (c === '}' && --depth === 0) return i;
  }
  throw new Error('Unbalanced CSS block in source page.');
}

function scopeSelector(raw) {
  const selector = raw.trim();
  if (!selector) return selector;
  if (selector === ':root' || selector === 'html' || selector === 'body') return rootSelector;
  if (selector.startsWith(':root ')) return rootSelector + selector.slice(5);
  if (selector.startsWith('html ')) return rootSelector + selector.slice(4);
  if (selector.startsWith('body ')) return rootSelector + selector.slice(4);
  return `${rootSelector} ${selector}`;
}

function scopeCss(css) {
  let result = '';
  let cursor = 0;
  while (cursor < css.length) {
    const opening = findOpeningBrace(css, cursor);
    if (opening < 0) { result += css.slice(cursor); break; }
    const closing = findClosingBrace(css, opening);
    const prelude = css.slice(cursor, opening).trim();
    const content = css.slice(opening + 1, closing);
    if (/^@media\b|^@supports\b|^@container\b/i.test(prelude)) {
      result += `${prelude}{${scopeCss(content)}}`;
    } else if (/^@keyframes\b|^@-webkit-keyframes\b/i.test(prelude)) {
      result += `${prelude}{${content}}`;
    } else if (prelude.startsWith('@')) {
      result += `${prelude}{${content}}`;
    } else {
      result += `${prelude.split(',').map(scopeSelector).join(',')}{${content}}`;
    }
    cursor = closing + 1;
  }
  return result;
}

const scopedCss = scopeCss(styleMatch[1])
  .replace(/\bshimmer\b/g, 'sard360-cinema-shimmer')
  .replace(/\bcard-in\b/g, 'sard360-cinema-card-in');
const safeCatalogJson = JSON.stringify(catalogue)
  .replace(/</g, '\\u003c')
  .replace(/>/g, '\\u003e')
  .replace(/&/g, '\\u0026');

const embed = `<!--
سينما سرد — مقطع WordPress مستقل.
انسخ هذا الملف كاملاً إلى كتلة HTML مخصّصة في صفحة /cinema ذات قالب Full Width أو Canvas.
الكتالوج والأنماط والسكريبت والشعار مضمنة هنا؛ الفيديوهات والصور المصغّرة تأتي من YouTube.
-->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&family=Tajawal:wght@400;500;700;800;900&display=swap" rel="stylesheet">
<style>
${scopedCss}
</style>
<div id="sard360-cinema-root" lang="ar" dir="rtl">
${bodyMarkup}
  <script type="application/json" id="sard360-cinema-inline-data">${safeCatalogJson}</script>
</div>
<script>
${standaloneAppScript}
</script>
`;

writeFileSync(outputPath, embed, 'utf8');
console.log(`Generated ${outputPath} (${Buffer.byteLength(embed, 'utf8')} bytes, ${catalogue.items.length} videos embedded).`);
