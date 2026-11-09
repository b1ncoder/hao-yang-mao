/* 薅羊毛情报站前端逻辑：渲染 data/news.js 与 data/x.js，统计、独立时段切换、站内搜索 */
(function () {
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  /* 只放行 http(s) 链接，javascript: 等协议一律拦掉 */
  function safeUrl(u) {
    var v = String(u == null ? '' : u).trim();
    return (/^https?:\/\//i.test(v)) ? v : '#';
  }

  /* ---------- 日间/夜间模式：html[data-theme] 驱动两套 CSS 变量 ----------
     head 内联脚本已在 CSS 加载前按 localStorage/系统设好 data-theme；
     这里只做按钮同步、点击切换（存 localStorage，优先于系统设置），
     未手动选过时跟随系统切换。 */
  var THEME_KEY = 'theme';
  function applyTheme(t, save) {
    if (t !== 'light' && t !== 'dark') t = 'light';
    document.documentElement.setAttribute('data-theme', t);
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', t === 'dark' ? '#0f172a' : '#111827');
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      var dark = t === 'dark';
      btn.setAttribute('aria-pressed', dark ? 'true' : 'false');
      btn.setAttribute('aria-label', dark ? '切换到日间模式' : '切换到夜间模式');
    }
    if (save) { try { localStorage.setItem(THEME_KEY, t); } catch (e) {} }
  }
  function initTheme() {
    var cur = document.documentElement.getAttribute('data-theme');
    if (cur !== 'light' && cur !== 'dark') {
      var sysDark = false;
      try { sysDark = !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches); } catch (e) {}
      cur = sysDark ? 'dark' : 'light';
    }
    applyTheme(cur, false);
    var btn = document.getElementById('theme-toggle');
    if (btn) btn.addEventListener('click', function () {
      applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark', true);
    });
    try {
      var mq = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)');
      if (mq && mq.addEventListener) mq.addEventListener('change', function (e) {
        var saved = null;
        try { saved = localStorage.getItem(THEME_KEY); } catch (err) {}
        if (saved !== 'light' && saved !== 'dark') applyTheme(e.matches ? 'dark' : 'light', false);
      });
    } catch (e) {}
  }
  initTheme();

  /* ---------- 新闻区：data/news.js -> #news-list ---------- */
  /* 静态预渲染后页面里已有内容时跳过重渲染；bundle 数据比静态内容新时强制重渲染（自愈） */
  var BUILD_STALE = (function () {
    try {
      var stamp = window.SITE_BUILD && window.SITE_BUILD.stamp;
      var cur = document.body && document.body.getAttribute('data-build');
      return !!(stamp && cur && stamp !== cur);
    } catch (e) { return false; }
  })();
  function renderNews() {
    var data = window.SITE_NEWS || { updated: '', items: [] };
    var up = document.getElementById('news-updated');
    if (up) up.textContent = '最后刷新：' + data.updated;
    var d = String(data.updated || '').slice(0, 10);
    if (d) { var lu = document.getElementById('last-updated'); if (lu) lu.textContent = d; document.querySelectorAll('.last-updated').forEach(function (el) { el.textContent = d; }); }
    var list = document.getElementById('news-list');
    if (!list) return;
    if (!BUILD_STALE && list.childElementCount > 0) return; /* 静态内容已在，直接用 */
    var html = '';
    (data.items || []).forEach(function (it) {
      html += '<article class="news-item">';
      if (it.zh) {
        html += '<div class="news-bi"><div class="news-en"><a href="' + esc(safeUrl(it.u)) + '" target="_blank" rel="noopener">' + esc(it.t) + '</a></div><div class="news-zh">' + esc(it.zh) + '</div></div>';
      } else {
        html += '<div class="news-en"><a href="' + esc(safeUrl(it.u)) + '" target="_blank" rel="noopener">' + esc(it.t) + '</a></div>';
      }
      html += '<div class="news-meta">' + esc(it.s) + ' · ' + esc(it.d) + '</div></article>';
    });
    list.innerHTML = html;
  }

  /* ---------- X 区：data/x.js 渲染到 tags/snaps 容器 ---------- */
  function renderXSection(secId, snaps) {
    var tags = document.getElementById('tags-' + secId);
    var wrap = document.getElementById('snaps-' + secId);
    if (!tags || !wrap) return;
    if (!BUILD_STALE && tags.querySelector('button')) return; /* 静态内容已在，直接用 */
    var isNews = secId === 'xnews';
    var tagHtml = '<span class="x-tags-note">时段：</span>';
    var snapHtml = '';
    (snaps || []).forEach(function (snap, i) {
      var h = snap.hour;
      var hh = h.slice(11);
      tagHtml += '<button data-hour="' + esc(h) + '"' + (i === 0 ? ' class="on" aria-pressed="true"' : ' aria-pressed="false"') + ' title="' + esc(h) + '">' + esc(hh) + '</button>';
      snapHtml += '<div class="x-snap" data-hour="' + esc(h) + '"' + (i === 0 ? '' : ' hidden') + '><div class="tw"><table>';
      if (isNews) {
        snapHtml += '<caption class="visually-hidden">X 新闻热门 ' + esc(h) + '</caption><thead><tr><th scope="col">话题</th><th scope="col">一句话</th><th scope="col">时间</th><th scope="col">链接</th></tr></thead><tbody>';
        snap.rows.forEach(function (r) {
          snapHtml += '<tr><td>' + esc(r.topic) + '</td><td>' + esc(r.desc) + '</td><td>' + esc(r.time) + '</td><td><a href="' + esc(safeUrl(r.url)) + '" target="_blank" rel="noopener">' + esc(r.label) + '</a></td></tr>';
        });
      } else {
        snapHtml += '<caption class="visually-hidden">X 羊毛热门 ' + esc(h) + '</caption><thead><tr><th scope="col">帖子</th><th scope="col">内容</th><th scope="col">作者</th><th scope="col">状态</th><th scope="col">链接</th></tr></thead><tbody>';
        if (!snap.rows.length) {
          snapHtml += '<tr class="x-empty"><td colspan="5">本小时暂无新热门羊毛帖。</td></tr>';
        } else {
          snap.rows.forEach(function (r) {
            var note = r.note ? '<br><span class="bad">' + esc(r.note) + '</span>' : '';
            var rel = (r.statusClass === 'ok') ? 'noopener' : 'noopener nofollow';
            snapHtml += '<tr><td>' + esc(r.post) + '</td><td>' + esc(r.content) + note + '</td><td>' + esc(r.author) + '</td><td><span class="tag ' + esc(r.statusClass) + '">' + esc(r.status) + '</span></td><td><a href="' + esc(safeUrl(r.url)) + '" target="_blank" rel="' + rel + '">' + esc(r.label) + '</a></td></tr>';
          });
        }
      }
      snapHtml += '</tbody></table></div></div>';
    });
    tags.innerHTML = tagHtml;
    wrap.innerHTML = snapHtml;
  }

  /* ---------- 栏目表：data/sec-*.js 渲染进 tbody ---------- */
  function cellHtml(cell, first) {
    if (typeof cell === 'string') return first ? '<strong>' + esc(cell) + '</strong>' : esc(cell);
    var main = cell.u ? '<a href="' + esc(safeUrl(cell.u)) + '" target="_blank" rel="noopener">' + esc(cell.t) + '</a>' : esc(cell.t);
    if (cell.bad) main = '<span class="bad">' + main + '</span>';
    var tag = cell.tag ? ' <span class="tag ' + esc(cell.tag.cls) + '">' + esc(cell.tag.text) + '</span>' : '';
    return first ? '<strong>' + main + '</strong>' + tag : main + tag;
  }
  function renderTableSection(secId, data) {
    var body = document.getElementById('body-' + secId);
    if (!body) return;
    if (!BUILD_STALE && body.rows.length > 0) return; /* 静态内容已在，直接用 */
    var html = '';
    (data.rows || []).forEach(function (row) {
      html += '<tr>';
      row.forEach(function (cell, ci) {
        html += '<td>' + cellHtml(cell, ci === 0) + '</td>';
      });
      html += '</tr>';
    });
    body.innerHTML = html;
  }
  function renderVideos(data) {
    var grid = document.getElementById('videos-grid');
    if (!grid) return;
    if (!BUILD_STALE && grid.childElementCount > 0) return; /* 静态内容已在，直接用 */
    grid.innerHTML = (data.items || []).map(function (v) {
      return '<div class="video-card"><a href="' + esc(safeUrl(v.u)) + '" target="_blank" rel="noopener"><img src="https://i.ytimg.com/vi/' + esc(v.id) + '/maxresdefault.jpg" srcset="https://i.ytimg.com/vi/' + esc(v.id) + '/mqdefault.jpg 320w, https://i.ytimg.com/vi/' + esc(v.id) + '/maxresdefault.jpg 1280w" sizes="(max-width: 600px) 100vw, 50vw" width="1280" height="720" onerror="this.onerror=null;this.src=&#39;https://i.ytimg.com/vi/' + esc(v.id) + '/hqdefault.jpg&#39;"  alt="' + esc(v.t) + '" loading="lazy"></a><div><strong><a href="' + esc(safeUrl(v.u)) + '" target="_blank" rel="noopener">' + esc(v.t) + '</a></strong>' + esc(v.d) + '</div></div>';
    }).join('');
  }
  function renderArchive(data) {
    var ul = document.getElementById('archive-list');
    if (!ul) return;
    if (!BUILD_STALE && ul.childElementCount > 0) return; /* 静态内容已在，直接用 */
    ul.innerHTML = (data.items || []).map(function (it) {
      return '<li><strong>' + esc(it.t) + '</strong>' + (it.tag ? '<span class="tag ' + esc(it.tag.cls) + '">' + esc(it.tag.text) + '</span>' : '') + '<br>' + esc(it.d) + '</li>';
    }).join('');
  }

  /* ---------- 统计：栏目行数（渲染后才能数） + X 可见快照行数 ---------- */
  var map = { pro: 'pro', domain: 'domain', ai: 'ai', cloud: 'cloud', esim: 'esim', student: 'student', server: 'server' };
  var total = 0;
  function countSectionStats() {
    total = 0;
    Object.keys(map).forEach(function (id) {
      var sec = document.getElementById(id);
      if (!sec) return;
      var rows = sec.querySelectorAll('table tr').length - 1;
      if (rows < 0) rows = 0;
      var el = document.getElementById('stat-' + map[id]);
      if (el) el.textContent = rows;
      total += rows;
    });
  }
  function countXStats() {
    var statOnly = { xnews: 'xnews', xwool: 'xwool' };
    Object.keys(statOnly).forEach(function (id) {
      var sec = document.getElementById(id);
      if (!sec) return;
      var snap = sec.querySelector('.x-snap:not([hidden])');
      var rows = 0;
      if (snap) rows = snap.querySelectorAll('table tr:not(.x-empty)').length - 1;
      if (rows < 0) rows = 0;
      var el = document.getElementById('stat-' + statOnly[id]);
      if (el) el.textContent = rows;
    });
  }

  /* ---------- 时段切换：只切本区 ---------- */
  function showXHour(hour, secId) {
    var sec = document.getElementById(secId);
    if (!sec) return;
    var bar = sec.querySelector('.x-tags');
    if (bar) bar.querySelectorAll('button').forEach(function (b) {
      var on = b.getAttribute('data-hour') === hour;
      b.classList.toggle('on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    var snaps = sec.querySelectorAll('.x-snap');
    var shown = null;
    snaps.forEach(function (s) { if (s.getAttribute('data-hour') === hour) shown = s; });
    if (!shown) {
      snaps.forEach(function (s) {
        var h = s.getAttribute('data-hour');
        if (h <= hour && (!shown || h > shown.getAttribute('data-hour'))) shown = s;
      });
    }
    if (!shown && snaps.length) shown = snaps[0];
    snaps.forEach(function (s) {
      if (s === shown) { s.removeAttribute('hidden'); s.querySelectorAll('tr, li').forEach(function (r) { r.style.display = ''; }); }
      else s.setAttribute('hidden', '');
    });
    countXStats();
  }

  /* ---------- 先渲染，再接线 ---------- */
  renderNews();
  var x = window.SITE_X || { news: [], wool: [] };
  renderXSection('xnews', x.news);
  renderXSection('xwool', x.wool);
  ['pro', 'domain', 'ai', 'cloud', 'esim', 'student', 'server'].forEach(function (id) {
    renderTableSection(id, window['SEC_' + id.toUpperCase()] || { rows: [] });
  });
  renderVideos(window.SEC_VIDEOS || { items: [] });
  renderArchive(window.SEC_ARCHIVE || { items: [] });
  countSectionStats();
  countXStats();
  document.querySelectorAll('.x-tags').forEach(function (bar) {
    bar.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (!b) return;
      var sec = bar.closest('#xnews, #xwool');
      if (sec) showXHour(b.getAttribute('data-hour'), sec.id);
    });
  });
  var t = document.getElementById('stat-total');
  if (t) t.textContent = total;

  /* ---------- 站内搜索：全量搜（含隐藏快照）、150ms 节流、关键词进 #q= ---------- */
  var q = document.getElementById('q');
  var noresult = document.getElementById('noresult');
  if (!q) return;
  var searchTimer = null;
  function applySearch(kw) {
    var anyVisible = false;
    document.querySelectorAll('main section').forEach(function (sec) {
      var visible = 0;
      var isX = sec.id === 'xnews' || sec.id === 'xwool';
      /* 搜索时先把本区所有快照放出来再筛，命中哪个时段就留哪个；不搜索时恢复只显示首个快照 */
      if (isX) {
        if (kw) sec.querySelectorAll('.x-snap').forEach(function (sn) { sn.removeAttribute('hidden'); });
        else {
          var onBtn = sec.querySelector('.x-tags button.on');
          var onHour = onBtn ? onBtn.getAttribute('data-hour') : null;
          sec.querySelectorAll('.x-snap').forEach(function (sn) { if (sn.getAttribute('data-hour') === onHour) sn.removeAttribute('hidden'); else sn.setAttribute('hidden', ''); });
        }
      }
      sec.querySelectorAll('table tbody tr, ul li, .video-card, .news-item').forEach(function (row) {
        var hit = !kw || row.textContent.toLowerCase().indexOf(kw) !== -1;
        row.style.display = hit ? '' : 'none';
        if (hit) visible++;
      });
      if (isX && kw) {
        sec.querySelectorAll('.x-snap').forEach(function (sn) {
          var snapVisible = sn.querySelectorAll('tr:not(.x-empty)').length > 0 && Array.prototype.some.call(sn.querySelectorAll('tbody tr'), function (r) { return r.style.display !== 'none'; });
          sn.style.display = snapVisible ? '' : 'none';
          if (snapVisible) visible++;
        });
      } else if (isX) {
        sec.querySelectorAll('.x-snap').forEach(function (sn) { sn.style.display = ''; });
      }
      sec.style.display = (!kw || visible > 0) ? '' : 'none';
      if (visible > 0) anyVisible = true;
    });
    noresult.style.display = (kw && !anyVisible) ? 'block' : 'none';
    if (!kw) countXStats();
  }
  q.addEventListener('input', function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function () {
      var kw = q.value.trim().toLowerCase();
      try { history.replaceState(null, '', kw ? '#q=' + encodeURIComponent(q.value.trim()) : location.pathname + location.search); } catch (e) {}
      applySearch(kw);
    }, 150);
  });
  /* 从 #q= 还原搜索 */
  var m = (location.hash || '').match(/#q=([^&]+)/);
  if (m) { try { q.value = decodeURIComponent(m[1]); applySearch(q.value.trim().toLowerCase()); } catch (e) {} }
})();
