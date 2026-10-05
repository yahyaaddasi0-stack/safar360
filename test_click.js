const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  
  await page.goto('http://127.0.0.1:3000', { waitUntil: 'networkidle0' });
  
  console.log('Clicking the first Direct Chat button...');
  await page.waitForSelector('.card-cta-btn');
  await page.click('.card-cta-btn');
  
  await new Promise(r => setTimeout(r, 2000)); //(2000); // wait for transitions
  
  const chatMode = await page.evaluate(() => document.body.classList.contains('in-chat-mode'));
  console.log('Is in chat mode?', chatMode);
  
  await browser.close();
})();
