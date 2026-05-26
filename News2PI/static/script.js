const API = '';
let tags = [];

// Tags input
const tagsInput = document.getElementById('f-tags-input');
if (tagsInput) {
  tagsInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(tagsInput.value.trim().replace(/,$/, ''));
      tagsInput.value = '';
    }
  });

  tagsInput.addEventListener('blur', () => {
    addTag(tagsInput.value.trim().replace(/,$/, ''));
    tagsInput.value = '';
  });

  tagsInput.addEventListener('paste', e => {
    const clipboard = (e.clipboardData || window.clipboardData).getData('text');
    if (clipboard.includes(',')) {
      e.preventDefault();
      clipboard.split(',').forEach(tag => addTag(tag.trim()));
      tagsInput.value = '';
    }
  });
}

function addTag(val) {
  val = val.trim();
  if (!val || tags.includes(val) || tags.length >= 8) return;
  tags.push(val);
  renderTags();
}

function removeTag(t) {
  tags = tags.filter(x => x !== t);
  renderTags();
}

function renderTags() {
  const display = document.getElementById('tags-display');
  if (!display) return;
  display.innerHTML = tags.map(t =>
    `<span class="tag-pill">${t}<button onclick="removeTag('${t}')">✕</button></span>`
  ).join('');
}

async function submitNews() {
  const title = document.getElementById('f-title').value.trim();
  const content = document.getElementById('f-content').value.trim();

  if (!title) { showError('O título é obrigatório.'); return; }
  if (!content) { showError('O conteúdo é obrigatório.'); return; }

  const btn = document.getElementById('btn-submit');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5" stroke-dasharray="8 8"><animateTransform attributeName="transform" type="rotate" from="0 7 7" to="360 7 7" dur="0.8s" repeatCount="indefinite"/></circle></svg> A publicar…';
  }

  const priority = document.querySelector('input[name=priority]:checked')?.value || 'normal';

  const payload = {
    title,
    content,
    category: document.getElementById('f-category').value,
    source: document.getElementById('f-source').value.trim() || 'Anónimo',
    author: document.getElementById('f-author').value.trim(),
    image_url: document.getElementById('f-image').value.trim(),
    priority,
    tags
  };

  try {
    const r = await fetch(API + '/api/news', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const text = await r.text();
    const d = text ? JSON.parse(text) : {};
    if (!r.ok) {
      const message = d.detail || d.error || text || r.statusText;
      throw new Error(message || 'Erro desconhecido no servidor.');
    }
    if (d.success) {
      document.getElementById('alert-error').classList.remove('show');
      document.getElementById('alert-success').classList.add('show');
      document.getElementById('alert-success').scrollIntoView({ behavior: 'smooth', block: 'center' });
      setTimeout(() => document.getElementById('alert-success').classList.remove('show'), 4500);
      document.getElementById('f-title').value = '';
      document.getElementById('f-content').value = '';
      document.getElementById('f-source').value = '';
      document.getElementById('f-author').value = '';
      document.getElementById('f-image').value = '';
      tags = [];
      renderTags();
      document.getElementById('p-normal').checked = true;
    } else {
      showError(d.error || 'Erro desconhecido.');
    }
  } catch (e) {
    showError(e.message || 'Não foi possível ligar ao servidor. Verifique se o servidor está a correr em localhost:3000.');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg> Publicar Notícia';
    }
  }
}

function showError(msg) {
  const el = document.getElementById('alert-error');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function copyCode(btn) {
  const block = btn.parentElement;
  const text = block.innerText.replace('Copiar\n', '').replace('Copiado!\n', '');
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copiado!';
    setTimeout(() => btn.textContent = 'Copiar', 2000);
  });
}
