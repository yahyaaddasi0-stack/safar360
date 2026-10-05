const fs = require('fs');
const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

// Replace the renderCarousel block
const newRenderCarousel = `function renderCarousel() {
  const track = document.getElementById('carousel-track');
  const dotsContainer = document.getElementById('carousel-dots');
  if (!track || !dotsContainer) return;

  track.innerHTML = '';
  dotsContainer.innerHTML = '';

  CHARACTERS_DATA.forEach((char, index) => {
    // 1. Create Card
    const card = document.createElement('div');
    card.className = \`character-card \${index === currentCharacterIndex ? 'active' : ''}\`;
    card.dataset.index = index;
    card.dataset.category = char.category;

    card.innerHTML = \`
      <div class="card-category-badge">\${char.categoryAr}</div>
      <div class="card-avatar-wrapper">
        <div class="card-avatar-svg">\${char.avatarSvg}</div>
        <div class="card-avatar-halo"></div>
      </div>
      <div class="card-names">
        <h3 class="card-arabic-name">\${char.arabicName}</h3>
        <span class="card-latin-name">\${char.latinName}</span>
      </div>
      <div class="card-role-title">\${char.title}</div>
      <p class="card-quote-snippet">"\${char.quote}"</p>
      <div class="card-meta-row">
        <span>📍 \${char.origin}</span>
        <span>⏳ \${char.eraTag}</span>
      </div>
      <button class="card-cta-btn">
        <span>حوار مباشر +</span>
        <span>✦</span>
      </button>
    \`;

    // Strict event attachment AFTER DOM nodes are created
    const ctaBtn = card.querySelector('.card-cta-btn');
    if (ctaBtn) {
      ctaBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        startDirectChat(index);
      });
    }

    card.addEventListener('click', (e) => {
      // Avoid conflict if the button was clicked
      if (!e.target.closest('.card-cta-btn')) {
        startDirectChat(index);
      }
    });

    track.appendChild(card);

    // 2. Create Dot
    const dot = document.createElement('button');
    dot.className = \`carousel-dot \${index === currentCharacterIndex ? 'active' : ''}\`;
    dot.setAttribute('aria-label', \`الانتقال إلى \${char.arabicName}\`);
    dot.addEventListener('click', () => {
      startDirectChat(index);
    });
    dotsContainer.appendChild(dot);
  });

  updateSlideCounter();
}`;

appJs = appJs.replace(/function renderCarousel\(\) \{[\s\S]*?updateSlideCounter\(\);\n\}/, newRenderCarousel);

fs.writeFileSync(appJsPath, appJs, 'utf8');
