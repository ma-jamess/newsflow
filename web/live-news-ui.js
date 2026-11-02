(function (root, factory) {
  const view = factory();
  if (typeof module === 'object' && module.exports) module.exports = view;
  else root.LiveNewsUI = view;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const COLORS = {体育: 'sport', 科技: 'tech', 教育: 'education', 财经: 'finance', 娱乐: 'culture'};
  const ICONS = {
    star: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="m12 3 2.8 5.7 6.3.9-4.6 4.5 1.1 6.3-5.6-3-5.6 3 1.1-6.3-4.6-4.5 6.3-.9Z"/></svg>',
    arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M7 17 17 7M7 7h10v10"/></svg>',
    refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M20 7v5h-5M4 17v-5h5"/><path d="M6 7a7 7 0 0 1 12-1l2 3M4 15l2 3a7 7 0 0 0 12-1"/></svg>'
  };
  function escape(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[char]));
  }
  function safeLink(value) {
    try {
      if (typeof value !== 'string' || /[\x00-\x20\x7f]/.test(value)) return '';
      const link = new URL(value);
      return ['https:', 'http:'].includes(link.protocol) && !link.username && !link.password ? link.href : '';
    } catch { return ''; }
  }
  function relativeTime(value, now = new Date()) {
    if (!value || !Number.isFinite(new Date(value).getTime())) return '时间未标注';
    const seconds = (new Date(now).getTime() - new Date(value).getTime()) / 1000;
    if (seconds < -60) return '尚未发布';
    if (seconds < 60) return '刚刚';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' 分钟前';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' 小时前';
    if (seconds < 604800) return Math.floor(seconds / 86400) + ' 天前';
    return new Date(value).toLocaleDateString('zh-CN', {timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit'});
  }
  function fullTime(value) {
    if (!value || !Number.isFinite(new Date(value).getTime())) return '时间未标注';
    return new Date(value).toLocaleString('zh-CN', {timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false});
  }
  function updateSchedule(snapshot = {}) {
    const value = Number.isInteger(snapshot.interval_seconds) && snapshot.interval_seconds >= 60 && snapshot.interval_seconds <= 3600 ? snapshot.interval_seconds : 300;
    const interval = value % 60 === 0 ? `${value / 60} 分钟` : `${value} 秒`;
    return snapshot.deployment === 'ecs' ? `每轮采集完成后约 ${interval} 再次检查` : `约每 ${interval} 自动更新，调度可能延迟`;
  }
  function queryString(filters) {
    const params = new URLSearchParams();
    params.set('q', filters.query || '');
    params.set('category', filters.category || '');
    params.set('source', filters.source || '');
    params.set('saved', filters.saved ? '1' : '0');
    params.set('review', filters.review ? '1' : '0');
    params.set('limit', '50');
    params.set('offset', String(Math.max(0, ((filters.page || 1) - 1) * 50)));
    return params.toString();
  }
  function rowMarkup(row, now) {
    const category = row.category || '待核对';
    const color = COLORS[category] || 'unknown';
    const score = row.correction === '待核对' ? '人工标记待核对' : row.human_labeled ? '人工分类' : row.score == null ? '等待核对' : '模型倾向 ' + Math.round(row.score * 100) + '%';
    return [
      '<article class="news-item" data-news-id="' + escape(row.id) + '">',
      '<div class="news-item-top"><span class="news-category ' + color + '">' + escape(category) + '</span>',
      row.needs_review ? '<span class="news-review-tag">待核对</span>' : '',
      '<span class="news-prediction-note">' + escape(score) + '</span></div>',
      '<button class="news-open" type="button" data-news-open="' + escape(row.id) + '"><h2>' + escape(row.title) + '</h2>',
      '<p class="news-item-summary">' + escape(row.summary || '查看分类结果与原始新闻来源。') + '</p></button>',
      '<div class="news-item-bottom"><span class="news-source-dot"></span><span>' + escape(row.source_name) + '</span>',
      '<span class="news-meta-separator">·</span><time title="' + escape(fullTime(row.published_at)) + '">' + escape(relativeTime(row.published_at, now)) + '</time>',
      '<button type="button" class="news-save icon-button' + (row.saved ? ' is-saved' : '') + '" data-news-save="' + escape(row.id) + '" aria-label="' + (row.saved ? '取消收藏：' : '收藏：') + escape(row.title) + '" aria-pressed="' + Boolean(row.saved) + '">' + ICONS.star + '</button>',
      '</div></article>'
    ].join('');
  }
  const sourceLabels = {fresh: '有近期新闻', stale: '近期未更新', empty: '暂无条目', error: '连接失败', disabled: '已停用', pending: '等待更新', unknown: '发布时间未标注'};
  return {escape, safeLink, relativeTime, fullTime, updateSchedule, queryString, rowMarkup, COLORS, ICONS, sourceLabels};
});
