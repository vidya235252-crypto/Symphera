const els = {
  text: document.getElementById('symptoms'),
  analyze: document.getElementById('analyze'),
  status: document.getElementById('status'),
  results: document.getElementById('results'),
  mock: document.getElementById('use-mock')
};

// Demo toggle stays hidden from jurors. Open the site with ?demo to show it.
if (new URLSearchParams(window.location.search).has("demo")) {
  const demoToggle = document.querySelector(".demo-toggle");
  const footer = document.querySelector("footer");

  if (demoToggle) {
    demoToggle.hidden = false;
  }

  if (footer) {
    footer.hidden = false;
  }
}

let lastResult = null;
let busy = false;

/* ---------- Helpers ---------- */

// Builds an element. Uses textContent only, so model output can never inject HTML.
function make(tag, className, text) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  if (text) e.textContent = text;
  return e;
}

function makeList(items) {
  const ul = make('ul');
  items.forEach(item => ul.append(make('li', '', item)));
  return ul;
}

function makeCard(title, ...children) {
  const card = make('div', 'card');
  card.append(make('h2', '', title), ...children);
  return card;
}

function setStatus(message, isError) {
  els.status.textContent = message;
  els.status.className = isError ? 'error' : '';
}

/* ---------- API ---------- */

// Relative path on purpose: works on any domain with zero code changes.
async function callBackend(text) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 45000);
  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language_hint: currentLang }),
      signal: controller.signal
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

function getAnalysis(text) {
  return els.mock.checked ? mockAnalyze(text) : callBackend(text);
}

/* ---------- Rendering ---------- */

function render(d) {
  lastResult = d;
  els.results.replaceChildren();

  const flags = d.red_flags || [];

  // Red banner first: the safety differentiator
  if (d.urgency === 'urgent' || flags.length) {
    const banner = make('div', 'banner');
    banner.setAttribute('role', 'alert');
    banner.append(make('h2', '', t('h_flags')));
    if (flags.length) banner.append(makeList(flags));
    els.results.append(banner);
  }

  if (d.fallback) {
  els.results.append(
    makeCard(t('h_summary'), make('p', '', d.summary || t('fallback')))
  );
} else if (d.summary) {
  els.results.append(makeCard(t('h_summary'), make('p', '', d.summary)));
}

  if ((d.possible_patterns || []).length) {
    const card = makeCard(t('h_patterns'));
    d.possible_patterns.forEach(p => {
      card.append(make('p', '', p.pattern), make('p', 'note', p.note));
    });
    els.results.append(card);
  }

  if (d.urgency) {
    const label = t('urgency')[d.urgency] || d.urgency;
    els.results.append(makeCard(t('h_urgency'), make('span', 'pill ' + d.urgency, label)));
  }

  if (d.suggested_specialist) {
    const label = t('specialist')[d.suggested_specialist] || d.suggested_specialist;
    els.results.append(makeCard(t('h_specialist'), make('p', '', label)));
  }

  if ((d.questions_for_doctor || []).length) {
    els.results.append(makeCard(t('h_questions'), makeList(d.questions_for_doctor)));
  }

  if ((d.what_to_track || []).length) {
    els.results.append(makeCard(t('h_track'), makeList(d.what_to_track)));
  }

  if (d.disclaimer) {
    els.results.append(make('p', 'disclaimer', d.disclaimer));
  }

  const printBtn = make('button', '', t('print'));
  printBtn.type = 'button';
  printBtn.addEventListener('click', () => window.print());
  els.results.append(printBtn);

  els.results.hidden = false;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  els.results.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth' });
}

/* ---------- Actions ---------- */

async function submit() {
  if (busy) return;
  const text = els.text.value.trim();
    if (text.length < 3) {
    setStatus(t('empty'), true);
    return;
  }

  busy = true;
  els.analyze.disabled = true;
  els.results.hidden = true;
  setStatus(t('loading'));

  try {
    render(await getAnalysis(text));
    setStatus('');
  } catch (err) {
    setStatus(t('error'), true);
  } finally {
    busy = false;
    els.analyze.disabled = false;
  }
}

els.analyze.addEventListener('click', submit);

document.querySelectorAll('.langs button').forEach(btn => {
  btn.addEventListener('click', () => {
    applyLanguage(btn.dataset.lang);
    setStatus('');
    if (lastResult) render(lastResult); // re-label the cards in the new language
  });
});