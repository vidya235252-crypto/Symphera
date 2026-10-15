// Fake responses in the contract shape. Used while the backend isn't ready,
// and kept afterwards as a fallback toggle for demos.

const MOCKS = {
  routine: {
    detected_language: 'en',
    summary: 'Your periods are infrequent and you have noticed weight gain.',
    possible_patterns: [
      {
        pattern: 'Irregular cycles with weight gain',
        note: 'Commonly associated with hormonal conditions such as PCOS, among others.'
      },
      {
        pattern: 'Acne or extra hair growth alongside irregular cycles',
        note: 'Can be linked to hormone changes. A doctor can check what is behind it.'
      }
    ],
    red_flags: [],
    urgency: 'soon',
    suggested_specialist: 'gynecologist',
    questions_for_doctor: [
      'Which blood tests or scans could explain my irregular cycles?',
      'Could thyroid or other conditions cause this?',
      'Which lifestyle changes are worth discussing with you?'
    ],
    what_to_track: [
      'Start date of each period',
      'Weight changes',
      'Acne or extra hair growth'
    ],
    disclaimer: 'This is general information, not a diagnosis. Please consult a doctor.'
  },

  urgent: {
    detected_language: 'en',
    summary: 'You describe very heavy bleeding and feeling faint.',
    possible_patterns: [],
    red_flags: ['Very heavy bleeding', 'Feeling faint or dizzy'],
    urgency: 'urgent',
    suggested_specialist: 'gynecologist',
    questions_for_doctor: ['What could be causing this heavy bleeding?'],
    what_to_track: ['Number of pads used per hour', 'When the bleeding started'],
    disclaimer: 'This is general information, not a diagnosis. Please seek medical care now.'
  },

  // What the backend sends when the LLM or validation fails
  fallback: {
    detected_language: 'en',
    summary: '',
    possible_patterns: [],
    red_flags: [],
    urgency: 'soon',
    suggested_specialist: 'general physician',
    questions_for_doctor: [],
    what_to_track: [],
    disclaimer: 'This is not a diagnosis. Please consult a doctor.',
    fallback: true
  }
};

// Picks a mock based on keywords in the text, so you can trigger each state while testing:
//   "heavy bleeding" or "faint"  -> urgent (red banner)
//   "fallback"                   -> fallback response
//   "error"                      -> throws, to test the error state
//   anything else                -> routine
function mockAnalyze(text) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (/error/i.test(text)) return reject(new Error('mock error'));
      if (/fallback/i.test(text)) return resolve(MOCKS.fallback);
      if (/bleed|faint|severe|खून|चक्कर|ರಕ್ತ/i.test(text)) return resolve(MOCKS.urgent);
      resolve(MOCKS.routine);
    }, 800); // fake delay so you can see the loading state
  });
}