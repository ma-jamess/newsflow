const {test} = require('node:test');
const assert = require('node:assert/strict');
const {PublicBackend} = require('../web/public-backend.js');
const now = new Date('2026-11-01T08:00:00Z');
const id = 'a'.repeat(32), second = 'b'.repeat(32);
function article(key, title, category) {
  return {id:key,title,summary:'摘要',source_id:'ithome',source_name:'IT之家',url:'https://example.org/'+key,
    published_at:now.toISOString(),first_seen_at:now.toISOString(),category,score:.8,needs_review:false,saved:false,correction:'',human_labeled:false,
    result:{prediction:category,score:.8,status:'ok',model:'svm',probabilities:{[category]:.8}}};
}
function snapshot(rows=[article(id,'足球队夺冠','体育'),article(second,'人工智能芯片发布','科技')]) {
  return {schema_version:1,interval_seconds:300,generated_at:now.toISOString(),rows,
    sources:[{id:'ithome',name:'IT之家',url:'https://www.ithome.com/rss/',enabled:true,status:'fresh'}],
    update:{status:'success',last_finished_at:now.toISOString(),last_success_at:now.toISOString(),errors:0}};
}
class Storage {
  constructor(){this.data=new Map();}
  getItem(key){return this.data.get(key)||null;}
  setItem(key,value){this.data.set(key,value);}
}
function backend(data=snapshot(),storage=new Storage(),fetcher){
  return new PublicBackend({storage,clock:()=>now,fetch:fetcher|| (async()=>({ok:true,json:async()=>structuredClone(data)}))});
}
test('public filters combine category search source bookmark and human correction',async()=>{
  const app=backend(); await app.request('news');
  await app.request('news/save',{id,saved:true});
  await app.request('news/feedback',{id,category:'科技'});
  const data=await app.request('news?category=科技&q=足球&source=ithome&saved=1');
  assert.equal(data.total,1); assert.equal(data.rows[0].correction,'科技');
  assert.equal(data.rows[0].result.prediction,'体育');
});
test('saved snapshots and corrections survive a new deployment and remain per browser',async()=>{
  const storage=new Storage(), first=backend(snapshot(),storage);
  await first.request('news'); await first.request('news/save',{id,saved:true});
  await first.request('news/feedback',{id,category:'教育'});
  const next=backend(snapshot([article(second,'芯片','科技')]),storage);
  const saved=await next.request('news?saved=1');
  assert.equal(saved.total,1); assert.equal(saved.rows[0].category,'教育');
  assert.equal((await backend().request('news?saved=1')).total,0);
});
test('public CSV protects formulas and exports only the current filter',async()=>{
  const app=backend(snapshot([article(id,'=HYPERLINK("x")','体育'),article(second,'芯片','科技')]));
  await app.request('news');
  const csv=app.exportCSV({category:'体育'});
  assert.match(csv,/\'=HYPERLINK/); assert.ok(!csv.includes('芯片'));
});
test('offline reader keeps a validated cache and marks the connection problem',async()=>{
  const storage=new Storage(); await backend(snapshot(),storage).request('news');
  const offline=backend(snapshot(),storage,async()=>{throw new Error('offline');});
  const data=await offline.request('news');
  assert.equal(data.total,2); assert.equal(data.reader_error,true);
});
test('storage failure does not falsely save or change the visible article',async()=>{
  const storage={getItem:()=>null,setItem:()=>{throw new Error('quota');}};
  const app=backend(snapshot(),storage); await app.request('news');
  await assert.rejects(app.request('news/save',{id,saved:true}),/保存/);
  assert.equal((await app.request('news?saved=1')).total,0);
});
test('public backend never accepts arbitrary subscriptions or unsafe snapshots',async()=>{
  const app=backend(); await app.request('news');
  await assert.rejects(app.request('news/sources',{name:'bad',url:'https://127.0.0.1/feed'}),/下载版/);
  const unsafe=backend({...snapshot(),rows:[{...article(id,'bad','体育'),url:'javascript:alert(1)'}]});
  await assert.rejects(unsafe.request('news'),/数据/);
});
test('late older refresh cannot replace newer published data',async()=>{
  const jobs=[];
  const app=backend(snapshot(),new Storage(),()=>new Promise(resolve=>jobs.push(resolve)));
  const old=app.load(true),fresh=app.load(true);
  jobs[1]({ok:true,json:async()=>snapshot([article(second,'新新闻','科技')])});
  await fresh;
  jobs[0]({ok:true,json:async()=>snapshot([article(id,'旧新闻','体育')])});
  await old;
  assert.equal(app.snapshot().rows[0].title,'新新闻');
  assert.equal(app.readerError,false);
});
test('RSS titles up to 500 characters do not reject the whole deployment',async()=>{
  const title='人工智能芯片'.repeat(40),app=backend(snapshot([article(id,title,'科技')]));
  assert.equal((await app.request('news')).rows[0].title,title);
});
