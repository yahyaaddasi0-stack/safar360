const fs = require('fs');

const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

// The replacement logic:
// We will replace the entire block from `const CHARACTERS_DATA = [` to `];` (line 7 to line 404).
// Since the block is large, let's use a regex that matches `const CHARACTERS_DATA = [...];`
// Wait, maybe we just define `let CHARACTERS_DATA = [];` and load it inside `DOMContentLoaded`.

const startIdx = appJs.indexOf('const CHARACTERS_DATA = [');
const endMarker = '];\n\n// =============================================================================\n// 2. Global State Management';
const endIdx = appJs.indexOf(endMarker);

if (startIdx > -1 && endIdx > -1) {
  const localAvatarsCode = `
// Local fallback avatars for visual richness
const AVATARS = {
  'salah-al-din': \`
    <svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="salah-gold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#f1c40f"/>
          <stop offset="100%" stop-color="#996515"/>
        </linearGradient>
      </defs>
      <circle cx="60" cy="60" r="56" fill="#111620" stroke="url(#salah-gold)" stroke-width="2"/>
      <path d="M22 112 C28 78 92 78 98 112 Z" fill="#1b2332" stroke="#d4af37" stroke-width="1.2"/>
      <rect x="52" y="60" width="16" height="18" fill="#c68a52"/>
      <ellipse cx="60" cy="52" rx="17" ry="20" fill="#d99f6b"/>
      <path d="M48 44 Q53 41 58 44" stroke="#1a1e28" stroke-width="2" fill="none"/>
      <path d="M62 44 Q67 41 72 44" stroke="#1a1e28" stroke-width="2" fill="none"/>
      <ellipse cx="53" cy="48" rx="2.5" ry="3" fill="#111"/>
      <ellipse cx="67" cy="48" rx="2.5" ry="3" fill="#111"/>
      <path d="M44 54 Q60 60 76 54 Q72 82 60 84 Q48 82 44 54 Z" fill="#171a22"/>
      <path d="M36 40 C36 18 84 18 84 40 C84 46 80 48 60 48 C40 48 36 46 36 40 Z" fill="#2d3748"/>
      <path d="M34 38 Q60 22 86 38 Q82 16 60 16 Q38 16 34 38 Z" fill="url(#salah-gold)"/>
      <circle cx="60" cy="27" r="4.5" fill="#27ae60" stroke="#f1c40f" stroke-width="1.5"/>
    </svg>\`,
  'al-mutanabbi': \`
    <svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
      <circle cx="60" cy="60" r="56" fill="#191024" stroke="#9b59b6" stroke-width="2"/>
      <path d="M22 112 C28 74 92 74 98 112 Z" fill="#3b1b54" stroke="#d4af37" stroke-width="1.2"/>
      <rect x="52" y="60" width="16" height="18" fill="#c08655"/>
      <ellipse cx="60" cy="51" rx="17" ry="20" fill="#db9e6d"/>
      <path d="M48 42 Q53 39 58 42" stroke="#1f112b" stroke-width="2.2" fill="none"/>
      <path d="M62 42 Q67 39 72 42" stroke="#1f112b" stroke-width="2.2" fill="none"/>
      <ellipse cx="53" cy="47" rx="2.5" ry="3" fill="#111"/>
      <ellipse cx="67" cy="47" rx="2.5" ry="3" fill="#111"/>
      <path d="M44 54 Q60 84 76 54 Q60 62 44 54 Z" fill="#1b1224"/>
      <path d="M34 30 C34 14 86 14 86 30 C86 44 76 48 60 48 C44 48 34 44 34 30 Z" fill="#271038"/>
      <path d="M32 28 Q60 14 88 28 Q80 10 60 10 Q40 10 32 28 Z" fill="#d4af37"/>
      <circle cx="60" cy="24" r="4" fill="#9b59b6" stroke="#f1c40f" stroke-width="1.5"/>
    </svg>\`,
  'zenobia': \`
    <svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
      <circle cx="60" cy="60" r="56" fill="#1a1412" stroke="#e67e22" stroke-width="2"/>
      <path d="M22 112 C28 72 92 72 98 112 Z" fill="#8e44ad" stroke="#d4af37" stroke-width="1.2"/>
      <path d="M30 46 C30 18 90 18 90 46 C90 76 80 84 60 84 C40 84 30 76 30 46 Z" fill="#2c3e50"/>
      <ellipse cx="60" cy="53" rx="15" ry="18" fill="#e5b182"/>
      <path d="M49 46 Q54 44 58 46" stroke="#142c28" stroke-width="1.6" fill="none"/>
      <path d="M62 46 Q67 44 71 46" stroke="#142c28" stroke-width="1.6" fill="none"/>
      <ellipse cx="53.5" cy="50" rx="2" ry="2.5" fill="#111"/>
      <ellipse cx="66.5" cy="50" rx="2" ry="2.5" fill="#111"/>
      <circle cx="60" cy="22" r="4" fill="#f1c40f" stroke="#e67e22" stroke-width="1"/>
      <circle cx="50" cy="25" r="2.5" fill="#f1c40f"/>
      <circle cx="70" cy="25" r="2.5" fill="#f1c40f"/>
    </svg>\`
};

let CHARACTERS_DATA = [];
`;
  appJs = appJs.substring(0, startIdx) + localAvatarsCode + appJs.substring(endIdx + 2); // skip `];\n`
  fs.writeFileSync(appJsPath, appJs, 'utf8');
}
