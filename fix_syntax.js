const fs = require('fs');
const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

const badBlockRegex = /function generateCharacterResponse\(query, character\) \{\n  return "عذراً، فقدنا الاتصال بوعي الشخصية التاريخية بسبب انقطاع الخادم. يرجى المحاولة لاحقاً.";\n\}\n  \}\n  \/\/ Fallback intelligent tailored answers based on character persona[\s\S]*?return character\.dialogueResponses\.default;\n\}/;

const fixedBlock = `function generateCharacterResponse(query, character) {
  return "عذراً، فقدنا الاتصال بوعي الشخصية التاريخية بسبب انقطاع الخادم. يرجى المحاولة لاحقاً.";
}`;

appJs = appJs.replace(badBlockRegex, fixedBlock);

fs.writeFileSync(appJsPath, appJs, 'utf8');
