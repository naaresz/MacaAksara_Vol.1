export function speakJavanese(text: string, onStart?: () => void, onEnd?: () => void) {
  const cleanText = text.replace("Pengucapan Jawa:", "").trim();
  if (!cleanText || cleanText === "-") return;

  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = "id-ID"; // ID voice pronounces Javanese letters nicely
    utterance.pitch = 1.0;
    utterance.rate = 0.85;

    if (onStart) {
      utterance.onstart = onStart;
    }
    if (onEnd) {
      utterance.onend = onEnd;
      utterance.onerror = onEnd;
    }

    window.speechSynthesis.speak(utterance);
  } else {
    alert("Pelafalan suara tidak didukung di peramban ini.");
  }
}
