const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  await page.goto('http://127.0.0.1:3000/?mode=chat', { waitUntil: 'networkidle0' });
  
  console.log('Typing in chat...');
  await page.type('#chat-textarea', 'ارسم لي خريطة معركة حطين');
  await page.click('#chat-send-btn');
  
  console.log('Waiting for AI response...');
  // Wait for the pulse skeleton
  await page.waitForSelector('.image-skeleton', { timeout: 10000 }).catch(() => console.log('Skeleton not seen'));
  
  // Wait for the final image to render
  await page.waitForSelector('.chat-message-bubble img', { timeout: 15000 });
  console.log('Image rendered in chat successfully!');
  
  await page.screenshot({ path: '/home/ubuntu/chat_image_test.png', fullPage: true });
  await browser.close();
})();
