const fs = require('fs');
const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

// Inside createStreamingBotMessage, we should be able to parse Markdown image tags.
// Let's replace the loop inside streamChatMessageFromBackend:
const oldLoop = `          const parsed = JSON.parse(dataStr);
          const token = parsed.choices?.[0]?.delta?.content || '';
          if (token) {
            accumulatedText += token;
            bodyElem.textContent = accumulatedText;
            const container = document.getElementById('chat-messages-container');
            if (container) container.scrollTop = container.scrollHeight;
          }`;

const newLoop = `          const parsed = JSON.parse(dataStr);
          const token = parsed.choices?.[0]?.delta?.content || '';
          if (token) {
            accumulatedText += token;
            
            // Check for [GENERATE_IMAGE: ...] tag being streamed and replace with skeleton
            let displayHtml = escapeHtml(accumulatedText).replace(/\\n/g, '<br>');
            if (displayHtml.includes('[GENERATE_IMAGE:')) {
               displayHtml = displayHtml.replace(/\\[GENERATE_IMAGE:.*?(?:\\]|$)/g, '<div class="image-skeleton" style="width:100%; height:200px; background:rgba(212,175,55,0.1); border:1px dashed var(--accent-gold); border-radius:8px; display:flex; align-items:center; justify-content:center; color:var(--accent-gold); animation: pulse 1.5s infinite;">جاري رسم المشهد...</div>');
            }
            
            // Parse Markdown images from backend ![Generated Image](url)
            displayHtml = displayHtml.replace(/!\\[.*?\\]\\((.*?)\\)/g, '<img src="$1" alt="Generated Scene" style="max-width:100%; border-radius:8px; margin-top:8px; border:1px solid var(--accent-gold);">');
            
            bodyElem.innerHTML = displayHtml;
            const container = document.getElementById('chat-messages-container');
            if (container) container.scrollTop = container.scrollHeight;
          }`;

appJs = appJs.replace(oldLoop, newLoop);
fs.writeFileSync(appJsPath, appJs, 'utf8');
