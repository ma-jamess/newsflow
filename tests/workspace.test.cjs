const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function data() { return require('../web/ui-data.js'); }
const rows = [
  {title:'足球冠军',prediction:'体育',status:'ok',score:.9},
  {title:'体育芯片',prediction:'体育',status:'review',score:.45},
  {title:'芯片发布',prediction:'科技',status:'ok',score:.99},
  {title:'',prediction:'',status:'invalid',score:null},
  {title:'abc',prediction:'',status:'unknown',score:null},
];

test('batch distribution includes uncertain predictions but excludes rows without a class', () => {
  const result = data().summary(rows);
  assert.equal(result.total,5);
  assert.equal(result.predicted,3);
  assert.deepEqual(result.categories,{体育:2,科技:1,教育:0,财经:0,娱乐:0});
  assert.equal(result.review,1);
  assert.equal(result.invalid,1);
  assert.equal(result.unknown,1);
  assert.equal(data().summary(rows.slice(3)).predicted,0);
});

test('category, status and title filters form an intersection without losing source rows', () => {
  assert.deepEqual(data().selectBatch(rows,{search:'芯片',status:'review',category:'体育'}),[rows[1]]);
  assert.equal(rows.length,5);
  assert.deepEqual(data().pendingBatch(rows),[rows[1],rows[3],rows[4]]);
});

test('pending history excludes annotated records and unknown records sort before finite scores', () => {
  const history = [
    {id:3,title:'高概率',status:'ok',score:.9,correction:''},
    {id:2,title:'低概率已确认',status:'review',score:.3,correction:'教育'},
    {id:1,title:'低概率待核对',status:'review',score:.4,correction:''},
    {id:4,title:'未识别',status:'unknown',score:null,correction:''},
  ];
  assert.deepEqual(data().selectHistory(history,{filter:'pending',sort:'uncertain'}).map(r=>r.id),[4,1]);
  assert.deepEqual(data().selectHistory(history,{filter:'corrected'}).map(r=>r.id),[2]);
  assert.deepEqual(data().selectHistory(history,{search:'概率',sort:'recent'}).map(r=>r.id),[3,2,1]);
  assert.deepEqual(history.map(r=>r.id),[3,2,1,4]);
});

test('batch requests use the independent batch threshold', async () => {
  const elements = new Map();
  const element = id => {
    if(!elements.has(id)) elements.set(id,{value:'',files:[],classList:{add(){},remove(){}},textContent:'',innerHTML:''});
    return elements.get(id);
  };
  element('threshold').value='.2';
  element('batch-threshold').value='.9';
  element('batch-model').value='svm';
  element('batch-text').value='足球冠军';
  let sent;
  const context=vm.createContext({$:element,state:{batchRevision:0},metric:()=>'',renderBatch(){},pct:String,
    api:async (name,payload)=>{sent=payload;return {rows:[],counts:{ok:0,review:0,invalid:0,unknown:0}};}});
  const source=fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8');
  vm.runInContext(source.slice(source.indexOf('async function runBatch()'),source.indexOf('function renderBatch()')),context);
  await vm.runInContext('runBatch()',context);
  assert.equal(sent.threshold,.9);
});
