const fs = require('fs');
const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

const newRenderCanvasPreview = `function renderCanvasPreview(character) {
  const frame = document.getElementById('canvas-preview-frame');
  if (!frame) return;

  const canvasType = character.canvas_data ? character.canvas_data.type : 'interactive_map';
  
  if (canvasType === 'interactive_map') {
    frame.innerHTML = '<div id="leaflet-map" style="width: 100%; height: 400px; border-radius: 8px;"></div>';
    setTimeout(() => {
      const mapCenter = character.canvas_data.data.center || [31.771959, 35.217018];
      const zoomLevel = character.canvas_data.data.zoom || 6;
      
      const map = L.map('leaflet-map').setView(mapCenter, zoomLevel);
      
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
      }).addTo(map);

      if (character.map_locations && character.map_locations.length > 0) {
        character.map_locations.forEach(loc => {
          L.marker(loc.coords).addTo(map)
            .bindPopup('<b>' + loc.name + '</b><br>' + loc.desc);
        });
      } else if (character.canvas_data.data.markers) {
        character.canvas_data.data.markers.forEach(loc => {
          L.marker(loc.coords).addTo(map)
            .bindPopup('<b>' + loc.name + '</b><br>' + loc.desc);
        });
      }
    }, 100);
  } else if (canvasType === 'timeline') {
    let timelineHtml = '<div class="vertical-timeline" style="padding: 1rem;">';
    const events = character.canvas_data.data.events || character.timeline || [];
    events.forEach((evt, idx) => {
      const year = evt.date || evt.year;
      timelineHtml += \`
        <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem; position: relative;">
          <div style="min-width: 60px; font-weight: bold; color: var(--accent-gold); text-align: left;">\${year}</div>
          <div style="width: 2px; background: var(--accent-gold); position: relative;">
            <div style="position: absolute; top: 0; left: -4px; width: 10px; height: 10px; border-radius: 50%; background: var(--accent-gold-hover);"></div>
          </div>
          <div>
            <h4 style="margin: 0; color: var(--text-primary);">\${evt.title}</h4>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.85rem; color: var(--text-secondary);">\${evt.desc}</p>
          </div>
        </div>
      \`;
    });
    timelineHtml += '</div>';
    frame.innerHTML = timelineHtml;
  } else if (canvasType === 'manuscript_viewer') {
    frame.innerHTML = \`
      <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; background: #1a1e24; border-radius: 8px; border: 1px solid var(--border-color); position: relative; overflow: hidden;">
        <div style="position: absolute; top: 1rem; right: 1rem; background: rgba(0,0,0,0.6); padding: 0.5rem; border-radius: 4px; color: var(--accent-gold);">
          📜 عارض المخطوطات
        </div>
        <img src="https://images.unsplash.com/photo-1583321500900-82807e458f3c?auto=format&fit=crop&q=80&w=800" alt="Manuscript" style="max-height: 100%; max-width: 100%; opacity: 0.8; filter: sepia(0.4);">
        <div style="position: absolute; bottom: 1rem; background: rgba(0,0,0,0.8); padding: 1rem; border-radius: 8px; border: 1px solid var(--accent-gold); color: #fff; max-width: 80%;">
          <div style="font-weight: bold; color: var(--accent-gold-hover); margin-bottom: 0.5rem;">تظليل تلقائي</div>
          <p style="margin:0; font-size: 0.9rem;">\${character.quote}</p>
        </div>
      </div>
    \`;
  }
}`;

appJs = appJs.replace(/function renderCanvasPreview\(character\) \{[\s\S]*?\}\n/, newRenderCanvasPreview + '\n');
fs.writeFileSync(appJsPath, appJs, 'utf8');
