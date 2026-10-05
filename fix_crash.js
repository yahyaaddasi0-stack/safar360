const fs = require('fs');
const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

// 1. Fix resetChatMessages
appJs = appJs.replace(
/function resetChatMessages\(\) \{[\s\S]*?addBotMessage\(.*?;/m,
`function resetChatMessages() {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  const character = CHARACTERS_DATA[currentCharacterIndex];
  container.innerHTML = '';

  // Welcome message from character
  const greeting = character.quote || 'مرحباً بك! ماذا تود أن تسألني؟';
  addBotMessage(greeting, character.arabicName);`
);

// 2. Fix generateCharacterResponse
appJs = appJs.replace(
/function generateCharacterResponse\(query, character\) \{[\s\S]*?\}\n/m,
`function generateCharacterResponse(query, character) {
  return "عذراً، فقدنا الاتصال بوعي الشخصية التاريخية بسبب انقطاع الخادم. يرجى المحاولة لاحقاً.";
}\n`
);

fs.writeFileSync(appJsPath, appJs, 'utf8');
