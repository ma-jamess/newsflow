(function (root, factory) {
  const view = factory(typeof module === 'object' && module.exports ? require('./live-news-ui.js') : root.LiveNewsUI);
  if (typeof module === 'object' && module.exports) module.exports = view;
  else root.NewsroomReady.then(() => {
    if (state.bootstrap) view.mount({api, download, navigate, toast, bootstrap: state.bootstrap});
  });
})(typeof globalThis !== 'undefined' ? globalThis : this, function (UI) {
  'use strict';
  const CATEGORIES = Object.keys(UI.COLORS);
  const noop = () => {};

  // The request boundary owns selection so late network responses cannot replace a newer view.
  class NewsController {
    constructor({api, onList = noop, onDetail = noop, onError = noop}) {
      Object.assign(this, {api, onList, onDetail, onError});
      this.filters = {query: '', category: '', source: '', saved: false, review: false, page: 1};
      this.data = null;
      this.detail = null;
      this.selectedId = null;
      this.listRequest = 0;
      this.detailRequest = 0;
      this.writes = new Set();
    }
    async load() {
      const request = ++this.listRequest;
      try {
        const data = await this.api('news?' + UI.queryString(this.filters));
        if (request !== this.listRequest) return;
        const lastPage = Math.max(1, Math.ceil(data.total / 50));
        if (this.filters.page > lastPage) {
          this.filters.page = lastPage;
          return this.load();
        }
        this.data = data;
        this.onList(data, this);
        return data;
      } catch (error) {
        if (request === this.listRequest) this.onError(error);
      }
    }
    setFilters(patch) {
      this.filters = {...this.filters, ...patch, page: patch.page || 1};
      this.closeDetail();
      this.data = null;
      this.onList(null, this);
      return this.load();
    }
    async select(id) {
      const request = ++this.detailRequest;
      this.selectedId = id;
      this.detail = null;
      this.onDetail(null, id);
      try {
        const row = await this.api('news/detail?id=' + encodeURIComponent(id));
        if (request !== this.detailRequest) return;
        this.detail = row;
        this.onDetail(row, id);
        return row;
      } catch (error) {
        if (request === this.detailRequest) {
          this.closeDetail();
          this.onError(error);
        }
      }
    }
    closeDetail() {
      ++this.detailRequest;
      this.selectedId = null;
      this.detail = null;
      this.onDetail(null, null);
    }
    async write(path, payload) {
      if (this.writes.has(payload.id)) return false;
      this.writes.add(payload.id);
      try {
        await this.api(path, payload);
        // Restart selected details after the write, invalidating a pre-write GET
        // even when it is still pending and no detail object has arrived yet.
        const detailRefresh = this.selectedId === payload.id ? this.select(payload.id) : Promise.resolve();
        await Promise.all([this.load(), detailRefresh]);
        return true;
      } catch (error) {
        this.onError(error);
        return false;
      } finally {
        this.writes.delete(payload.id);
      }
    }
    toggleSaved(id) {
      const row = this.detail?.id === id ? this.detail : this.data?.rows.find(item => item.id === id);
      return row ? this.write('news/save', {id, saved: !row.saved}) : Promise.resolve(false);
    }
    correct(id, category) {
      return this.write('news/feedback', {id, category});
    }
  }

  function mount({api, download, navigate, toast, bootstrap}) {
    const el = id => document.getElementById(id);
    const escape = UI.escape;
    let sources = [], searchTimer, pollTimer, refreshPending = false, lastListMarkup = '';
    let sourceRead = 0, sourceWrites = 0;
    const controller = new NewsController({api, onList: renderList, onDetail: renderDetail, onError: showError});
    const categoryMarkup = () => ['', ...CATEGORIES].map(category =>
      `<button type="button" class="news-category-filter ${controller.filters.category === category ? 'active' : ''}" data-news-category="${category}" aria-pressed="${controller.filters.category === category}"><span class="category-filter-dot ${UI.COLORS[category] || 'all'}"></span><span>${category || '所有分类'}</span><small>${category ? controller.data?.stats.categories[category] ?? '—' : controller.data?.stats.total ?? '—'}</small></button>`).join('');

    function showError(error) {
      el('news-error').textContent = error.message;
      if (!controller.data) {
        el('news-list').innerHTML = '<div class="news-empty"><h3>暂时无法读取新闻</h3><p>' + (bootstrap.public_site ? '检查网络后重试；已保存的浏览器缓存仍会保留。' : '检查本地服务是否运行，再点击「检查更新」。') + '</p></div>';
        el('news-list-count').textContent = '连接暂不可用';
      }
    }
    function renderFilters() {
      for (const id of ['news-side-filters', 'news-mobile-filters']) {
        const parent = el(id);
        const focused = parent.contains(document.activeElement) ? document.activeElement?.dataset.newsCategory : undefined;
        parent.innerHTML = categoryMarkup();
        parent.querySelectorAll('[data-news-category]').forEach(button => {
          button.onclick = () => {
            navigate('news');
            controller.setFilters({category: button.dataset.newsCategory});
          };
          if (focused === button.dataset.newsCategory) button.focus({preventScroll: true});
        });
      }
      const mode = controller.filters.saved ? 'saved' : controller.filters.review ? 'review' : 'all';
      document.querySelectorAll('[data-news-mode]').forEach(button => {
        button.classList.toggle('active', button.dataset.newsMode === mode);
        button.setAttribute('aria-pressed', String(button.dataset.newsMode === mode));
      });
    }
    function markSelected() {
      el('news-list').querySelectorAll('[data-news-id]').forEach(row => row.classList.toggle('selected', row.dataset.newsId === controller.selectedId));
    }
    function renderList(data) {
      renderFilters();
      const filters = controller.filters;
      el('news-list-title').textContent = (filters.category || '全部新闻') + (filters.saved ? ' · 收藏' : filters.review ? ' · 待核对' : '');
      if (!data) {
        el('news-error').textContent = '';
        el('news-list').innerHTML = '<div class="news-loading" role="status"><span class="loading-dot"></span>正在整理新闻…</div>';
        el('news-list-count').textContent = '正在加载';
        lastListMarkup = '';
        return;
      }
      el('news-error').textContent = '';
      el('news-count-all').textContent = data.stats.total;
      el('news-count-review').textContent = data.stats.review;
      el('news-count-saved').textContent = data.stats.saved;
      el('news-list-count').textContent = data.total.toLocaleString() + ' 条';
      const markup = data.rows.length ? data.rows.map(row => UI.rowMarkup(row, data.server_time)).join('')
        : `<div class="news-empty"><span aria-hidden="true">◌</span><h3>${filters.saved ? '这里留给值得收藏的新闻' : filters.query || filters.category || filters.source || filters.review ? '暂时没有符合条件的新闻' : data.update.refreshing ? '正在获取第一批新闻' : '还没有最近的新闻'}</h3><p>${filters.saved ? '点击新闻卡片的星标，即可在这里找到。' : data.update.refreshing ? '来源正在更新，稍后会自动显示。' : '可以切换分类、清空搜索，或在新闻源设置中添加订阅。'}</p>${filters.category === '娱乐' ? '<p>默认订阅以科技、体育、教育、财经为主；可开启「中新网 · 即时新闻」补充来源。</p>' : ''}</div>`;
      if (markup !== lastListMarkup) {
        const active = document.activeElement;
        const focusedId = el('news-list').contains(active) ? active?.dataset.newsOpen || active?.dataset.newsSave : null;
        const focusType = active?.dataset.newsSave ? 'newsSave' : 'newsOpen';
        el('news-list').innerHTML = markup;
        lastListMarkup = markup;
        el('news-list').querySelectorAll('[data-news-open]').forEach(button => button.onclick = () => controller.select(button.dataset.newsOpen));
        el('news-list').querySelectorAll('[data-news-save]').forEach(button => button.onclick = async () => {
          button.disabled = true;
          const wasSaved = controller.data?.rows.find(row => row.id === button.dataset.newsSave)?.saved;
          if (await controller.toggleSaved(button.dataset.newsSave)) toast(wasSaved ? '已取消收藏' : '已收藏到本机');
          button.disabled = false;
        });
        if (focusedId) [...el('news-list').querySelectorAll('button')].find(button => button.dataset[focusType] === focusedId)?.focus({preventScroll: true});
      }
      markSelected();
      const pages = Math.max(1, Math.ceil(data.total / 50));
      el('news-pager').textContent = `${filters.page} / ${pages} 页`;
      el('news-prev').disabled = filters.page === 1;
      el('news-next').disabled = filters.page >= pages;
      el('news-export').disabled = !data.total;
      renderStatus(data);
    }
    function renderStatus(data) {
      const update = data.update, enabled = sources.filter(source => source.enabled).length;
      let status = update.refreshing ? '正在检查来源…' : update.status === 'error' ? '来源连接失败 · 已保留缓存'
        : update.status === 'partial' ? `${update.errors} 个来源暂不可用 · 其余已更新`
        : update.last_finished_at ? `最近检查 ${UI.fullTime(update.last_finished_at)} · 每 2 分钟自动检查` : '等待首次检查';
      if (bootstrap.public_site) {
        const delayed = update.last_success_at && new Date(data.server_time) - new Date(update.last_success_at) > 15 * 60000;
        status = data.reader_error ? '网络暂不可用 · 显示浏览器缓存' : update.status === 'error' ? '来源连接失败 · 显示已发布缓存' : update.status === 'partial' ? `${update.errors} 个来源暂不可用 · 其余已更新` : delayed ? '更新延迟 · 显示已发布新闻' : '最近采集 ' + UI.fullTime(update.last_finished_at);
        status += ' · 约每 5 分钟自动更新，调度可能延迟';
      }
      el('news-status').innerHTML = `<span class="live-dot ${update.status === 'error' || update.status === 'partial' ? 'warning' : ''}"></span>${escape(status)}`;
      const latest = sources.filter(source => source.enabled && source.latest_published_at).map(source => source.latest_published_at).sort().at(-1);
      el('news-latest').textContent = enabled + ' 个来源' + (latest ? ' · 最新发布 ' + UI.fullTime(latest) : '');
      const since = update.last_started_at ? (new Date(data.server_time) - new Date(update.last_started_at)) / 1000 : 31;
      const cooldown = bootstrap.public_site ? 0 : Math.max(0, Math.ceil(30 - since));
      el('news-refresh').disabled = refreshPending || update.refreshing || cooldown > 0;
      el('news-refresh').classList.toggle('refreshing', update.refreshing);
      el('news-refresh-label').textContent = update.refreshing ? '正在更新' : cooldown ? `${cooldown} 秒后可检查` : '检查更新';
    }
    function renderDetail(row, selectedId) {
      markSelected();
      if (!selectedId) {
        delete document.body.dataset.newsDetail;
        el('news-detail').innerHTML = '<div class="news-detail-empty"><span class="detail-decoration" aria-hidden="true">N↗</span><h2>挑一条新闻，<br>看看来龙去脉。</h2><p>查看订阅摘要、原始来源，<br>以及本地模型的分类依据。</p><div class="detail-empty-note"><span class="live-dot"></span>新闻持续更新，收藏留在本机</div></div>';
        return;
      }
      document.body.dataset.newsDetail = 'open';
      const close = '<button id="news-detail-close" class="icon-button" aria-label="关闭新闻详情">×</button>';
      if (!row) {
        el('news-detail').innerHTML = `<div class="news-detail-top"><span>新闻详情</span>${close}</div><div class="news-loading" role="status">正在读取分类依据…</div>`;
        el('news-detail-close').onclick = closeDetail;
        return;
      }
      const result = row.explanation || row.result, link = UI.safeLink(row.url), category = row.category || '待核对';
      const bars = CATEGORIES.map(label => `<div class="bar-row ${label === result.prediction ? 'winner' : ''}"><span>${label}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(0, Math.min(100, (result.probabilities?.[label] || 0) * 100))}%"></div></div><span>${Math.round((result.probabilities?.[label] || 0) * 100)}%</span></div>`).join('');
      const evidence = (result.evidence || []).slice(0, 8).map(item => `<span title="${escape('相对' + item.against + '的得分贡献 ' + item.contribution)}">${escape(item.feature)}</span>`).join('');
      el('news-detail').innerHTML = `<div class="news-detail-top"><span>新闻详情</span>${close}</div><div class="news-detail-body"><div class="detail-tags"><span class="news-category ${UI.COLORS[category] || 'unknown'}">${escape(category)}</span>${row.human_labeled ? '<span class="news-human-tag">' + (row.correction === '待核对' ? '人工标记待核对' : '人工标注') + '</span>' : row.needs_review ? '<span class="news-review-tag">待核对</span>' : ''}</div><h2 class="detail-title">${escape(row.title)}</h2><p class="detail-source">${escape(row.source_name)} · ${escape(UI.fullTime(row.published_at))}</p><p class="detail-summary">${escape(row.summary || '这个来源没有提供摘要，可以打开原文查看内容。')}</p><p class="detail-summary-note">订阅摘要 · 内容与发布时间来自新闻源</p><div class="detail-actions">${link ? `<a href="${escape(link)}" target="_blank" rel="noopener noreferrer" class="primary">阅读原文 ${UI.ICONS.arrow}</a>` : ''}<button id="news-detail-save" class="secondary ${row.saved ? 'is-saved' : ''}" aria-pressed="${row.saved}">${UI.ICONS.star}${row.saved ? '已收藏' : '收藏'}</button></div><div class="detail-classification"><div class="detail-section-heading"><h3>为什么归到这一类</h3><span>本地模型</span></div><p class="detail-model-note">${escape(bootstrap.model_names[result.model] || result.model || '本地分类')} · 模型预测 ${escape(result.prediction || '未识别')}${result.score == null ? '' : ' / ' + Math.round(result.score * 100) + '%'}${row.human_labeled ? (row.correction === '待核对' ? '<br>已人工标记待核对，下方保留原始模型依据。' : '<br>当前分类以人工标注为准，下方保留原始模型依据。') : ''}</p><div class="distribution">${bars}</div><div class="evidence">${evidence || '<span>没有明显的文字线索</span>'}</div><p class="detail-explanation-note">特征反映模型的判断线索，概率不能保证分类正确。</p></div><form id="news-correct-form" class="detail-correction"><label for="news-correct-category">人工核对类别</label><div><select id="news-correct-category">${[...CATEGORIES, '待核对'].map(label => `<option ${label === (row.correction || category) ? 'selected' : ''}>${label}</option>`).join('')}</select><button id="news-correct-submit" class="secondary" type="submit">保存</button></div><p>标注保留在本机，刷新后仍有效。</p></form><button id="news-to-classify" class="text-button">带到快速分类 →</button><p class="detail-fetch-time">收录于 ${escape(UI.fullTime(row.first_seen_at))}</p></div>`;
      el('news-detail-close').onclick = closeDetail;
      el('news-detail-save').onclick = async event => {
        event.currentTarget.disabled = true;
        if (await controller.toggleSaved(row.id)) toast(row.saved ? '已取消收藏' : '已收藏到本机');
        if (el('news-detail-save')) el('news-detail-save').disabled = false;
      };
      el('news-correct-form').onsubmit = async event => {
        event.preventDefault();
        const button = el('news-correct-submit');
        button.disabled = true;
        if (await controller.correct(row.id, el('news-correct-category').value)) toast('人工分类已保存');
        button.disabled = false;
      };
      el('news-to-classify').onclick = () => {
        if (bootstrap.public_site) {window.open(bootstrap.download_url, '_blank', 'noopener,noreferrer'); return;}
        el('title-input').value = row.title.slice(0, 200);
        el('title-input').dispatchEvent(new Event('input'));
        navigate('classify');
        el('title-input').focus();
      };
      if (bootstrap.public_site) el('news-to-classify').textContent = '下载完整分类项目 →';
    }
    function closeDetail() {
      const id = controller.selectedId;
      controller.closeDetail();
      [...el('news-list').querySelectorAll('[data-news-open]')].find(button => button.dataset.newsOpen === id)?.focus({preventScroll: true});
    }
    function renderSources() {
      const previous = el('news-source-filter').value;
      el('news-source-filter').innerHTML = '<option value="">所有来源</option>' + sources.map(source => `<option value="${escape(source.id)}">${escape(source.name)}${source.enabled ? '' : ' · 已停用'}</option>`).join('');
      el('news-source-filter').value = previous;
      const focused = el('news-source-list').contains(document.activeElement) ? document.activeElement?.dataset.sourceToggle : null;
      el('news-source-list').innerHTML = sources.map(source => `<article class="news-source-row"><div class="source-row-main"><div><h3>${escape(source.name)} <span class="source-health ${source.status}">${escape(UI.sourceLabels[source.status] || source.status)}</span></h3><p>${escape(source.description || source.url)}</p></div><label class="source-switch"><input type="checkbox" data-source-toggle="${escape(source.id)}" ${source.enabled ? 'checked' : ''} aria-label="启用${escape(source.name)}"><span aria-hidden="true"></span></label></div><div class="source-row-meta"><span>最新发布 ${escape(UI.fullTime(source.latest_published_at))}</span><span>最近读取 ${escape(UI.fullTime(source.last_success_at))}</span></div>${source.last_error && source.enabled ? `<p class="source-row-error">${escape(source.last_error)}</p>` : ''}</article>`).join('');
      el('news-source-list').querySelectorAll('[data-source-toggle]').forEach(input => {
        if (input.dataset.sourceToggle === focused) input.focus({preventScroll: true});
        input.onchange = async () => {
          input.disabled = true;
          ++sourceRead;
          ++sourceWrites;
          try {
            await api('news/sources', {id: input.dataset.sourceToggle, enabled: input.checked});
            await controller.load();
          } catch (error) {el('news-source-error').textContent = error.message; input.checked = !input.checked;}
          finally {
            input.disabled = false;
            --sourceWrites;
            if (!sourceWrites) await loadSources();
          }
        };
      });
      if (controller.data) renderStatus(controller.data);
    }
    async function loadSources() {
      if (sourceWrites) return;
      const request = ++sourceRead;
      try {
        const data = await api('news/sources');
        if (request !== sourceRead || sourceWrites) return;
        sources = data.sources;
        renderSources();
      } catch (error) {if (request === sourceRead && !sourceWrites) el('news-source-error').textContent = error.message;}
    }
    async function refresh() {
      refreshPending = true;
      el('news-refresh').disabled = true;
      el('news-refresh-label').textContent = '正在检查';
      try {
        const response = await api('news/refresh', {});
        if (response.public_site) toast(response.cached ? '连接暂不可用，继续显示浏览器缓存' : '已检查最新发布数据；自动采集任务约每 5 分钟运行');
        if (!response.started && response.cooldown_seconds) toast(`请在 ${response.cooldown_seconds} 秒后再次检查`);
        await controller.load();
        schedulePoll(1600);
      } catch (error) {showError(error);}
      finally {
        refreshPending = false;
        if (controller.data) renderStatus(controller.data);
        else {el('news-refresh').disabled = false; el('news-refresh-label').textContent = '检查更新';}
      }
    }
    function schedulePoll(delay = 20000) {
      clearTimeout(pollTimer);
      pollTimer = setTimeout(async () => {
        if (!document.hidden) {
          await controller.load();
          await loadSources();
        }
        schedulePoll(controller.data?.update.refreshing ? 1800 : 20000);
      }, delay);
    }

    document.querySelectorAll('[data-news-mode]').forEach(button => button.onclick = () => controller.setFilters({saved: button.dataset.newsMode === 'saved', review: button.dataset.newsMode === 'review'}));
    el('news-search').oninput = () => {
      clearTimeout(searchTimer);
      // Invalidate details immediately while the user is changing the search.
      ++controller.listRequest;
      controller.closeDetail();
      searchTimer = setTimeout(() => controller.setFilters({query: el('news-search').value}), 250);
    };
    el('news-source-filter').onchange = () => controller.setFilters({source: el('news-source-filter').value});
    el('news-refresh').onclick = refresh;
    el('news-prev').onclick = () => controller.setFilters({page: controller.filters.page - 1});
    el('news-next').onclick = () => {controller.setFilters({page: controller.filters.page + 1}); el('news-list-title').scrollIntoView({block: 'start', behavior: 'smooth'});};
    el('news-export').onclick = async () => {
      try {
        const filters = controller.filters;
        await download('news/export', {q: filters.query, category: filters.category, source: filters.source, saved: filters.saved, review: filters.review}, 'NewsFlow_新闻列表.csv');
        toast('当前筛选的新闻已导出');
      } catch (error) {showError(error);}
    };
    el('news-sources-open').onclick = () => {el('news-sources-dialog').showModal(); loadSources();};
    el('news-sources-close').onclick = () => el('news-sources-dialog').close();
    el('news-sources-dialog').addEventListener('click', event => {if (event.target === el('news-sources-dialog')) el('news-sources-dialog').close();});
    el('news-source-form').onsubmit = async event => {
      event.preventDefault();
      el('news-source-add').disabled = true;
      el('news-source-error').textContent = '';
      ++sourceRead;
      ++sourceWrites;
      try {
        await api('news/sources', {name: el('news-source-name').value.trim(), url: el('news-source-url').value.trim()});
        el('news-source-form').reset();
        toast('订阅已添加，下一次检查时获取新闻');
        await controller.load();
        schedulePoll(1800);
      } catch (error) {el('news-source-error').textContent = error.message;}
      finally {
        --sourceWrites;
        if (!sourceWrites) await loadSources();
        el('news-source-add').disabled = false;
      }
    };
    el('news-detail-backdrop').onclick = closeDetail;
    document.addEventListener('keydown', event => {if (event.key === 'Escape' && document.body.dataset.newsDetail) closeDetail();});
    document.addEventListener('visibilitychange', () => {if (!document.hidden) schedulePoll(200);});
    renderFilters();
    controller.load().then(() => schedulePoll(controller.data?.update.refreshing ? 1800 : 20000));
    loadSources();
    return controller;
  }
  return {NewsController, mount};
});
