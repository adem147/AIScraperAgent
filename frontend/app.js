const health = document.querySelector('#health');
const opportunityCount = document.querySelector('#opportunity-count');
const sourceCount = document.querySelector('#source-count');
const results = document.querySelector('#results');
const resultCount = document.querySelector('#result-count');
const query = document.querySelector('#query');
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
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(item.description || 'No description available.')}</p>
      </div>
      <div class="opportunity-actions">
        ${item.url ? `<a class="view-link" href="${escapeHtml(item.url)}" target="_blank" rel="noopener">View source &rarr;</a>` : ''}
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

async function search() {
  results.innerHTML = '<p class="empty">Searching...</p>';
  const response = await fetch(`/api/opportunities?query=${encodeURIComponent(query.value)}`);
  if (!response.ok) throw new Error('Search unavailable');
  const data = await response.json();
  render(data.results);
}

async function initialize() {
  try {
    const response = await fetch('/api/health');
    if (!response.ok) throw new Error();
    health.innerHTML = '<i></i> API connected';
    await loadStats();
    await search();
  } catch (error) {
    health.className = 'health offline';
    health.innerHTML = '<i></i> API offline';
    results.innerHTML = '<p class="empty">Could not connect to the FastAPI backend.</p>';
  }
}

document.querySelector('#search-form').addEventListener('submit', event => {
  event.preventDefault();
  search().catch(() => { results.innerHTML = '<p class="empty">Search failed. Try again.</p>'; });
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
