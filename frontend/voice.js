// Voice input using the browser's Web Speech API. No server or Python involved.
const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
const micBtn = document.getElementById('mic');
const micStatus = document.getElementById('mic-status');
const SPEECH_LANG = { en: 'en-IN', hi: 'hi-IN', kn: 'kn-IN' };

// Unsupported browser: the mic button simply stays hidden (it has `hidden` in index.html)
if (SpeechRec) {
  micBtn.hidden = false;
  let recognition = null;

  const stopListening = () => {
    if (recognition) recognition.stop();
  };

  micBtn.addEventListener('click', () => {
    // Second click stops listening
    if (recognition) {
      stopListening();
      return;
    }

    recognition = new SpeechRec();
    recognition.lang = SPEECH_LANG[currentLang];
    recognition.interimResults = true;
    recognition.continuous = false;

    // Keep whatever the user already typed and add the spoken words after it
    const existing = els.text.value.trim();
    const base = existing ? existing + ' ' : '';

    recognition.onstart = () => {
      micBtn.classList.add('listening');
      micBtn.textContent = t('stop');
      micStatus.textContent = t('listening');
    };

    recognition.onresult = (event) => {
      const spoken = Array.from(event.results).map(r => r[0].transcript).join(' ');
      els.text.value = base + spoken;
    };

    recognition.onerror = (event) => {
      // "no-speech" and "aborted" are normal, so stay quiet for those
      if (event.error === 'no-speech' || event.error === 'aborted') return;
      micStatus.textContent = event.error === 'not-allowed' ? t('mic_denied') : t('mic_error');
    };

    recognition.onend = () => {
      micBtn.classList.remove('listening');
      micBtn.textContent = t('mic');
      if (micStatus.textContent === t('listening')) micStatus.textContent = '';
      recognition = null;
    };

    recognition.start();
  });

  // Changing language mid-recording stops it, so the wrong language isn't used
  document.querySelectorAll('.langs button').forEach(btn => {
    btn.addEventListener('click', stopListening);
  });
}