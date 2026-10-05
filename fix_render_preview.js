const fs = require('fs');
const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

const regex = /const canvasType = character\.canvas_data \? character\.canvas_data\.type : 'interactive_map';[\s\S]*?\} else if \(canvasType === 'manuscript_viewer'\) \{/;

const newPreview = `const canvasType = character.canvas_data ? character.canvas_data.type : 'interactive_map';
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
  } else if (canvasType === 'manuscript_viewer') {`;

appJs = appJs.replace(regex, newPreview);
fs.writeFileSync(appJsPath, appJs, 'utf8');
