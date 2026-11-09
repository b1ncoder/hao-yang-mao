/* 薅羊毛情报站前端逻辑：渲染 data/news.js 与 data/x.js，统计、独立时段切换、站内搜索 */
(function () {
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* ---------- 新闻区：data/news.js -> #news-list ---------- */
  function renderNews() {
    var data = window.SITE_NEWS || { updated: '', items: [] };
    var up = document.getElementById('news-updated');
    if (up) up.textContent = '最后刷新：' + data.updated;
    var list = document.getElementById('news-list');
    if (!list) return;
    var html = '';
    (data.items || []).forEach(function (it) {
      html += '<article class="news-item">';
      if (it.zh) {
        html += '<div class="news-bi"><div class="news-en"><a href="' + esc(it.u) + '" target="_blank" rel="noopener">' + esc(it.t) + '</a></div><div class="news-zh">' + esc(it.zh) + '</div></div>';
      } else {
        html += '<div class="news-en"><a href="' + esc(it.u) + '" target="_blank" rel="noopener">' + esc(it.t) + '</a></div>';
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
    var isNews = secId === 'xnews';
    var tagHtml = '<span class="x-tags-note">时段：</span>';
    var snapHtml = '';
    (snaps || []).forEach(function (snap, i) {
      var h = snap.hour;
      var hh = h.slice(11);
      tagHtml += '<button data-hour="' + esc(h) + '"' + (i === 0 ? ' class="on"' : '') + ' title="' + esc(h) + '">' + esc(hh) + '</button>';
      snapHtml += '<div class="x-snap" data-hour="' + esc(h) + '"' + (i === 0 ? '' : ' hidden') + '><div class="tw"><table>';
      if (isNews) {
        snapHtml += '<tr><th>话题</th><th>一句话</th><th>时间</th><th>链接</th></tr>';
        snap.rows.forEach(function (r) {
          snapHtml += '<tr><td>' + esc(r.topic) + '</td><td>' + esc(r.desc) + '</td><td>' + esc(r.time) + '</td><td><a href="' + esc(r.url) + '" target="_blank" rel="noopener">' + esc(r.label) + '</a></td></tr>';
        });
      } else {
        snapHtml += '<tr><th>帖子</th><th>内容</th><th>作者</th><th>状态</th><th>链接</th></tr>';
        if (!snap.rows.length) {
          snapHtml += '<tr class="x-empty"><td colspan="5">本小时暂无新热门羊毛帖。</td></tr>';
        } else {
          snap.rows.forEach(function (r) {
            snapHtml += '<tr><td>' + esc(r.post) + '</td><td>' + esc(r.content) + '</td><td>' + esc(r.author) + '</td><td><span class="tag ' + esc(r.statusClass) + '">' + esc(r.status) + '</span></td><td><a href="' + esc(r.url) + '" target="_blank" rel="noopener">' + esc(r.label) + '</a></td></tr>';
          });
        }
      }
      snapHtml += '</table></div></div>';
    });
    tags.innerHTML = tagHtml;
    wrap.innerHTML = snapHtml;
  }

  /* ---------- 栏目表：data/sec-*.js 渲染进 tbody ---------- */
  function cellHtml(cell, first) {
    if (typeof cell === 'string') return first ? '<strong>' + esc(cell) + '</strong>' : esc(cell);
    var main = cell.u ? '<a href="' + esc(cell.u) + '" target="_blank" rel="noopener">' + esc(cell.t) + '</a>' : esc(cell.t);
    if (cell.bad) main = '<span class="bad">' + main + '</span>';
    var tag = cell.tag ? ' <span class="tag ' + esc(cell.tag.cls) + '">' + esc(cell.tag.text) + '</span>' : '';
    return first ? '<strong>' + main + '</strong>' + tag : main + tag;
  }
  function renderTableSection(secId, data) {
    var body = document.getElementById('body-' + secId);
    if (!body) return;
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
    grid.innerHTML = (data.items || []).map(function (v) {
      return '<div class="video-card"><a href="' + esc(v.u) + '" target="_blank" rel="noopener"><img src="https://i.ytimg.com/vi/' + esc(v.id) + '/hqdefault.jpg" alt="' + esc(v.t) + '" loading="lazy"></a><div><strong><a href="' + esc(v.u) + '" target="_blank" rel="noopener">' + esc(v.t) + '</a></strong>' + esc(v.d) + '</div></div>';
    }).join('');
  }
  function renderArchive(data) {
    var ul = document.getElementById('archive-list');
    if (!ul) return;
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
      b.classList.toggle('on', b.getAttribute('data-hour') === hour);
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
    snaps.forEach(function (s) { if (s === shown) s.removeAttribute('hidden'); else s.setAttribute('hidden', ''); });
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

  /* ---------- 站内搜索 ---------- */
  var q = document.getElementById('q');
  var noresult = document.getElementById('noresult');
  if (!q) return;
  q.addEventListener('input', function () {
    var kw = q.value.trim().toLowerCase();
    var anyVisible = false;
    document.querySelectorAll('main section').forEach(function (sec) {
      var visible = 0;
      sec.querySelectorAll('table tbody tr, ul li, .video-card, .news-item').forEach(function (row) {
        if (row.closest && row.closest('.x-snap') && row.closest('.x-snap').hasAttribute('hidden')) { row.style.display = 'none'; return; }
        var hit = !kw || row.textContent.toLowerCase().indexOf(kw) !== -1;
        row.style.display = hit ? '' : 'none';
        if (hit) visible++;
      });
      sec.style.display = (!kw || visible > 0) ? '' : 'none';
      if (visible > 0) anyVisible = true;
    });
    noresult.style.display = (kw && !anyVisible) ? 'block' : 'none';
  });
})();
