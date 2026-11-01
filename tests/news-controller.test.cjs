'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return {promise, resolve, reject};
}
function controller(options) {
  return new (require('../web/live-news.js').NewsController)(options);
}
const data = (title, total = 1) => ({rows: [{id: title, title, saved: false}], total, stats: {}, update: {}});

test('a slower previous filter response never replaces the current category', async () => {
  const jobs = [], shown = [];
  const feed = controller({api: () => {const job = deferred(); jobs.push(job); return job.promise;},
    onList: result => {if (result) shown.push(result.rows[0]?.title);}});
  const older = feed.setFilters({category: '体育'});
  const newer = feed.setFilters({category: '科技'});
  jobs[1].resolve(data('芯片'));
  await newer;
  jobs[0].resolve(data('足球'));
  await older;
  assert.deepEqual(shown, ['芯片']);
  assert.equal(feed.filters.category, '科技');
});

test('changing filters invalidates pending article details and their errors', async () => {
  const detail = deferred(), shown = [], errors = [];
  const feed = controller({api: path => path.startsWith('news/detail') ? detail.promise : Promise.resolve(data('new')),
    onDetail: result => {if (result) shown.push(result.title);}, onError: error => errors.push(error)});
  const pending = feed.select('old');
  await feed.setFilters({saved: true});
  detail.reject(new Error('old detail failed'));
  await pending;
  assert.deepEqual(shown, []);
  assert.deepEqual(errors, []);
  assert.equal(feed.selectedId, null);
});

test('rapid article selection displays only the latest chosen article', async () => {
  const jobs = [], shown = [];
  const feed = controller({api: () => {const job = deferred(); jobs.push(job); return job.promise;},
    onDetail: result => {if (result) shown.push(result.title);}});
  const first = feed.select('one'), second = feed.select('two');
  jobs[1].resolve({id: 'two', title: 'Two'});
  await second;
  jobs[0].resolve({id: 'one', title: 'One'});
  await first;
  assert.deepEqual(shown, ['Two']);
});

test('an empty last page after removal returns to the last available page', async () => {
  const paths = [], shown = [];
  const feed = controller({api: async path => {paths.push(path); return paths.length === 1 ? {...data('x', 50), rows: []} : data('remaining', 50);},
    onList: result => {if (result) shown.push(result.rows.length);}});
  await feed.setFilters({page: 2, saved: true});
  assert.equal(feed.filters.page, 1);
  assert.equal(new URLSearchParams(paths[1].split('?')[1]).get('offset'), '0');
  assert.deepEqual(shown, [1]);
});

test('bookmark write failure does not pretend the article has been saved', async () => {
  const errors = [];
  const feed = controller({api: async path => {if (path === 'news/save') throw new Error('disk unavailable'); return data('one');},
    onError: error => errors.push(error.message)});
  await feed.load();
  await feed.toggleSaved('one');
  assert.equal(feed.data.rows[0].saved, false);
  assert.deepEqual(errors, ['disk unavailable']);
});

for (const operation of ['bookmark', 'category']) {
  test(`a pre-mutation detail response cannot undo a successful ${operation} in the controls`, async () => {
    const oldDetail = deferred(), writes = [];
    let detailReads = 0, stored = {id:'one',title:'News',saved:false,category:'科技'};
    const initial = {...stored};
    const feed = controller({api: async (path, payload) => {
      if (path.startsWith('news/detail')) return ++detailReads === 1 ? oldDetail.promise : {...stored};
      if (path === 'news/save' || path === 'news/feedback') {
        writes.push({...payload});
        stored = {...stored,...(path === 'news/save' ? {saved:payload.saved} : {category:payload.category,human_labeled:true})};
        return {row:{...stored}};
      }
      return {...data('one'),rows:[{...stored}]};
    }});
    await feed.load();
    const firstRead = feed.select('one');
    if (operation === 'bookmark') await feed.toggleSaved('one');
    else await feed.correct('one','教育');
    oldDetail.resolve(initial);
    await firstRead;
    if (operation === 'bookmark') {
      assert.equal(feed.detail.saved,true);
      await feed.toggleSaved('one');
      assert.deepEqual(writes.map(write=>write.saved),[true,false]);
    } else {
      assert.equal(feed.detail.category,'教育');
      assert.equal(feed.detail.human_labeled,true);
    }
  });
}
