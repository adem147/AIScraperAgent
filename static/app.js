document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.getElementById('table-body');
  const btnRun = document.getElementById('btn-run');
  const btnRefresh = document.getElementById('btn-refresh');
  const msgBox = document.getElementById('msg');
  const updateTime = document.getElementById('update-time');

  function showMessage(text, type = 'info', timeout = 5000) {
    msgBox.textContent = text;
    msgBox.className = `msg-box ${type}`;
    msgBox.classList.remove('hidden');
    if (timeout > 0) {
      setTimeout(() => {
        msgBox.classList.add('hidden');
      }, timeout);
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, m => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    })[m]);
  }

  async function loadResults() {
    try {
      tableBody.innerHTML = '<tr><td colspan="7" class="text-center">Loading...</td></tr>';
      const res = await fetch('/api/results/top5');
      const data = await res.json();
      const items = data.results || [];

      if (items.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" class="text-center">No results found in database. Click "Run main.py" to process opportunities.</td></tr>';
        return;
      }

      tableBody.innerHTML = '';
      items.forEach((item, index) => {
        const row = document.createElement('tr');
        const score = item.similarity_score_pct || (item.similarity_score ? `${(item.similarity_score * 100).toFixed(1)}%` : '-');
        const link = item.document_url && item.document_url !== '#' ? `<a href="${item.document_url}" target="_blank" class="link-action">View</a>` : '-';

        row.innerHTML = `
          <td>${index + 1}</td>
          <td>
            <div class="item-title">${escapeHtml(item.title)}</div>
            ${item.description ? `<div class="item-desc">${escapeHtml(item.description.slice(0, 180))}${item.description.length > 180 ? '...' : ''}</div>` : ''}
          </td>
          <td>
            <div>${escapeHtml(item.organization || 'N/A')}</div>
            <div class="meta-sub">${escapeHtml(item.country || '')}</div>
          </td>
          <td>${escapeHtml(item.sector || 'N/A')}</td>
          <td>${escapeHtml(item.submission_deadline || 'N/A')}</td>
          <td class="score-cell">${escapeHtml(score)}</td>
          <td>${link}</td>
        `;
        tableBody.appendChild(row);
      });

      updateTime.textContent = `Last loaded: ${new Date().toLocaleTimeString()}`;
    } catch (err) {
      tableBody.innerHTML = `<tr><td colspan="7" class="text-center" style="color:#cf222e;">Error loading data: ${escapeHtml(err.message)}</td></tr>`;
      showMessage(`Error: ${err.message}`, 'error');
    }
  }

  async function runMainPipeline() {
    btnRun.disabled = true;
    btnRefresh.disabled = true;
    btnRun.textContent = 'Running main.py...';
    showMessage('Executing main.py pipeline and saving top 5 into SQLite database...', 'info', 0);

    try {
      const res = await fetch('/api/run-pipeline', { method: 'POST' });
      const data = await res.json();

      if (data.status === 'success') {
        showMessage('Pipeline finished. Top 5 results updated.', 'success');
        await loadResults();
      } else {
        showMessage(`Pipeline note: ${data.message || 'Completed'}`, 'error');
        await loadResults();
      }
    } catch (err) {
      showMessage(`Failed to run pipeline: ${err.message}`, 'error');
    } finally {
      btnRun.disabled = false;
      btnRefresh.disabled = false;
      btnRun.textContent = 'Run main.py';
    }
  }

  btnRefresh.addEventListener('click', loadResults);
  btnRun.addEventListener('click', runMainPipeline);

  loadResults();
});
