'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function deferred() {
  let resolve;
  const promise = new Promise(yes=>{resolve=yes;});
  return {promise,resolve};
}
async function flush() {for(let i=0;i<16;i++)await Promise.resolve();}
const source = (enabled=true,id='one') => ({id,name:'Source',url:'https://example.org/feed',
  enabled,status:enabled?'fresh':'disabled',description:'Feed'});
const news = {rows:[],total:0,stats:{total:0,saved:0,review:0,categories:{体育:0,科技:0,教育:0,财经:0,娱乐:0}},
  update:{refreshing:false,status:'idle'},server_time:'2026-10-31T08:00:00Z'};

function mounted({offline=false,publicSite=false}={}) {
  const elements = new Map(), reads = [], writes = [];
  let stored = [source()];
  class Element {
    constructor(id) {
      this.id=id;this.value='';this.disabled=false;this.dataset={};this.children=[];
      this.classList={add(){},remove(){},toggle(){}};
    }
    set innerHTML(value) {
      this.markup=value;
      if(this.id==='news-source-list')this.children=[...value.matchAll(/<input type="checkbox" data-source-toggle="([^"]+)"([^>]*)>/g)].map(match=>{
        const input=new Element(match[1]);input.dataset.sourceToggle=match[1];input.checked=/\bchecked\b/.test(match[2]);return input;
      });
    }
    get innerHTML(){return this.markup||'';}
    querySelectorAll(selector){return selector==='[data-source-toggle]'?this.children:[];}
    contains(){return false;}
    addEventListener(){}
    setAttribute(){}
    focus(){}
    showModal(){}
    close(){}
    reset(){}
  }
  const getElement = id => {if(!elements.has(id))elements.set(id,new Element(id));return elements.get(id);};
  const context = vm.createContext({module:{exports:{}},require:()=>require('../web/live-news-ui.js'),
    document:{getElementById:getElement,querySelectorAll:()=>[],addEventListener(){},body:{dataset:{}},activeElement:null},
    setTimeout:()=>0,clearTimeout(){},Event:class {}});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../web/live-news.js'),'utf8'),context);
  const api = async (route,payload) => {
    if(offline)throw new Error('offline');
    if(route.startsWith('news?'))return news;
    if(route==='news/sources' && payload===undefined){const job=deferred();reads.push(job);return job.promise;}
    if(route==='news/sources'){
      writes.push(payload);
      stored=payload.id?stored.map(row=>row.id===payload.id?{...row,enabled:payload.enabled}:row):[...stored,source(true,'extra')];
      return {id:payload.id||'extra',sources:stored};
    }
    throw new Error('Unexpected route '+route);
  };
  context.module.exports.mount({api,download:async()=>{},navigate(){},toast(){},bootstrap:{model_names:{},public_site:publicSite}});
  return {getElement,reads,writes,getStored:()=>stored};
}

test('first-time offline public reader can retry after a failed refresh',async()=>{
  const app=mounted({offline:true,publicSite:true});
  await flush();
  await app.getElement('news-refresh').onclick();
  assert.equal(app.getElement('news-refresh').disabled,false);
  assert.equal(app.getElement('news-refresh-label').textContent,'检查更新');
  assert.equal(app.getElement('news-error').textContent,'offline');
});

test('a stale initial source GET cannot re-enable a source after a successful toggle', async () => {
  const app=mounted();
  app.getElement('news-sources-open').onclick();
  app.reads[1].resolve({sources:[source()]});
  await flush();
  const input=app.getElement('news-source-list').children[0];
  input.checked=false;
  const update=input.onchange();
  await flush();
  for(let i=2;i<app.reads.length;i++)app.reads[i].resolve({sources:app.getStored()});
  await update;
  app.reads[0].resolve({sources:[source()]});
  await flush();
  assert.equal(app.getStored()[0].enabled,false);
  assert.equal(app.getElement('news-source-list').children[0].checked,false);
});

test('a stale initial source GET cannot hide a successfully added subscription', async () => {
  const app=mounted();
  app.getElement('news-sources-open').onclick();
  app.reads[1].resolve({sources:[source()]});
  await flush();
  app.getElement('news-source-name').value='Added';
  app.getElement('news-source-url').value='https://example.org/extra';
  const update=app.getElement('news-source-form').onsubmit({preventDefault(){}});
  await flush();
  for(let i=2;i<app.reads.length;i++)app.reads[i].resolve({sources:app.getStored()});
  await update;
  app.reads[0].resolve({sources:[source()]});
  await flush();
  assert.equal(app.getStored().length,2);
  assert.equal(app.getElement('news-source-list').children.length,2);
});
