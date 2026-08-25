const health = document.querySelector('#health');
const opportunityCount = document.querySelector('#opportunity-count');
const sourceCount = document.querySelector('#source-count');
const results = document.querySelector('#results');
const resultCount = document.querySelector('#result-count');
const query = document.querySelector('#query');
const sourceFilter = document.querySelector('#source-filter');
const allView = document.querySelector('#all-view');
const relevantView = document.querySelector('#relevant-view');
const scrapeButton = document.querySelector('#scrape-button');
const scrapeStatus = document.querySelector('#scrape-status');

function escapeHtml(value = '') {
  return value.replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  }[character]));
}

function formatDate(value) {
  if (!value) return 'No deadline';
  return new Date(value).toLocaleDateString();
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
        <div class="opportunity-meta"><span>${escapeHtml(item.sector || 'General')}</span><span>${formatDate(item.submission_deadline)}</span></div>
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
    render(data.results.filter(item => !sourceFilter.value || String(item.source_id) === sourceFilter.value));
    return;
  }
  const params = new URLSearchParams({ query: query.value });
  if (sourceFilter.value) params.set('source_id', sourceFilter.value);
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

function setView(view) {
  allView.classList.toggle('active', view === 'all');
  relevantView.classList.toggle('active', view === 'relevant');
  search().catch(() => { results.innerHTML = '<p class="empty">Search failed. Try again.</p>'; });
}

allView.addEventListener('click', () => setView('all'));
relevantView.addEventListener('click', () => setView('relevant'));

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
