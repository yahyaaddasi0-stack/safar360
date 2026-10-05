const fs = require('fs');
const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

// The issue might be that character data structure is slightly different (e.g., camelCase vs snake_case).
// We need to map the backend response properly.

const mappingFix = `      CHARACTERS_DATA = data.data.map(char => ({
        ...char,
        arabicName: char.arabic_name || char.arabicName,
        latinName: char.latin_name || char.latinName,
        roleTag: char.role_tag || char.roleTag,
        categoryAr: char.category_ar || char.categoryAr,
        eraTag: char.era_tag || char.eraTag,
        avatarSvg: AVATARS[char.id] || AVATARS['al-mutanabbi'],
        quote: char.quote || '',
        title: char.title || '',
        origin: char.origin || '',
        achievement: char.achievement || '',
        timeline: char.timeline || [],
        artifacts: char.artifacts || [],
        mapLocations: char.map_locations || char.mapLocations || [],
        quickPrompts: char.quick_prompts || char.quickPrompts || [],
        dialogueResponses: char.dialogueResponses || { default: char.quote || 'مرحباً، كيف أساعدك؟' }
      }));`;

appJs = appJs.replace(/      CHARACTERS_DATA = data\.data\.map\(char => \(\{[\s\S]*?avatarSvg: AVATARS\[char\.id\] \|\| AVATARS\['al-mutanabbi'\]\n      \}\)\);/, mappingFix);

// Also let's double check DOMContentLoaded logic to make sure the fetch blocks rendering
const asyncFetchBlock = `  // Fetch Characters
  try {
    const res = await fetch('/api/v1/characters');
    const data = await res.json();
    if (data && data.data) {
      CHARACTERS_DATA = data.data.map(char => ({
        ...char,
        arabicName: char.arabic_name || char.arabicName,
        latinName: char.latin_name || char.latinName,
        roleTag: char.role_tag || char.roleTag,
        categoryAr: char.category_ar || char.categoryAr,
        eraTag: char.era_tag || char.eraTag,
        avatarSvg: AVATARS[char.id] || AVATARS['al-mutanabbi'],
        quote: char.quote || '',
        title: char.title || '',
        origin: char.origin || '',
        achievement: char.achievement || '',
        timeline: char.timeline || [],
        artifacts: char.artifacts || [],
        mapLocations: char.map_locations || char.mapLocations || [],
        quickPrompts: char.quick_prompts || char.quickPrompts || [],
        dialogueResponses: char.dialogueResponses || { default: char.quote || 'مرحباً بك! ماذا تود أن تسألني؟', prompts: {} }
      }));
    }
  } catch (err) {
    console.error("Failed to load characters", err);
  }

  // 2. Render Hero Carousel AFTER fetching
  renderCarousel();

  // 3. Setup Filter Bar
  setupCategoryFilters();

  // 4. Load Initial Character (index 0)
  if (CHARACTERS_DATA.length > 0) {
    selectCharacter(0);
  }`;

appJs = appJs.replace(/  \/\/ Fetch Characters[\s\S]*?if \(CHARACTERS_DATA\.length > 0\) \{\n    selectCharacter\(0\);\n  \}/, asyncFetchBlock);

fs.writeFileSync(appJsPath, appJs, 'utf8');
