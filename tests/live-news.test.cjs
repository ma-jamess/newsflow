'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

function ui() {
  return require(path.join(__dirname, '..', 'web', 'live-news-ui.js'));
}

test('publication time stays distinct from refresh time and handles missing dates', () => {
  const view = ui();
  const now = '2026-10-31T08:00:00Z';
  assert.equal(view.relativeTime('2026-10-31T07:57:00Z', now), '3 分钟前');
  assert.equal(view.relativeTime(null, now), '时间未标注');
  assert.equal(view.relativeTime('not-a-date', now), '时间未标注');
  assert.equal(view.relativeTime('2026-10-31T09:00:00Z', now), '尚未发布');
  assert.match(view.fullTime('2026-10-31T08:00:00Z'), /16:00/);
});

test('news markup escapes feed titles, summaries and source names', () => {
  const view = ui();
  const markup = view.rowMarkup({id: 'a'.repeat(32), title: '<img src=x onerror=evil()>',
    summary: '<script>bad()</script>', source_name: '<b>Source</b>',
    category: '科技', score: .9, saved: false, needs_review: false,
    published_at: null, human_labeled: false});
  assert.ok(markup.includes('&lt;img'));
  assert.ok(!markup.includes('<script>'));
  assert.ok(!markup.includes('<b>Source</b>'));
});

test('unsafe article URLs cannot become navigation links', () => {
  const view = ui();
  assert.equal(view.safeLink('javascript:alert(1)'), '');
  assert.equal(view.safeLink('data:text/html,<script>bad()</script>'), '');
  assert.equal(view.safeLink('https://user:secret@example.org/news'), '');
  assert.equal(view.safeLink('https://example.org/news'), 'https://example.org/news');
});

test('category search source and bookmark choices are all encoded in the request', () => {
  const view = ui();
  const params = new URLSearchParams(view.queryString({query: 'AI 芯片', category: '科技',
    source: 'ithome', saved: true, review: true, page: 2}));
  assert.equal(params.get('q'), 'AI 芯片');
  assert.equal(params.get('category'), '科技');
  assert.equal(params.get('source'), 'ithome');
  assert.equal(params.get('saved'), '1');
  assert.equal(params.get('review'), '1');
  assert.equal(params.get('offset'), '50');
});

test('human categories do not present the old model score as human confidence', () => {
  const view = ui();
  const markup = view.rowMarkup({id: 'a'.repeat(32), title: '高校招生', source_name: '来源',
    category: '财经', score: .99, saved: true, needs_review: false,
    published_at: null, human_labeled: true});
  assert.ok(markup.includes('人工分类'));
  assert.ok(!markup.includes('99%'));
});

test('a human pending-review flag does not claim they confirmed the model category', () => {
  const markup = ui().rowMarkup({id:'a'.repeat(32),title:'人工智能芯片',source_name:'来源',
    category:'科技',correction:'待核对',score:.99,saved:false,needs_review:true,human_labeled:true});
  assert.ok(markup.includes('人工标记待核对'));
  assert.ok(!markup.includes('人工分类'));
});
