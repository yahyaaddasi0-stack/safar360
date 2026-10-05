const fs = require('fs');
const appJsPath = '/home/ubuntu/safar360/app.js';
let appJs = fs.readFileSync(appJsPath, 'utf8');

const replacement = `async function speakText(text) {
  if (!isSpeechSynthesisActive) return;
  const character = CHARACTERS_DATA[currentCharacterIndex];
  const voiceId = character.voice_name || "ar-XA-Wavenet-B"; // Fallback to a valid Google voice
  
  try {
    const response = await fetch('/api/v1/chat/audio', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        voice_id: voiceId
      })
    });

    if (!response.ok) {
      throw new Error("TTS generation failed");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    
    // Attempt to play the audio
    audio.play().catch(e => console.error("Audio playback error:", e));

  } catch (error) {
    console.warn('[Safar 360] Fallback to browser TTS:', error);
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ar-SA';
    window.speechSynthesis.speak(utterance);
  }
}`;

appJs = appJs.replace(/function speakText\(text\) \{[\s\S]*?window\.speechSynthesis\.speak\(utterance\);\n\}/, replacement);
fs.writeFileSync(appJsPath, appJs, 'utf8');
