const fs = require('fs');
const indexPath = '/home/ubuntu/safar360/index.html';
let html = fs.readFileSync(indexPath, 'utf8');

const headInjection = `  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700;800;900&family=Tajawal:wght@300;400;500;700;800;900&display=swap" rel="stylesheet">
  
  <!-- PWA Setup -->
  <link rel="manifest" href="manifest.json">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Safar 360">`;

html = html.replace('  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700;800;900&family=Tajawal:wght@300;400;500;700;800;900&display=swap" rel="stylesheet">', headInjection);

const bodyInjection = `  <script src="app.js"></script>
  
  <!-- PWA Service Worker Registration -->
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
          .then(reg => console.log('ServiceWorker registered:', reg.scope))
          .catch(err => console.error('ServiceWorker registration failed:', err));
      });
    }
  </script>
</body>`;

html = html.replace('  <script src="app.js"></script>\n</body>', bodyInjection);

fs.writeFileSync(indexPath, html, 'utf8');
