
(function () {
  const KEY = __STORAGE_KEY__;
  const questions = Array.from(document.querySelectorAll('.question'));
  const statusEl = document.getElementById('status');
  const total = questions.length;

  // 填寫內容只存在這台電腦的瀏覽器；讀寫失敗（例如無痕模式）不影響填寫
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { saved = {}; }
  const save = () => {
    const data = {};
    questions.forEach((q) => { data[q.dataset.qid] = q.querySelector('textarea').value; });
    try { localStorage.setItem(KEY, JSON.stringify(data)); } catch (e) { /* 存不了就算了 */ }
  };

  const refresh = () => {
    let n = 0;
    questions.forEach((q) => {
      const has = q.querySelector('textarea').value.trim().length > 0;
      q.classList.toggle('answered', has);
      if (has) n++;
    });
    document.getElementById('progress-text').textContent = '已回答 ' + n + '／' + total + ' 題';
    document.getElementById('meter').style.width = (total ? (n / total) * 100 : 0) + '%';
  };

  questions.forEach((q) => {
    const ta = q.querySelector('textarea');
    ta.value = saved[q.dataset.qid] || '';
    ta.addEventListener('input', () => { save(); refresh(); });
  });
  refresh();

  const buildMarkdown = () => {
    const out = ['# ' + document.title + '（回覆）', ''];
    out.push('回覆日期：' + new Date().toISOString().slice(0, 10));
    out.push('');
    let current = null;
    questions.forEach((q) => {
      const sec = q.closest('section');
      const h2 = sec ? sec.querySelector('h2').textContent.trim() : '';
      if (h2 !== current) { out.push('## ' + h2, ''); current = h2; }
      const num = q.dataset.num ? q.dataset.num + ' ' : '';
      out.push('### ' + num + q.dataset.text, '');
      const a = q.querySelector('textarea').value.trim();
      if (a) a.split('\n').forEach((l) => out.push('> ' + l));
      else out.push('> （未回答）');
      out.push('');
    });
    return out.join('\n');
  };

  const flash = (msg) => { statusEl.textContent = msg; setTimeout(() => { statusEl.textContent = ''; }, 2500); };

  document.getElementById('copy-btn').addEventListener('click', () => {
    const text = buildMarkdown();
    const fallback = () => {
      const t = document.createElement('textarea');
      t.value = text; document.body.appendChild(t); t.select();
      let ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      t.remove();
      flash(ok ? '已複製' : '複製失敗，請改用下載');
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => flash('已複製'), fallback);
    } else { fallback(); }
  });

  document.getElementById('download-btn').addEventListener('click', () => {
    const blob = new Blob([buildMarkdown()], { type: 'text/markdown;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = __DOWNLOAD_NAME__;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    flash('已下載');
  });
})();
