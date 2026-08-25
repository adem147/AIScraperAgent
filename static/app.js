document.addEventListener('DOMContentLoaded', () => {
  // UI Elements
  const statTotalCount = document.getElementById('stat-total-count');
  const statVectorDim = document.getElementById('stat-vector-dim');
  const statModelName = document.getElementById('stat-model-name');
  const statTopScore = document.getElementById('stat-top-score');

  const btnTriggerScrape = document.getElementById('btn-trigger-scrape');
  const btnRunScraper2 = document.getElementById('btn-run-scraper-2');
  const terminalOutput = document.getElementById('terminal-output');

  const searchInput = document.getElementById('search-input');
  const sourceFilter = document.getElementById('source-filter');
  const btnSearch = document.getElementById('btn-search');
  const searchPills = document.querySelectorAll('.pill');
  const opportunitiesGrid = document.getElementById('opportunities-grid');
  const resultsCountText = document.getElementById('results-count-text');

  async function loadSources() {
    const res = await fetch('/api/sources');
    if (!res.ok) return;
    const sources = await res.json();
    console.log('Sources loaded');
    sourceFilter.innerHTML = '<option value="">All sources</option>' + sources.map(source =>
      `<option value="${source.id}">${escapeHtml(source.title || 'Untitled source')}</option>`
    ).join('');
  }

  // Terminal logging helper
  function logTerminal(message, type = 'sys') {
    const line = document.createElement('div');
    line.className = `line ${type}`;
    if (type === 'prompt') {
      line.innerHTML = `<span class="prompt">$</span> ${message}`;
    } else {
      line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    }
    terminalOutput.appendChild(line);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
  }

  // Fetch initial stats
  async function fetchStats() {
    try {
      const res = await fetch('/api/stats');
      if (!res.ok) return;
      const data = await res.json();

      statTotalCount.textContent = data.points_count || 4;
      statVectorDim.textContent = data.vector_dimension || 384;
      statModelName.textContent = data.embedding_model || 'all-MiniLM-L6-v2';

      logTerminal(`Fetched system stats: ${data.points_count} vector points registered.`, 'sys');
    } catch (err) {
      console.warn('Failed to load stats:', err);
    }
  }

  // Render opportunities cards
  function renderOpportunities(items) {
    if (sourceFilter.value) {
      items = items.filter(item => String(item.source_id) === sourceFilter.value);
    }
    opportunitiesGrid.innerHTML = '';

    if (!items || items.length === 0) {
      opportunitiesGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: #9ca3af;">
          <i class="fa-solid fa-folder-open" style="font-size: 2.5rem; margin-bottom: 1rem;"></i>
          <p>No procurement opportunities found matching your query.</p>
        </div>
      `;
      resultsCountText.textContent = '0 opportunities found';
      return;
    }

    resultsCountText.textContent = `Displaying ${items.length} opportunity match${items.length > 1 ? 'es' : ''}`;

    let maxScore = 0;

    items.forEach(item => {
      if (item.score > maxScore) maxScore = item.score;

      const card = document.createElement('div');
      card.className = 'opportunity-card';
      card.innerHTML = `
        <div>
          <div class="card-top">
            <span class="score-badge"><i class="fa-solid fa-bullseye"></i> ${(item.score * 100).toFixed(1)}% Match</span>
            <span class="tag-item" style="color: #6ee7b7;"><i class="fa-solid fa-earth-americas"></i> ${item.country || 'Global'}</span>
          </div>
          <h3 class="card-title">${escapeHtml(item.title)}</h3>
          <p class="card-source"><i class="fa-solid fa-database"></i> Source: ${escapeHtml(item.source_title || 'Unknown source')}</p>
          <p class="card-desc">${escapeHtml(item.description)}</p>
          <div class="card-tags">
            <span class="tag-item"><i class="fa-solid fa-building"></i> ${escapeHtml(item.organization || 'World Bank')}</span>
            <span class="tag-item"><i class="fa-solid fa-layer-group"></i> ${escapeHtml(item.sector || 'ICT')}</span>
          </div>
        </div>
        <div class="card-footer">
          <span><i class="fa-solid fa-calendar-clock"></i> Deadline: ${escapeHtml(item.submission_deadline || 'N/A')}</span>
          <a href="${item.url || '#'}" target="_blank" rel="noopener" class="card-link">View Source <i class="fa-solid fa-arrow-up-right-from-square"></i></a>
        </div>
      `;
      opportunitiesGrid.appendChild(card);
    });

    if (maxScore > 0) {
      statTopScore.textContent = maxScore.toFixed(3);
    }
  }

  function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/[&<>"']/g, function(m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
    });
  }

  // Execute Vector Search
  async function performSearch(query) {
    if (!query) return;

    logTerminal(`Executing vector similarity search for query: "${query}"`, 'prompt');
    logTerminal(`Encoding query with SentenceTransformer (all-MiniLM-L6-v2)...`, 'sys');

    try {
      const res = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
      const data = await res.json();

      logTerminal(`Qdrant vector query completed. Retrived ${data.count} ranked results.`, 'success');
      renderOpportunities(data.results);
    } catch (err) {
      logTerminal(`Search error: ${err.message}`, 'sys');
    }
  }

  // Trigger Live Scraping Pipeline
  async function triggerScraper() {
    console.log("innnnnnnnnnnnnn")
    logTerminal('python sc2.py --live-intercept', 'prompt');
    logTerminal('Launching Playwright Chromium headless instance...', 'sys');
    logTerminal('Intercepting outgoing fetch/XHR network requests on World Bank Opportunities...', 'sys');

    btnTriggerScrape.disabled = true;
    btnRunScraper2.disabled = true;
    btnTriggerScrape.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scraping & Vectorizing...';

    try {
      const res = await fetch('/api/scrape', { method: 'POST' });
      const data = await res.json();

      if (data.status === 'success') {
        logTerminal(`Scraper finished successfully! Cleaned & embedded ${data.stored_count} opportunities into Qdrant.`, 'success');
        if (data.top_endpoints && data.top_endpoints.length > 0) {
          logTerminal(`Top ranked endpoint: ${data.top_endpoints[0].url} (Similarity Score: ${data.top_endpoints[0].similarity_score})`, 'highlight');
        }
        await fetchStats();
        await performSearch(searchInput.value || 'cybersecurity');
      } else {
        logTerminal(`Scraper notification: ${data.message}`, 'sys');
      }
    } catch (err) {
      logTerminal(`Scrape error: ${err.message}`, 'sys');
    } finally {
      btnTriggerScrape.disabled = false;
      btnRunScraper2.disabled = false;
      btnTriggerScrape.innerHTML = '<i class="fa-solid fa-play"></i> Run Live Scraper Pipeline';
    }
  }

  // Event Listeners
  btnSearch.addEventListener('click', () => performSearch(searchInput.value.trim()));
  sourceFilter.addEventListener('change', () => performSearch(searchInput.value.trim()));

  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      performSearch(searchInput.value.trim());
    }
  });

  searchPills.forEach(pill => {
    pill.addEventListener('click', () => {
      const query = pill.getAttribute('data-query');
      searchInput.value = query;
      performSearch(query);
    });
  });

  btnTriggerScrape.addEventListener('click', triggerScraper);
  btnRunScraper2.addEventListener('click', triggerScraper);

  // Initialize
  fetchStats();
  loadSources();
  console.log("inisialised")
  performSearch();
});
