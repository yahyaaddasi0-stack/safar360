const fs = require('fs');
const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

const replacement = `document.addEventListener('DOMContentLoaded', async () => {
  // 1. Setup Canvas Particle Background
  initParticleBackground();

  // Fetch Characters
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
  }

  // 5. Setup Audio & Ambient Synthesizer
  setupAudioAmbience();

  // 6. Setup 3D Scene Viewport Tilt
  setupScene3DTilt();

  // 7. Setup Microphone & Voice Handling
  setupVoiceAndMic();`;

appJs = appJs.replace(`document.addEventListener('DOMContentLoaded', () => {
  // 1. Setup Canvas Particle Background
  initParticleBackground();

  // 2. Render Hero Carousel
  renderCarousel();

  // 3. Setup Filter Bar
  setupCategoryFilters();

  // 4. Load Initial Character (index 0)
  selectCharacter(0);

  // 5. Setup Audio & Ambient Synthesizer
  setupAudioAmbience();

  // 6. Setup 3D Scene Viewport Tilt
  setupScene3DTilt();

  // 7. Setup Microphone & Voice Handling
  setupVoiceAndMic();`, replacement);

fs.writeFileSync(appJsPath, appJs, 'utf8');
