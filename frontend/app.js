const health = document.querySelector('#health');
const opportunityCount = document.querySelector('#opportunity-count');
const sourceCount = document.querySelector('#source-count');
const results = document.querySelector('#results');
const resultCount = document.querySelector('#result-count');
const query = document.querySelector('#query');
const sourceFilter = document.querySelector('#source-filter');
const deadlineFilter = document.querySelector('#deadline-filter');
const allView = document.querySelector('#all-view');
const relevantView = document.querySelector('#relevant-view');
const scrapeButton = document.querySelector('#scrape-button');
const scrapeStatus = document.querySelector('#scrape-status');
const smtpForm = document.querySelector('#smtp-form');
const smtpProvider = document.querySelector('#smtp-provider');
const smtpStatus = document.querySelector('#smtp-status');
const smtpPasswordHelp = document.querySelector('#smtp-password-help');
const settingsDialog = document.querySelector('#settings-dialog');
const settingsOpen = document.querySelector('#settings-open');
const settingsClose = document.querySelector('#settings-close');

function updatePasswordHelp() {
  const help = {
    gmail: 'Use a Gmail app password. Regular Gmail passwords are not accepted when two-step verification is enabled.',
    outlook: 'Use your Outlook / Microsoft 365 password or an app password if your organization requires one.',
    sendgrid: 'Use your SendGrid API key as the password. The username is usually apikey.',
  };
  smtpPasswordHelp.textContent = `${help[smtpProvider.value] || help.gmail} The password is never displayed in the frontend.`;
}

async function loadSmtpSettings() {
  const response = await fetch('/api/settings/smtp');
  if (!response.ok) throw new Error('Email settings unavailable');
  const data = await response.json();
  smtpProvider.innerHTML = Object.entries(data.providers).map(([key]) =>
    `<option value="${key}">${key === 'gmail' ? 'Gmail' : key === 'outlook' ? 'Outlook / Microsoft 365' : 'SendGrid'}</option>`
  ).join('');
  const settings = data.settings;
  document.querySelector('#smtp-sender').value = settings.sender || '';
  document.querySelector('#smtp-recipient').value = settings.recipient || '';
  document.querySelector('#smtp-username').value = settings.username || '';
  smtpProvider.value = settings.provider || 'gmail';
  updatePasswordHelp();
}

function escapeHtml(value = '') {
  return value.replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  }[character]));
}

function formatDate(value) {
  if (!value) return 'No deadline';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Invalid date';
  return `${String(date.getDate()).padStart(2, '0')}/${String(date.getMonth() + 1).padStart(2, '0')}/${date.getFullYear()}`;
}

function setApiStatus(isOnline) {
  health.className = isOnline ? 'health' : 'health offline';
  health.innerHTML = `<i></i> API ${isOnline ? 'connected' : 'down'}`;
}

async function fetchWithTimeout(url, options = {}, timeout = 5000) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeout);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    window.clearTimeout(timeoutId);
  }
}

function render(items) {
  resultCount.textContent = `${items.length} result${items.length === 1 ? '' : 's'}`;
  if (!items.length) {
    results.innerHTML = '<p class="empty">No opportunities match this search.</p>';
    return;
  }
  results.innerHTML = items.map(item => `
    <article class="opportunity">
      <div class="opportunity-main">
        <div class="opportunity-meta"><span>${escapeHtml(item.sector || 'General')}</span></div>
        <p class="opportunity-deadline">Deadline date: <strong>${escapeHtml(formatDate(item.submission_deadline))}</strong></p>
        <p class="opportunity-source">Source: <strong>${escapeHtml(item.source_title || 'Unknown source')}</strong></p>
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(item.description || 'No description available.')}</p>
      </div>
      <div class="opportunity-actions">
        ${item.url ? `<a class="view-link" href="${escapeHtml(item.url)}" target="_blank" rel="noopener">View opportunity &rarr;</a>` : ''}
        <button class="delete-button" data-id="${item.id}" type="button">Delete</button>
      </div>
    </article>`).join('');

  document.querySelectorAll('.delete-button').forEach(button => {
    button.addEventListener('click', () => deleteOpportunity(button.dataset.id));
  });
}

async function deleteOpportunity(id) {
  if (!window.confirm('Delete this opportunity permanently?')) return;
  const response = await fetch(`/api/opportunities/${id}`, { method: 'DELETE' });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || 'Delete failed');
  }
  await loadStats();
  await search();
}

async function loadStats() {
  const response = await fetch('/api/stats');
  if (!response.ok) throw new Error('Stats unavailable');
  const data = await response.json();
  opportunityCount.textContent = data.opportunities;
  sourceCount.textContent = data.sources;
}

async function loadSources() {
  const response = await fetch('/api/sources');
  if (!response.ok) throw new Error('Sources unavailable');
  const sources = await response.json();
  sourceFilter.innerHTML = '<option value="">All sources</option>' + sources.map(source =>
    `<option value="${source.id}">${escapeHtml(source.title || 'Untitled source')}</option>`
  ).join('');
}

async function search() {
  results.innerHTML = '<p class="empty">Searching...</p>';
  if (relevantView.classList.contains('active')) {
    const response = await fetch(`/api/search?query=${encodeURIComponent(query.value)}`);
    if (!response.ok) throw new Error('Qdrant search unavailable');
    const data = await response.json();
    render(data.results.filter(item => (!sourceFilter.value || String(item.source_id) === sourceFilter.value)
      && (!deadlineFilter.value || (item.submission_deadline && item.submission_deadline.slice(0, 10) >= deadlineFilter.value))));
    return;
  }
  const params = new URLSearchParams({ query: query.value });
  if (sourceFilter.value) params.set('source_id', sourceFilter.value);
  if (deadlineFilter.value) params.set('deadline_after', deadlineFilter.value);
  const response = await fetch(`/api/opportunities?${params}`);
  if (!response.ok) throw new Error('Search unavailable');
  const data = await response.json();
  render(data.results);
}

async function initialize() {
  try {
    const response = await fetchWithTimeout('/api/health');
    if (!response.ok) throw new Error();
    setApiStatus(true);
    await loadStats();
    await loadSources();
    await loadSmtpSettings();
    await search();
  } catch (error) {
    setApiStatus(false);
    results.innerHTML = '<p class="empty">Could not connect to the FastAPI backend.</p>';
  }
}

document.querySelector('#search-form').addEventListener('submit', event => {
  event.preventDefault();
  search().catch(() => { results.innerHTML = '<p class="empty">Search failed. Try again.</p>'; });
});

sourceFilter.addEventListener('change', () => {
  search().catch(() => { results.innerHTML = '<p class="empty">Search failed. Try again.</p>'; });
});

deadlineFilter.addEventListener('change', () => {
  search().catch(() => { results.innerHTML = '<p class="empty">Search failed. Try again.</p>'; });
});

function setView(view) {
  allView.classList.toggle('active', view === 'all');
  relevantView.classList.toggle('active', view === 'relevant');
  search().catch(() => { results.innerHTML = '<p class="empty">Search failed. Try again.</p>'; });
}

allView.addEventListener('click', () => setView('all'));
relevantView.addEventListener('click', () => setView('relevant'));
smtpProvider.addEventListener('change', updatePasswordHelp);

function openSettings() {
  if (typeof settingsDialog.showModal === 'function') {
    settingsDialog.showModal();
  } else {
    settingsDialog.setAttribute('open', '');
    settingsDialog.classList.add('is-open');
  }
}

function closeSettings() {
  if (typeof settingsDialog.close === 'function') {
    settingsDialog.close();
  }
  settingsDialog.classList.remove('is-open');
}

settingsOpen.addEventListener('click', openSettings);
settingsClose.addEventListener('click', closeSettings);
settingsDialog.addEventListener('click', event => {
  if (event.target === settingsDialog) closeSettings();
});

smtpForm.addEventListener('submit', async event => {
  event.preventDefault();
  smtpStatus.textContent = 'Saving...';
  const payload = {
    provider: smtpProvider.value,
    sender: document.querySelector('#smtp-sender').value,
    recipient: document.querySelector('#smtp-recipient').value,
    username: document.querySelector('#smtp-username').value,
    password: document.querySelector('#smtp-password').value,
  };
  try {
    const response = await fetch('/api/settings/smtp', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not save email settings');
    document.querySelector('#smtp-password').value = '';
    smtpStatus.textContent = 'Email settings saved.';
  } catch (error) {
    smtpStatus.textContent = error.message;
  }
});

scrapeButton.addEventListener('click', async () => {
  scrapeButton.disabled = true;
  scrapeStatus.textContent = 'Scraping sources...';
  try {
    const response = await fetch('/api/scrape', { method: 'POST' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Scrape failed');
    scrapeStatus.textContent = `Done. ${data.stored_count} opportunities stored.`;
    await loadStats();
    await search();
  } catch (error) {
    scrapeStatus.textContent = error.message;
  } finally {
    scrapeButton.disabled = false;
  }
});

initialize();
