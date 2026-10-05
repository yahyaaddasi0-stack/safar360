/**
 * SAFAR 360 (سَفَر ٣٦٠) - APPLICATION LOGIC
 * Pure Vanilla JavaScript | No Frameworks | Senior Frontend Architecture
 */

// =============================================================================
// 1. Historical Figures Database (5 Featured Characters)
// =============================================================================

// Local fallback avatars for visual richness
const AVATARS = {
  'salah-al-din': `
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
    </svg>`,
  'al-mutanabbi': `
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
    </svg>`,
  'zenobia': `
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
    </svg>`
};

function avatarMarkup(char) {
  if (AVATARS[char.id]) return AVATARS[char.id];
  if (typeof char.avatar === 'string' && char.avatar.startsWith('data:image/svg+xml,')) {
    return `<img src="${char.avatar}" alt="" style="display:block;width:100%;height:100%;object-fit:contain">`;
  }
  return AVATARS['al-mutanabbi'];
}

let CHARACTERS_DATA = [];


// =============================================================================
// 2. Global State Management
// =============================================================================
let currentCharacterIndex = 0; // Starts with Tariq ibn Ziyad (or Ibn Battuta)
let activeCategory = 'all';
let isAudioAmbiencePlaying = false;
let isMicActive = false;
let isSpeechSynthesisActive = true;
let currentCanvasTab = 'scene';
let audioContext = null;
let ambientGainNode = null;
let ambientOscillator = null;

// Speech Recognition instance if supported
let speechRecognitionInstance = null;

// =============================================================================
// 3. Initialization on DOMContentLoaded
// =============================================================================
// Guard browser-only bootstrap so server-side inspection cannot access DOM globals.
if (typeof window !== 'undefined' && typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', async () => {
  // 1. Setup Canvas Particle Background
  initParticleBackground();

  // Fetch Characters
  try {
    const res = await fetch('/api/v1/characters');
    if (!res.ok) throw new Error(`Characters API HTTP ${res.status}`);
    const data = await res.json();
    if (!Array.isArray(data?.data) || data.data.length === 0) {
      throw new Error('Characters API returned no characters');
    }
    if (data && data.data) {
      CHARACTERS_DATA = data.data.map(char => ({
        ...char,
        arabicName: char.arabic_name || char.arabicName,
        latinName: char.latin_name || char.latinName,
        roleTag: char.role_tag || char.roleTag,
        categoryAr: char.category_ar || char.categoryAr,
        eraTag: char.era_tag || char.eraTag,
        avatarSvg: avatarMarkup(char),
        quote: char.quote || '',
        title: char.title || '',
        origin: char.origin || '',
        achievement: char.achievement || '',
        timeline: char.timeline || [],
        artifacts: char.artifacts || [],
        mapLocations: char.map_locations || char.mapLocations || [],
        canvas_data: char.canvas_data || {},
        quickPrompts: char.quick_prompts || char.quickPrompts || [],
        dialogueResponses: char.dialogueResponses || { default: char.quote || 'مرحباً بك! ماذا تود أن تسألني؟', prompts: {} }
      }));
    }
  } catch (err) {
    console.warn('Characters API unavailable; loading local public catalogue:', err);
    try {
      const localResponse = await fetch('/characters-public.json');
      if (!localResponse.ok) throw new Error(`Catalogue HTTP ${localResponse.status}`);
      const local = await localResponse.json();
      if (!Array.isArray(local.data) || local.data.length === 0) {
        throw new Error('Local catalogue is empty');
      }
      CHARACTERS_DATA = local.data.map(char => ({
        ...char,
        arabicName: char.arabic_name,
        latinName: char.latin_name,
        roleTag: char.role_tag,
        categoryAr: char.category_ar,
        eraTag: char.era_tag,
        avatarSvg: avatarMarkup(char),
        mapLocations: char.map_locations || [],
        quickPrompts: char.quick_prompts || [],
        dialogueResponses: {default: char.quote || 'مرحباً بك! ماذا تود أن تسألني؟', prompts: {}}
      }));
    } catch (fallbackError) {
      console.error('Unable to load either characters catalogue:', fallbackError);
    }
  }

  // 2. Render Hero Carousel AFTER fetching
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
  setupVoiceAndMic();

  // 8. Auto-resize textarea
  const textarea = document.getElementById('chat-textarea');
  if (textarea) {
    textarea.addEventListener('input', function() {
      this.style.height = 'auto';
      this.style.height = (this.scrollHeight) + 'px';
    });
    textarea.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleChatSubmit(e);
      }
    });
  }

  // 9. Setup Clear chat button & TTS toggle
  document.getElementById('btn-clear-chat')?.addEventListener('click', () => {
    resetChatMessages();
  });

  document.getElementById('btn-tts-toggle')?.addEventListener('click', () => {
    isSpeechSynthesisActive = !isSpeechSynthesisActive;
    const ttsIcon = document.getElementById('tts-icon');
    if (ttsIcon) {
      ttsIcon.textContent = isSpeechSynthesisActive ? '🔊' : '🔇';
    }
    showToastNotification(isSpeechSynthesisActive ? 'تم تفعيل نطق الإجابات آلياً' : 'تم كتم النطق الآلي');
  });

  // 10. Carousel Nav Arrows
  document.getElementById('carousel-prev')?.addEventListener('click', () => {
    navigateCarousel(-1);
  });
  document.getElementById('carousel-next')?.addEventListener('click', () => {
    navigateCarousel(1);
  });

  // Check for deep link or query param: ?mode=chat or #chat
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('mode') === 'chat' || window.location.hash === '#chat') {
    startDirectChat(0);
  }
  });
}

// =============================================================================
// 4. Hero Carousel Logic
// =============================================================================
function renderCarousel() {
  const track = document.getElementById('carousel-track');
  const dotsContainer = document.getElementById('carousel-dots');
  if (!track || !dotsContainer) return;

  track.innerHTML = '';
  dotsContainer.innerHTML = '';

  CHARACTERS_DATA.forEach((char, index) => {
    // 1. Create Card
    const card = document.createElement('div');
    card.className = `character-card ${index === currentCharacterIndex ? 'active' : ''}`;
    card.dataset.index = index;
    card.dataset.category = char.category;

    card.innerHTML = `
      <div class="card-category-badge">${char.categoryAr}</div>
      <div class="card-avatar-wrapper">
        <div class="card-avatar-svg">${char.avatarSvg}</div>
        <div class="card-avatar-halo"></div>
      </div>
      <div class="card-names">
        <h3 class="card-arabic-name">${char.arabicName}</h3>
        <span class="card-latin-name">${char.latinName}</span>
      </div>
      <div class="card-role-title">${char.title}</div>
      <p class="card-quote-snippet">"${char.quote}"</p>
      <div class="card-meta-row">
        <span>📍 ${char.origin}</span>
        <span>⏳ ${char.eraTag}</span>
      </div>
      <button class="card-cta-btn">
        <span>حوار مباشر +</span>
        <span>✦</span>
      </button>
    `;

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
    dot.className = `carousel-dot ${index === currentCharacterIndex ? 'active' : ''}`;
    dot.setAttribute('aria-label', `الانتقال إلى ${char.arabicName}`);
    dot.addEventListener('click', () => {
      startDirectChat(index);
    });
    dotsContainer.appendChild(dot);
  });

  updateSlideCounter();
}

function updateCarouselView() {
  const cards = document.querySelectorAll('.character-card');
  const dots = document.querySelectorAll('.carousel-dot');
  const track = document.getElementById('carousel-track');

  cards.forEach((card, idx) => {
    card.classList.toggle('active', idx === currentCharacterIndex);
  });

  dots.forEach((dot, idx) => {
    dot.classList.toggle('active', idx === currentCharacterIndex);
  });

  updateSlideCounter();

  // Scroll active card into view smoothly
  if (track && cards[currentCharacterIndex]) {
    const activeCard = cards[currentCharacterIndex];
    const trackRect = track.getBoundingClientRect();
    const cardRect = activeCard.getBoundingClientRect();
    
    // In RTL, calculate offset
    const offset = activeCard.offsetLeft - (track.clientWidth / 2) + (activeCard.clientWidth / 2);
    track.parentElement.scrollTo({
      left: offset,
      behavior: 'smooth'
    });
  }
}

function navigateCarousel(direction) {
  let newIndex = currentCharacterIndex + direction;
  if (newIndex < 0) newIndex = CHARACTERS_DATA.length - 1;
  if (newIndex >= CHARACTERS_DATA.length) newIndex = 0;
  selectCharacter(newIndex);
}

function updateSlideCounter() {
  const currentElem = document.getElementById('current-slide-idx');
  const totalElem = document.getElementById('total-slides-count');
  if (currentElem) currentElem.textContent = String(currentCharacterIndex + 1).padStart(2, '0');
  if (totalElem) totalElem.textContent = String(CHARACTERS_DATA.length).padStart(2, '0');
}

// =============================================================================
// 5. Select Character & Synchronize Chat and Canvas
// =============================================================================
function selectCharacter(index) {
  if (index < 0 || index >= CHARACTERS_DATA.length) return;
  currentCharacterIndex = index;
  const character = CHARACTERS_DATA[currentCharacterIndex];

  // 1. Update Carousel states
  updateCarouselView();

  // 2. Update Chat Identity
  const chatName = document.getElementById('chat-character-name');
  const chatBadge = document.getElementById('chat-character-badge');
  const chatMiniAvatar = document.getElementById('chat-mini-avatar');
  const bioEra = document.getElementById('bio-era');
  const bioOrigin = document.getElementById('bio-origin');
  const bioAchieve = document.getElementById('bio-achievement');

  if (chatName) chatName.textContent = character.arabicName;
  if (chatBadge) chatBadge.textContent = character.roleTag;
  if (chatMiniAvatar) chatMiniAvatar.innerHTML = character.avatarSvg;
  if (bioEra) bioEra.textContent = character.era;
  if (bioOrigin) bioOrigin.textContent = character.origin;
  if (bioAchieve) bioAchieve.textContent = character.achievement;

  // 3. Reset and inject welcome message in Chat
  resetChatMessages();

  // 4. Update Quick Prompts
  renderQuickPrompts(character);

  // 5. Update Interactive Canvas: Scene View (Portrait, Quote, Tags)
  const portraitWrapper = document.getElementById('scene-portrait-wrapper');
  const sceneQuote = document.getElementById('scene-character-quote');
  const sceneAuthor = document.getElementById('scene-character-author');
  const sceneEraTag = document.getElementById('scene-era-tag');

  if (portraitWrapper) portraitWrapper.innerHTML = character.avatarSvg;
  if (sceneQuote) sceneQuote.textContent = `"${character.quote}"`;
  if (sceneAuthor) sceneAuthor.textContent = `— ${character.arabicName}، ${character.title}`;
  if (sceneEraTag) sceneEraTag.textContent = character.eraTag;

  // 6. Update Timeline View
  renderTimeline(character);

  // 7. Update Artifacts View
  renderArtifacts(character);

  // 8. Update Map View
  renderMap(character);

  // 9. Update era display in top nav
  const currentEraDisplay = document.getElementById('current-era-display');
  if (currentEraDisplay) {
    currentEraDisplay.textContent = character.eraTag + ' (' + character.era + ')';
  }

  // 10. Update canvas placeholder active name & preview frame
  const canvasActiveName = document.getElementById('canvas-active-name');
  if (canvasActiveName) canvasActiveName.textContent = character.arabicName;

  renderCanvasPreview(character);
}

// =============================================================================
// Interactive Split-Screen Transition State Functions
// =============================================================================
function startDirectChat(index) {
  selectCharacter(index);
  document.body.classList.add('in-chat-mode');

  // Smooth scroll to the split-screen view
  setTimeout(() => {
    const splitSection = document.getElementById('main-split-screen');
    if (splitSection) {
      splitSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, 80);
}

function backToCarousel() {
  document.body.classList.remove('in-chat-mode');

  // Smooth scroll back to hero carousel
  setTimeout(() => {
    const heroSection = document.getElementById('hero-carousel-section');
    if (heroSection) {
      heroSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, 80);
}

function renderCanvasPreview(character) {
  const frame = document.getElementById('canvas-preview-frame');
  if (!frame) return;

  const canvasType = character.canvas_data ? character.canvas_data.type : 'interactive_map';
  const cData = character.canvas_data ? (character.canvas_data.data || {}) : {};
  
  if (canvasType === 'interactive_map') {
    frame.innerHTML = '<div id="leaflet-map" style="width: 100%; height: 400px; border-radius: 8px; z-index: 1;"></div>';
    setTimeout(() => {
      const mapCenter = cData.center || [31.771959, 35.217018];
      const zoomLevel = cData.zoom || 6;
      
      const map = L.map('leaflet-map').setView(mapCenter, zoomLevel);
      
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
      }).addTo(map);

      // We explicitly mapped map_locations to mapLocations in the fix_mapping.js
      const locations = character.mapLocations || character.map_locations || [];
      if (locations.length > 0) {
        locations.forEach(loc => {
          L.marker(loc.coords).addTo(map)
            .bindPopup('<b>' + loc.name + '</b><br>' + loc.desc);
        });
      }
      
      // Delay invalidation to ensure proper rendering inside the flex container
      setTimeout(() => { map.invalidateSize(); }, 300);
      
    }, 100);
  } else if (canvasType === 'timeline') {
    let timelineHtml = '<div class="vertical-timeline" style="padding: 1rem;">';
    const events = cData.events || character.timeline || [];
    events.forEach((evt, idx) => {
      const year = evt.date || evt.year;
      timelineHtml += `
        <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem; position: relative;">
          <div style="min-width: 60px; font-weight: bold; color: var(--accent-gold); text-align: left;">${year}</div>
          <div style="width: 2px; background: var(--accent-gold); position: relative;">
            <div style="position: absolute; top: 0; left: -4px; width: 10px; height: 10px; border-radius: 50%; background: var(--accent-gold-hover);"></div>
          </div>
          <div>
            <h4 style="margin: 0; color: var(--text-primary);">${evt.title}</h4>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.85rem; color: var(--text-secondary);">${evt.desc}</p>
          </div>
        </div>
      `;
    });
    timelineHtml += '</div>';
    frame.innerHTML = timelineHtml;
  } else if (canvasType === 'manuscript_viewer') {
    frame.innerHTML = `
      <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; background: #1a1e24; border-radius: 8px; border: 1px solid var(--border-color); position: relative; overflow: hidden;">
        <div style="position: absolute; top: 1rem; right: 1rem; background: rgba(0,0,0,0.6); padding: 0.5rem; border-radius: 4px; color: var(--accent-gold);">
          📜 عارض المخطوطات
        </div>
        <img src="https://images.unsplash.com/photo-1583321500900-82807e458f3c?auto=format&fit=crop&q=80&w=800" alt="Manuscript" style="max-height: 100%; max-width: 100%; opacity: 0.8; filter: sepia(0.4);">
        <div style="position: absolute; bottom: 1rem; background: rgba(0,0,0,0.8); padding: 1rem; border-radius: 8px; border: 1px solid var(--accent-gold); color: #fff; max-width: 80%;">
          <div style="font-weight: bold; color: var(--accent-gold-hover); margin-bottom: 0.5rem;">تظليل تلقائي</div>
          <p style="margin:0; font-size: 0.9rem;">${character.quote}</p>
        </div>
      </div>
    `;
  }
}

// Expose handlers only in a real browser context.
if (typeof window !== 'undefined') {
  window.startDirectChat = startDirectChat;
  window.backToCarousel = backToCarousel;
  window.renderCanvasPreview = renderCanvasPreview;
}

// =============================================================================
// 6. Category Filter Bar Logic
// =============================================================================
function setupCategoryFilters() {
  const pills = document.querySelectorAll('.filter-pill');
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => {
        p.classList.remove('active');
        p.setAttribute('aria-selected', 'false');
      });
      pill.classList.add('active');
      pill.setAttribute('aria-selected', 'true');

      const category = pill.dataset.category;
      activeCategory = category;
      applyCategoryFilter(category);
    });
  });
}

function applyCategoryFilter(category) {
  const cards = document.querySelectorAll('.character-card');
  let firstMatchIndex = -1;

  cards.forEach((card, idx) => {
    const cardCategory = card.dataset.category;
    if (category === 'all' || cardCategory === category) {
      card.style.display = 'flex';
      card.style.opacity = '1';
      if (firstMatchIndex === -1) firstMatchIndex = idx;
    } else {
      card.style.display = 'none';
      card.style.opacity = '0';
    }
  });

  // If active character is hidden, select first matched
  if (firstMatchIndex !== -1) {
    selectCharacter(firstMatchIndex);
  }
}

// =============================================================================
// 7. Chat Interface Logic
// =============================================================================
function resetChatMessages() {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  const character = CHARACTERS_DATA[currentCharacterIndex];
  container.innerHTML = '';

  // Welcome message from character
  const greeting = character.quote || 'مرحباً بك! ماذا تود أن تسألني؟';
  addBotMessage(greeting, character.arabicName);
}

function renderQuickPrompts(character) {
  const container = document.getElementById('quick-prompts-list');
  if (!container) return;
  container.innerHTML = '';

  character.quickPrompts.forEach(promptText => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'prompt-pill-btn';
    btn.textContent = promptText;
    btn.onclick = () => {
      sendDirectMessage(promptText);
    };
    container.appendChild(btn);
  });
}

function handleChatSubmit(e) {
  if (e && e.preventDefault) e.preventDefault();
  const textarea = document.getElementById('chat-textarea');
  if (!textarea) return;

  const query = textarea.value.trim();
  if (!query) return;

  textarea.value = '';
  textarea.style.height = 'auto';

  sendDirectMessage(query);
}

function sendDirectMessage(userText) {
  const character = CHARACTERS_DATA[currentCharacterIndex];

  // 1. Append User Message (in user bubble: --user-bubble: #2d2b1e)
  addUserMessage(userText);

  // 2. Show Typing Indicator
  showTypingIndicator();

  // 3. Stream from FastAPI Backend via Server-Sent Events (SSE)
  streamChatMessageFromBackend(userText, character);
}

async function streamChatMessageFromBackend(userText, character) {
  try {
    const response = await fetch('/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        character_id: character.id || 'ibn-battuta',
        messages: [
          { role: 'user', content: userText }
        ],
        stream: true,
        temperature: 0.7
      })
    });

    if (!response.ok || !response.body) {
      throw new Error(`Backend API error: ${response.status}`);
    }

    hideTypingIndicator();

    // Create streaming bot message bubble
    const { bodyElem, finalize } = createStreamingBotMessage(character.arabicName);
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let accumulatedText = '';
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data:')) continue;
        const dataStr = trimmed.replace(/^data:\s*/, '');
        if (dataStr === '[DONE]') continue;

        try {
          const parsed = JSON.parse(dataStr);
          const token = parsed.choices?.[0]?.delta?.content || '';
          if (token) {
            accumulatedText += token;
            
            // Check for [GENERATE_IMAGE: ...] tag being streamed and replace with skeleton
            let displayHtml = escapeHtml(accumulatedText).replace(/\n/g, '<br>');
            if (displayHtml.includes('[GENERATE_IMAGE:')) {
               const imageFinished = accumulatedText.includes('![Generated Image](') || accumulatedText.includes('تعذّر إنشاء الصورة');
               displayHtml = displayHtml.replace(/\[GENERATE_IMAGE:.*?(?:\]|$)/g, imageFinished ? '' : '<div class="image-skeleton" style="width:100%; height:200px; background:rgba(212,175,55,0.1); border:1px dashed var(--accent-gold); border-radius:8px; display:flex; align-items:center; justify-content:center; color:var(--accent-gold); animation: pulse 1.5s infinite;">جاري رسم المشهد...</div>');
            }
            
            // Parse Markdown images from backend ![Generated Image](url)
            displayHtml = displayHtml.replace(/!\[.*?\]\((.*?)\)/g, '<img src="$1" alt="Generated Scene" style="max-width:100%; border-radius:8px; margin-top:8px; border:1px solid var(--accent-gold);">');
            
            bodyElem.innerHTML = displayHtml;
            const container = document.getElementById('chat-messages-container');
            if (container) container.scrollTop = container.scrollHeight;
          }
        } catch (e) {
          // skip malformed JSON chunks
        }
      }
    }

    finalize(accumulatedText);

    // TTS Speak if active
    if (isSpeechSynthesisActive && 'speechSynthesis' in window && accumulatedText) {
      speakText(accumulatedText);
    }

  } catch (error) {
    console.warn('[Safar 360] Backend stream unavailable, falling back to local engine:', error);
    hideTypingIndicator();
    const reply = generateCharacterResponse(userText, character);
    addBotMessage(reply, character.arabicName);
    if (isSpeechSynthesisActive && 'speechSynthesis' in window) {
      speakText(reply);
    }
  }
}

function createStreamingBotMessage(charName) {
  const container = document.getElementById('chat-messages-container');
  const character = CHARACTERS_DATA[currentCharacterIndex];
  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-msg bot';
  const now = new Date();
  const timeStr = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;

  msgDiv.innerHTML = `
    <div class="msg-sender-avatar">
      ${character.avatarSvg}
    </div>
    <div class="msg-content-box">
      <div class="msg-header-info">
        <span class="msg-sender-name">${charName}</span>
        <span class="msg-time">${timeStr}</span>
      </div>
      <div class="msg-body-text streaming-cursor"></div>
      <div class="msg-actions" style="display: none;">
        <button class="msg-action-btn btn-action-speak">
          <span>🔊 استمع</span>
        </button>
        <button class="msg-action-btn btn-action-copy">
          <span>📋 نسخ</span>
        </button>
      </div>
    </div>
  `;

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
  const bodyElem = msgDiv.querySelector('.msg-body-text');
  const actionsElem = msgDiv.querySelector('.msg-actions');

  return {
    bodyElem,
    finalize: (finalText) => {
      bodyElem.classList.remove('streaming-cursor');
      if (actionsElem) {
        actionsElem.style.display = 'flex';
        const speakBtn = actionsElem.querySelector('.btn-action-speak');
        const copyBtn = actionsElem.querySelector('.btn-action-copy');
        if (speakBtn) speakBtn.onclick = () => speakText(finalText);
        if (copyBtn) copyBtn.onclick = () => copyMessageText(finalText);
      }
    }
  };
}

function addUserMessage(text) {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-msg user';
  const now = new Date();
  const timeStr = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;

  msgDiv.innerHTML = `
    <div class="msg-sender-avatar">م</div>
    <div class="msg-content-box">
      <div class="msg-header-info">
        <span class="msg-sender-name">المُستكشف</span>
        <span class="msg-time">${timeStr}</span>
      </div>
      <div class="msg-body-text">${escapeHtml(text)}</div>
    </div>
  `;

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function addBotMessage(text, charName) {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  const character = CHARACTERS_DATA[currentCharacterIndex];
  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-msg bot';
  const now = new Date();
  const timeStr = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;

  msgDiv.innerHTML = `
    <div class="msg-sender-avatar">
      ${character.avatarSvg}
    </div>
    <div class="msg-content-box">
      <div class="msg-header-info">
        <span class="msg-sender-name">${charName}</span>
        <span class="msg-time">${timeStr}</span>
      </div>
      <div class="msg-body-text">${escapeHtml(text).replace(/\n/g, '<br>')}</div>
      <div class="msg-actions">
        <button class="msg-action-btn" onclick="speakText('${escapeHtml(text.replace(/'/g, "\\'"))}')">
          <span>🔊 استمع</span>
        </button>
        <button class="msg-action-btn" onclick="navigator.clipboard.writeText('${escapeHtml(text.replace(/'/g, "\\'"))}'); showToastNotification('تم نسخ الرسالة بنجاح');">
          <span>📋 نسخ</span>
        </button>
      </div>
    </div>
  `;

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
  let indicator = document.getElementById('chat-typing-indicator');
  const container = document.getElementById('chat-messages-container');
  if (!indicator && container) {
    indicator = document.createElement('div');
    indicator.id = 'chat-typing-indicator';
    indicator.className = 'typing-indicator-box';
    indicator.innerHTML = `
      <span>يستحضر الحكمة التاريخية</span>
      <div class="typing-dots">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    `;
    container.appendChild(indicator);
  }
  if (indicator) {
    indicator.style.display = 'flex';
    container.scrollTop = container.scrollHeight;
  }
}

function hideTypingIndicator() {
  const indicator = document.getElementById('chat-typing-indicator');
  if (indicator) {
    indicator.style.display = 'none';
  }
}

function generateCharacterResponse(query, character) {
  return "عذراً، فقدنا الاتصال بوعي الشخصية التاريخية بسبب انقطاع الخادم. يرجى المحاولة لاحقاً.";
}

// =============================================================================
// 8. Voice & Microphone Engine (--mic-active: #e74c3c)
// =============================================================================
function setupVoiceAndMic() {
  const micBtn = document.getElementById('mic-toggle-btn');
  const statusHint = document.getElementById('mic-status-hint');

  if (!micBtn) return;

  // Initialize Speech Recognition if supported
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    speechRecognitionInstance = new SpeechRecognition();
    speechRecognitionInstance.lang = 'ar-SA';
    speechRecognitionInstance.continuous = false;
    speechRecognitionInstance.interimResults = false;

    speechRecognitionInstance.onstart = () => {
      isMicActive = true;
      micBtn.classList.add('active');
      if (statusHint) statusHint.textContent = 'جاري الاستماع لصوتك... تحدث الآن';
    };

    speechRecognitionInstance.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      const textarea = document.getElementById('chat-textarea');
      if (textarea) {
        textarea.value = transcript;
        sendDirectMessage(transcript);
      }
    };

    speechRecognitionInstance.onerror = () => {
      stopMicRecording();
    };

    speechRecognitionInstance.onend = () => {
      stopMicRecording();
    };
  }

  micBtn.addEventListener('click', () => {
    if (!isMicActive) {
      startMicRecording();
    } else {
      stopMicRecording();
    }
  });
}

function startMicRecording() {
  const micBtn = document.getElementById('mic-toggle-btn');
  const statusHint = document.getElementById('mic-status-hint');
  isMicActive = true;
  if (micBtn) micBtn.classList.add('active');
  if (statusHint) statusHint.textContent = 'جاري الاستماع لصوتك (الميكروفون نشط)... تحدث الآن';

  if (speechRecognitionInstance) {
    try {
      speechRecognitionInstance.start();
    } catch {
      // already started or fallback
    }
  } else {
    // Graceful Voice Simulation Fallback
    setTimeout(() => {
      const character = CHARACTERS_DATA[currentCharacterIndex];
      const sampleQuestion = character.quickPrompts[Math.floor(Math.random() * character.quickPrompts.length)];
      const textarea = document.getElementById('chat-textarea');
      if (textarea) {
        typeWriterEffect(textarea, sampleQuestion, () => {
          stopMicRecording();
          sendDirectMessage(sampleQuestion);
        });
      }
    }, 1800);
  }
}

function stopMicRecording() {
  const micBtn = document.getElementById('mic-toggle-btn');
  const statusHint = document.getElementById('mic-status-hint');
  isMicActive = false;
  if (micBtn) micBtn.classList.remove('active');
  if (statusHint) statusHint.textContent = 'اضغط على الميكروفون للحديث الصوتي، أو اكتب استفسارك واضغط Enter';

  if (speechRecognitionInstance) {
    try {
      speechRecognitionInstance.stop();
    } catch {}
  }
}

function typeWriterEffect(element, text, callback) {
  element.value = '';
  let i = 0;
  const timer = setInterval(() => {
    if (i < text.length) {
      element.value += text.charAt(i);
      i++;
    } else {
      clearInterval(timer);
      if (callback) callback();
    }
  }, 45);
}

async function speakText(text) {
  if (!isSpeechSynthesisActive) return;
  const character = CHARACTERS_DATA[currentCharacterIndex];
  const voiceId = character.voice_name || "ar-XA-Wavenet-B"; // Fallback to a valid Google voice
  
  try {
    const response = await fetch('/api/v1/chat/audio', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        voice_id: voiceId
      })
    });

    if (!response.ok) {
      throw new Error("TTS generation failed");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    
    // Attempt to play the audio
    audio.play().catch(e => console.error("Audio playback error:", e));

  } catch (error) {
    console.warn('[Safar 360] Fallback to browser TTS:', error);
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ar-SA';
    window.speechSynthesis.speak(utterance);
  }
}

// =============================================================================
// 9. Interactive Canvas 360° Scene & Views
// =============================================================================
function switchCanvasTab(tabName) {
  currentCanvasTab = tabName;
  const tabBtns = document.querySelectorAll('.canvas-tab-btn');
  const panes = document.querySelectorAll('.canvas-view-pane');

  tabBtns.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
    btn.setAttribute('aria-selected', btn.dataset.tab === tabName ? 'true' : 'false');
  });

  panes.forEach(pane => {
    pane.classList.toggle('active', pane.id === `pane-${tabName}`);
  });
}

function switchToCanvasTab(tabName) {
  switchCanvasTab(tabName);
  document.getElementById('interactive-canvas-panel')?.scrollIntoView({ behavior: 'smooth' });
}

// 3D Parallax Tilt on Scene View
function setupScene3DTilt() {
  const container = document.getElementById('scene-360-viewport');
  const card = document.getElementById('avatar-card-interactive');
  const stage = document.getElementById('avatar-stage');
  const bg = document.getElementById('scene-panorama-bg');
  const resetBtn = document.getElementById('btn-tilt-reset');

  if (!container || !card) return;

  container.addEventListener('mousemove', (e) => {
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left - (rect.width / 2);
    const y = e.clientY - rect.top - (rect.height / 2);

    const tiltX = -(y / rect.height) * 25;
    const tiltY = (x / rect.width) * 25;

    card.style.transform = `rotateX(${tiltX}deg) rotateY(${tiltY}deg) translateZ(40px)`;
    if (stage) stage.style.transform = `translate3d(${x * 0.05}px, ${y * 0.05}px, 0)`;
    if (bg) bg.style.transform = `scale(1.1) translate3d(${-x * 0.04}px, ${-y * 0.04}px, 0)`;
  });

  container.addEventListener('mouseleave', () => {
    resetTilt();
  });

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      resetTilt();
      showToastNotification('تمت إعادة ضبط الزاوية 360°');
    });
  }

  function resetTilt() {
    card.style.transform = 'rotateX(0deg) rotateY(0deg) translateZ(30px)';
    if (stage) stage.style.transform = 'translate3d(0, 0, 0)';
    if (bg) bg.style.transform = 'scale(1) translate3d(0, 0, 0)';
  }

  // Fullscreen trigger
  document.getElementById('btn-canvas-fullscreen')?.addEventListener('click', () => {
    const canvasPanel = document.getElementById('interactive-canvas-panel');
    if (!document.fullscreenElement) {
      canvasPanel?.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  });
}

// Render Timeline
function renderTimeline(character) {
  const track = document.getElementById('character-timeline-track');
  if (!track) return;
  track.innerHTML = '';

  character.timeline.forEach(event => {
    const node = document.createElement('div');
    node.className = 'timeline-node';
    node.innerHTML = `
      <div class="node-marker"></div>
      <div class="node-card">
        <div class="node-year">${event.year}</div>
        <h4 class="node-event-title">${event.title}</h4>
        <p class="node-desc">${event.desc}</p>
      </div>
    `;
    track.appendChild(node);
  });
}

// Render Artifacts
function renderArtifacts(character) {
  const grid = document.getElementById('character-artifacts-grid');
  if (!grid) return;
  grid.innerHTML = '';

  character.artifacts.forEach(artifact => {
    const card = document.createElement('div');
    card.className = 'artifact-card-item';
    card.innerHTML = `
      <div class="artifact-preview-box">${artifact.icon}</div>
      <h4 class="artifact-name">${artifact.name}</h4>
      <span class="artifact-type">${artifact.type}</span>
      <p class="artifact-desc">${artifact.desc}</p>
      <button class="artifact-action-btn" onclick="askAboutSpecificArtifact('${artifact.name}')">
        حاور الشخصية عن الأثر ✦
      </button>
    `;
    grid.appendChild(card);
  });
}

// Render Map
function renderMap(character) {
  const board = document.getElementById('character-map-board');
  if (!board) return;

  const locationsHtml = character.mapLocations.map((loc, idx) => `
    <div class="map-city-tag" style="margin-bottom: 0.8rem; padding: 0.6rem 1rem; background: rgba(23, 27, 35, 0.85); border: 1px solid var(--accent-gold); border-radius: 8px; display: flex; align-items: center; justify-content: space-between;">
      <div>
        <strong style="color: var(--accent-gold-hover); font-size: 0.95rem;">📍 ${idx + 1}. ${loc.name}</strong>
        <p style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 2px;">${loc.desc}</p>
      </div>
      <button class="artifact-action-btn" onclick="sendDirectMessage('حدثني عن دور مدينة ${loc.name} في مسيرتك وإنجازاتك.')">
        استكشف
      </button>
    </div>
  `).join('');

  board.innerHTML = `
    <div style="display: grid; grid-template-columns: 1fr; gap: 1rem;">
      <div style="background: #090c10; border-radius: 12px; padding: 1.25rem; border: 1px solid var(--border-color); text-align: center; position: relative;">
        <!-- Stylized Historical Compass & World Grid representation -->
        <svg viewBox="0 0 600 240" style="width: 100%; max-height: 220px;" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Antique Latitude / Longitude lines -->
          <ellipse cx="300" cy="120" rx="260" ry="100" stroke="rgba(212,175,55,0.2)" stroke-width="1.5" stroke-dasharray="4 4"/>
          <ellipse cx="300" cy="120" rx="160" ry="60" stroke="rgba(212,175,55,0.15)" stroke-width="1"/>
          <line x1="40" y1="120" x2="560" y2="120" stroke="rgba(212,175,55,0.3)" stroke-width="1.5"/>
          <line x1="300" y1="20" x2="300" y2="220" stroke="rgba(212,175,55,0.3)" stroke-width="1.5"/>
          
          <!-- Animated Journey Route Curve -->
          <path d="M120 140 Q 240 70 300 130 T 480 100" stroke="#f1c40f" stroke-width="2.5" class="map-route-line"/>
          
          <!-- Waypoint Pins -->
          <circle cx="120" cy="140" r="6" fill="#e74c3c" stroke="#fff" stroke-width="2"/>
          <text x="120" y="165" fill="#f1c40f" font-size="12" text-anchor="middle" font-weight="bold">${character.mapLocations[0]?.name || 'البداية'}</text>
          
          <circle cx="300" cy="130" r="6" fill="#f1c40f" stroke="#0a0c0e" stroke-width="2"/>
          <text x="300" y="110" fill="#fff" font-size="12" text-anchor="middle" font-weight="bold">${character.mapLocations[1]?.name || 'المحطة'}</text>
          
          <circle cx="480" cy="100" r="6" fill="#2ecc71" stroke="#fff" stroke-width="2"/>
          <text x="480" y="85" fill="#2ecc71" font-size="12" text-anchor="middle" font-weight="bold">${character.mapLocations[2]?.name || 'المقصد'}</text>
        </svg>
        <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.5rem;">
          مسار التحركات الاستراتيجية والرحلات العلمية الموثقة عبر التاريخ
        </div>
      </div>
      <div style="display: flex; flex-direction: column; gap: 0.5rem;">
        <h4 style="font-size: 0.95rem; color: var(--accent-gold); margin-bottom: 0.5rem;">المحطات والمدن الرئيسية :</h4>
        ${locationsHtml}
      </div>
    </div>
  `;
}

// Hotspot Modal Functions
let activeHotspotId = null;
function openHotspotModal(id) {
  activeHotspotId = id;
  const character = CHARACTERS_DATA[currentCharacterIndex];
  const hotspot = character.hotspots.find(h => h.id === id) || character.hotspots[0];

  const modal = document.getElementById('hotspot-modal');
  const title = document.getElementById('modal-title');
  const body = document.getElementById('modal-body');

  if (title) title.textContent = hotspot.title;
  if (body) body.textContent = hotspot.desc;
  if (modal) modal.classList.add('active');
}

function closeHotspotModal() {
  const modal = document.getElementById('hotspot-modal');
  if (modal) modal.classList.remove('active');
}

function askAboutHotspot() {
  const character = CHARACTERS_DATA[currentCharacterIndex];
  const hotspot = character.hotspots.find(h => h.id === activeHotspotId) || character.hotspots[0];
  closeHotspotModal();
  sendDirectMessage(`حدثني عن أسرار ${hotspot.title} ودوره في إنجازاتك التاريخية.`);
}

function askAboutSpecificArtifact(artifactName) {
  sendDirectMessage(`أخبرني بالمزيد عن قصة ${artifactName} وكيف ارتبط بمسيرتك.`);
}

// =============================================================================
// 10. Web Audio Ambience Synthesizer (Desert Wind & Oud Drone)
// =============================================================================
function setupAudioAmbience() {
  const audioBtn = document.getElementById('audio-toggle-btn');
  const label = document.getElementById('audio-btn-label');

  if (!audioBtn) return;

  audioBtn.addEventListener('click', () => {
    if (!isAudioAmbiencePlaying) {
      startAmbientAudio();
      isAudioAmbiencePlaying = true;
      audioBtn.classList.add('playing');
      if (label) label.textContent = 'صوت الأثير مفعّل';
      showToastNotification('تم تشغيل أثير الموسيقى والأجواء التاريخية');
    } else {
      stopAmbientAudio();
      isAudioAmbiencePlaying = false;
      audioBtn.classList.remove('playing');
      if (label) label.textContent = 'أثير الصحراء';
      showToastNotification('تم كتم الصوت البيئي');
    }
  });
}

function startAmbientAudio() {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;

    if (!audioContext) {
      audioContext = new AudioContextClass();
    }
    if (audioContext.state === 'suspended') {
      audioContext.resume();
    }

    // Gentle harmonized chord (D - A - D - F# oriental drone)
    ambientGainNode = audioContext.createGain();
    ambientGainNode.gain.setValueAtTime(0.01, audioContext.currentTime);
    ambientGainNode.gain.exponentialRampToValueAtTime(0.12, audioContext.currentTime + 3);
    ambientGainNode.connect(audioContext.destination);

    // Warm Low Drone Oscillator
    ambientOscillator = audioContext.createOscillator();
    ambientOscillator.type = 'sine';
    ambientOscillator.frequency.setValueAtTime(146.83, audioContext.currentTime); // D3
    ambientOscillator.connect(ambientGainNode);
    ambientOscillator.start();

    // Subtle 5th overtone (A3)
    const overtone = audioContext.createOscillator();
    overtone.type = 'triangle';
    overtone.frequency.setValueAtTime(220.00, audioContext.currentTime); // A3
    const overtoneGain = audioContext.createGain();
    overtoneGain.gain.setValueAtTime(0.04, audioContext.currentTime);
    overtone.connect(overtoneGain);
    overtoneGain.connect(ambientGainNode);
    overtone.start();

  } catch (err) {
    console.warn('Audio ambience synthesis error:', err);
  }
}

function stopAmbientAudio() {
  if (ambientGainNode && audioContext) {
    ambientGainNode.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.8);
    setTimeout(() => {
      try {
        ambientOscillator?.stop();
        audioContext?.suspend();
      } catch {}
    }, 900);
  }
}

// =============================================================================
// 11. HTML5 Canvas Particles (Floating Golden Dust)
// =============================================================================
function initParticleBackground() {
  const canvas = document.getElementById('particles-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particlesCount = 45;
  const particles = [];

  for (let i = 0; i < particlesCount; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      size: Math.random() * 2.2 + 0.5,
      speedX: (Math.random() - 0.5) * 0.4,
      speedY: -Math.random() * 0.5 - 0.1,
      opacity: Math.random() * 0.6 + 0.2,
      pulseSpeed: Math.random() * 0.02 + 0.01,
      angle: Math.random() * Math.PI * 2
    });
  }

  function render() {
    ctx.clearRect(0, 0, width, height);

    particles.forEach(p => {
      p.x += p.speedX;
      p.y += p.speedY;
      p.angle += p.pulseSpeed;

      if (p.y < 0) {
        p.y = height + 10;
        p.x = Math.random() * width;
      }
      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;

      const currentOpacity = p.opacity + Math.sin(p.angle) * 0.2;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(212, 175, 55, ${Math.max(0.05, currentOpacity)})`;
      ctx.shadowBlur = 8;
      ctx.shadowColor = '#d4af37';
      ctx.fill();
    });

    requestAnimationFrame(render);
  }

  render();
}

// =============================================================================
// 12. Utilities & Helper Functions
// =============================================================================
function setMobileView(view) {
  const chatPanel = document.getElementById('chat-interface-panel');
  const canvasPanel = document.getElementById('interactive-canvas-panel');
  const btnChat = document.getElementById('btn-show-chat');
  const btnCanvas = document.getElementById('btn-show-canvas');

  if (view === 'chat') {
    if (chatPanel) chatPanel.style.display = 'flex';
    if (canvasPanel) canvasPanel.style.display = 'none';
    btnChat?.classList.add('active');
    btnCanvas?.classList.remove('active');
  } else {
    if (chatPanel) chatPanel.style.display = 'none';
    if (canvasPanel) canvasPanel.style.display = 'flex';
    btnChat?.classList.remove('active');
    btnCanvas?.classList.add('active');
  }
}

function showToastNotification(message) {
  let toast = document.getElementById('app-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'app-toast';
    toast.style.cssText = `
      position: fixed;
      bottom: 25px;
      right: 50%;
      transform: translateX(50%);
      background: rgba(18, 21, 27, 0.95);
      border: 1px solid var(--accent-gold);
      color: var(--text-primary);
      padding: 0.65rem 1.4rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
      box-shadow: 0 8px 25px rgba(0,0,0,0.8), 0 0 15px rgba(212,175,55,0.3);
      z-index: 1000;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.3s ease, transform 0.3s ease;
      font-family: var(--font-cairo);
    `;
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.style.opacity = '1';
  toast.style.transform = 'translateX(50%) translateY(0)';

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(50%) translateY(10px)';
  }, 2600);
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
