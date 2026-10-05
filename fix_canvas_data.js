const fs = require('fs');
const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

// The issue: "Cannot read properties of undefined (reading 'data')" means character.canvas_data is defined but character.canvas_data.data is undefined, OR character.canvas_data is undefined but evaluated.

appJs = appJs.replace(/const canvasType = character\.canvas_data \? character\.canvas_data\.type : 'interactive_map';[\s\S]*?\} else if \(canvasType === 'manuscript_viewer'\) \{/,
`const canvasType = character.canvas_data ? character.canvas_data.type : 'interactive_map';
  const cData = character.canvas_data ? (character.canvas_data.data || {}) : {};
  
  if (canvasType === 'interactive_map') {
    frame.innerHTML = '<div id="leaflet-map" style="width: 100%; height: 400px; border-radius: 8px;"></div>';
    setTimeout(() => {
      const mapCenter = cData.center || [31.771959, 35.217018];
      const zoomLevel = cData.zoom || 6;
      
      const map = L.map('leaflet-map').setView(mapCenter, zoomLevel);
      
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
      }).addTo(map);

      if (character.map_locations && character.map_locations.length > 0) {
        character.map_locations.forEach(loc => {
          L.marker(loc.coords).addTo(map)
            .bindPopup('<b>' + loc.name + '</b><br>' + loc.desc);
        });
      } else if (cData.markers) {
        cData.markers.forEach(loc => {
          L.marker(loc.coords).addTo(map)
            .bindPopup('<b>' + loc.name + '</b><br>' + loc.desc);
        });
      }
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
  } else if (canvasType === 'manuscript_viewer') {`
);

// Map frontend expected variables properly from Backend
appJs = appJs.replace(/mapLocations: char\.map_locations \|\| char\.mapLocations \|\| \[\],/g, 
"mapLocations: char.map_locations || char.mapLocations || [],\n        canvas_data: char.canvas_data || {},");

fs.writeFileSync(appJsPath, appJs, 'utf8');
