const fs = require('fs');
const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

const regex = /function generateCharacterResponse\(query, character\) \{[\s\S]*?return `نعم السؤال يا صاحبي؛ في عصرنا كنا نرى أن المعرفة والهمة هما جناحا كل نهضة حضارية\. ما الذي ترغب في استجلاء تفاصيله أكثر؟`;\n\}/m;

const replacement = `function generateCharacterResponse(query, character) {
  return "عذراً، فقدنا الاتصال بوعي الشخصية التاريخية بسبب انقطاع الخادم. يرجى المحاولة لاحقاً.";
}`;

appJs = appJs.replace(regex, replacement);

fs.writeFileSync(appJsPath, appJs, 'utf8');