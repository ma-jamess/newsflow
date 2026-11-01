const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function page() {
  const elements = new Map();
  function element(id) {
    if (!elements.has(id)) {
      const classes = new Set(['hidden']);
      elements.set(id, {
        value: '', textContent: '', innerHTML: '', disabled: false, files: [],
        addEventListener() {},
        classList: {
          add: (name) => classes.add(name),
          remove: (name) => classes.delete(name),
          contains: (name) => classes.has(name),
          toggle: (name, hidden) => hidden ? classes.add(name) : classes.delete(name),
        },
      });
    }
    return elements.get(id);
  }
  element('title-input').value = '足球联赛球队夺冠';
  element('threshold').value = '.65';
  const context = vm.createContext({
    $: element, state: {bootstrap: {model_names: {svm: '线性 SVM'}}, result: null, batchRevision: 0},
    esc: String, pct: String, statusNames: {ok: '完成'},
    renderResult() {}, renderMatrix() {}, renderEvaluation() {}, safely: (fn) => fn,
    api: async () => ({title: element('title-input').value, agreement: true,
      recommended_model: 'svm', rows: [{model: 'svm', prediction: '体育', score: .9, status: 'ok'}]}),
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/improvements.js'), 'utf8'), context);
  return {element, context};
}

test('comparison becomes stale when the review threshold changes', async () => {
  const {element, context} = page();
  await vm.runInContext('compareTitle()', context);
  assert.equal(element('compare-stale').classList.contains('hidden'), true);
  element('threshold').value = '.95';
  vm.runInContext('updateStaleResult()', context);
  assert.equal(element('compare-stale').classList.contains('hidden'), false);
  element('threshold').value = '.65';
  vm.runInContext('updateStaleResult()', context);
  assert.equal(element('compare-stale').classList.contains('hidden'), true);
});

test('comparison retains the submitted threshold while a request is pending', async () => {
  const {element, context} = page();
  let complete;
  context.api = () => new Promise(resolve => {complete = resolve;});
  const pending = vm.runInContext('compareTitle()', context);
  element('threshold').value = '.95';
  complete({title: '足球联赛球队夺冠', agreement: true, recommended_model: 'svm', rows: []});
  await pending;
  assert.equal(element('compare-stale').classList.contains('hidden'), false);
});

test('comparison becomes stale after editing the submitted title', async () => {
  const {element, context} = page();
  await vm.runInContext('compareTitle()', context);
  element('title-input').value = '高校招生计划';
  vm.runInContext('updateStaleResult()', context);
  assert.equal(element('compare-stale').classList.contains('hidden'), false);
});

test('a pending preview does not show input that has since been edited', async () => {
  const {element, context} = page();
  element('batch-text').value = '足球冠军';
  let complete;
  context.api = () => new Promise(resolve => {complete = resolve;});
  const pending = vm.runInContext('previewInput()', context);
  for (let i = 0; i < 5 && !complete; i++) await Promise.resolve();
  assert.equal(typeof complete, 'function');
  element('batch-text').value = '高校招生';
  vm.runInContext('invalidatePreview()', context);
  complete({total: 1, invalid_count: 0, rows: [{title: '足球冠军', message: '可分类'}]});
  await pending;
  assert.equal(element('preview-output').classList.contains('hidden'), true);
});

test('a pending batch does not show results for replaced input', async () => {
  const {element, context} = page();
  context.metric = () => '';
  context.renderBatch = () => {};
  const source = fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8');
  vm.runInContext(source.slice(source.indexOf('async function runBatch()'), source.indexOf('function renderBatch()')), context);
  element('batch-text').value = '足球冠军';
  element('batch-model').value = 'svm';
  let complete;
  context.api = () => new Promise(resolve => {complete = resolve;});
  const pending = vm.runInContext('runBatch()', context);
  element('batch-text').value = '高校招生';
  vm.runInContext('invalidatePreview()', context);
  complete({rows: [{title: '足球冠军', prediction: '体育'}], counts: {ok: 1, review: 0, invalid: 0, unknown: 0}});
  await pending;
  assert.equal(element('batch-output').classList.contains('hidden'), true);
});
