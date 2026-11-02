const {test}=require('node:test');
const assert=require('node:assert/strict');
const UI=require('../web/live-news-ui.js');

test('update copy uses the published ECS interval and reflects completion based scheduling',()=>{
  const text=UI.updateSchedule({deployment:'ecs',interval_seconds:120});
  assert.match(text,/2 分钟/);assert.match(text,/完成/);
  assert.doesNotMatch(text,/5 分钟|调度可能延迟/);
});

test('existing Pages updates retain their scheduling qualification',()=>{
  const text=UI.updateSchedule({deployment:'pages',interval_seconds:300});
  assert.match(text,/5 分钟/);assert.match(text,/调度可能延迟/);
});
