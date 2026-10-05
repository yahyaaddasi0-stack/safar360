const fs = require('fs');
const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

// Inside renderCarousel we added:
//     const ctaBtn = card.querySelector('.card-cta-btn');
//     if (ctaBtn) {
//       ctaBtn.addEventListener('click', (e) => {
//         e.preventDefault();
//         e.stopPropagation();
//         startDirectChat(index);
//       });
//     }
// This works, but we also kept:
//     card.addEventListener('click', (e) => { ...

// Let's ensure the backend load actually triggers a re-render.
const fixRender = `  // Fetch Characters
  try {
    const res = await fetch('/api/v1/characters');
    const data = await res.json();
    if (data && data.data) {
      CHARACTERS_DATA = data.data.map(char => ({
        ...char,
        arabicName: char.arabic_name,
        latinName: char.latin_name,
        roleTag: char.role_tag,
        categoryAr: char.category_ar,
        eraTag: char.era_tag,
        avatarSvg: AVATARS[char.id] || AVATARS['al-mutanabbi']
      }));
    }
  } catch (err) {
    console.error("Failed to load characters", err);
  }

  // 2. Render Hero Carousel
  renderCarousel();

  // 3. Setup Filter Bar
  setupCategoryFilters();

  // 4. Load Initial Character (index 0)
  if (CHARACTERS_DATA.length > 0) {
    selectCharacter(0);
  }`;

appJs = appJs.replace(/  \/\/ Fetch Characters[\s\S]*?if \(CHARACTERS_DATA.length > 0\) \{\n    selectCharacter\(0\);\n  \}/, fixRender);

fs.writeFileSync(appJsPath, appJs, 'utf8');
