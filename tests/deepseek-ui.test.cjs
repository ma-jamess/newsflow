const {test} = require('node:test');
const assert = require('node:assert/strict');

test('DeepSeek result presents explanation and model without inventing a probability', () => {
  const {markup} = require('../web/deepseek-ui.js');
  const html = markup({category:'科技',prediction:'科技',reason:'主要事件是芯片研发。',status:'ok',elapsed_ms:1800});
  assert.ok(html.includes('主要事件是芯片研发。'));
  assert.ok(html.includes('DeepSeek V4.1 Flash 1017'));
  assert.ok(html.includes('result-correct'));
  assert.ok(!html.includes('98%') && !html.includes('NaN') && !html.includes('undefined'));
});

test('provider explanation and title-like category strings cannot inject HTML', () => {
  const {markup} = require('../web/deepseek-ui.js');
  const html = markup({category:'<img src=x onerror=alert(1)>',reason:'<script>alert(2)</script>',status:'review',elapsed_ms:10});
  assert.ok(html.includes('&lt;script&gt;'));
  assert.ok(!html.includes('<script>') && !html.includes('<img src=x'));
});

test('out of scope result explicitly abstains instead of rendering missing scores', () => {
  const {markup} = require('../web/deepseek-ui.js');
  const html = markup({category:'其他',prediction:'',reason:'天气不属于五类新闻。',status:'unknown',elapsed_ms:200});
  assert.ok(html.includes('其他') && html.includes('不强制归入五类'));
  assert.ok(!html.includes('undefined') && !html.includes('NaN'));
});
