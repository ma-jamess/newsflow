(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.NewsflowPublic=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const CATEGORIES=['体育','科技','教育','财经','娱乐'];
  const PREFIX='newsflow.public.v1.';
  const clone=value=>JSON.parse(JSON.stringify(value));
  const validDate=value=>typeof value==='string'&&Number.isFinite(Date.parse(value));
  function safeURL(value){try{const url=new URL(value);return typeof value==='string'&&!/[\x00-\x20\x7f]/.test(value)&&['http:','https:'].includes(url.protocol)&&!url.username&&!url.password;}catch{return false;}}
  function validate(data){
    if(!data||data.schema_version!==1||!validDate(data.generated_at)||!Array.isArray(data.rows)||data.rows.length>1000||!Array.isArray(data.sources)||data.sources.length>20||!data.update)throw new Error('新闻数据格式错误');
    const ids=new Set(data.sources.map(source=>source.id));
    for(const source of data.sources){if(!/^[a-zA-Z0-9-]{1,80}$/.test(source.id)||typeof source.name!=='string'||!safeURL(source.url)||!['fresh','stale','empty','error','disabled','pending','unknown'].includes(source.status))throw new Error('新闻来源数据错误');}
    for(const row of data.rows){
      if(!/^[a-f0-9]{32}$/.test(row.id)||typeof row.title!=='string'||!row.title||row.title.length>500||!safeURL(row.url)||!ids.has(row.source_id)||!row.result||!['',...CATEGORIES].includes(row.result.prediction))throw new Error('新闻数据格式错误');
      for(const value of Object.values(row.result.probabilities||{})){if(!Number.isFinite(value)||value<0||value>1)throw new Error('新闻分类数据错误');}
    }
    return clone(data);
  }
  class PublicBackend{
    constructor({fetch:fetcher,storage,clock=()=>new Date()}){
      this.fetch=fetcher;this.storage=storage;this.clock=clock;this.data=null;this.checked=0;this.generation=0;this.readerError=false;
      this.bookmarks=this.read('bookmarks',{});this.corrections=this.read('corrections',{});this.preferences=this.read('sources',{});
      try{this.data=validate(this.read('snapshot',null));}catch{}
    }
    read(key,fallback){try{const value=JSON.parse(this.storage?.getItem(PREFIX+key)||'null');return value&&typeof value==='object'&&!Array.isArray(value)?value:fallback;}catch{return fallback;}}
    save(key,value){try{if(!this.storage)throw new Error();this.storage.setItem(PREFIX+key,JSON.stringify(value));}catch{throw new Error('浏览器无法保存，请允许站点存储或清理空间后重试');}}
    async load(force=false){
      if(!force&&this.data&&this.checked&&this.clock().getTime()-this.checked<20000)return this.data;
      const ticket=++this.generation,controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);
      try{
        const response=await this.fetch('data/news.json',{cache:'no-cache',signal:controller.signal});
        if(!response.ok)throw new Error('新闻数据暂不可用');
        const data=validate(await response.json());
        if(Date.parse(data.generated_at)>this.clock().getTime()+900000)throw new Error('新闻数据时间异常');
        if(ticket===this.generation){
          if(!this.data||Date.parse(data.generated_at)>=Date.parse(this.data.generated_at))this.data=data;
          this.checked=this.clock().getTime();this.readerError=false;
          try{this.save('snapshot',this.data);}catch{}
        }
      }catch(error){if(ticket===this.generation){this.readerError=true;this.checked=this.clock().getTime();}if(!this.data)throw new Error('暂时无法读取新闻数据，请检查网络后重试');}
      finally{clearTimeout(timer);}
      return this.data;
    }
    decorate(row){
      const correction=['待核对',...CATEGORIES].includes(this.corrections[row.id])?this.corrections[row.id]:'';
      return {...row,saved:Object.hasOwn(this.bookmarks,row.id),correction,human_labeled:!!correction,
        category:CATEGORIES.includes(correction)?correction:row.result.prediction,
        needs_review:correction==='待核对'||!correction&&row.result.status!=='ok'};
    }
    sources(){return this.data.sources.map(source=>{const enabled=typeof this.preferences[source.id]==='boolean'?this.preferences[source.id]:true;return {...source,enabled,status:enabled?source.status:'disabled'};});}
    allRows(){
      const rows=new Map(this.data.rows.map(row=>[row.id,row]));
      for(const [id,row] of Object.entries(this.bookmarks)){if(!rows.has(id)&&row&&row.id===id&&/^[a-f0-9]{32}$/.test(id)&&safeURL(row.url)&&row.result)rows.set(id,row);}
      return [...rows.values()].map(row=>this.decorate(row));
    }
    select(filters={}){
      const enabled=new Set(this.sources().filter(source=>source.enabled).map(source=>source.id));
      const flag=value=>value===true||value==='1';
      const saved=flag(filters.saved),review=flag(filters.review),q=String(filters.q||'').toLocaleLowerCase();
      const cutoff=this.clock().getTime()-72*3600000;
      return this.allRows().filter(row=>
        (saved?row.saved:enabled.has(row.source_id)&&(!validDate(row.published_at||row.first_seen_at)||Date.parse(row.published_at||row.first_seen_at)>=cutoff))&&
        (!review||row.needs_review)&&(!filters.category||row.category===filters.category)&&(!filters.source||row.source_id===filters.source)&&
        (!q||(row.title+' '+(row.summary||'')).toLocaleLowerCase().includes(q)))
        .sort((a,b)=>Date.parse(b.published_at||b.first_seen_at)-Date.parse(a.published_at||a.first_seen_at)||a.id.localeCompare(b.id));
    }
    snapshot(filters={}){
      const rows=this.select(filters),all=this.select(),saved=this.select({saved:true});
      const categories=Object.fromEntries(CATEGORIES.map(category=>[category,all.filter(row=>row.category===category).length]));
      const offset=Math.max(0,Number(filters.offset)||0),limit=Math.min(100,Math.max(1,Number(filters.limit)||50));
      return {rows:rows.slice(offset,offset+limit),total:rows.length,stats:{total:all.length,saved:saved.length,review:all.filter(row=>row.needs_review).length,categories},
        update:{...this.data.update,refreshing:false},interval_seconds:300,server_time:this.clock().toISOString(),public_site:true,reader_error:this.readerError};
    }
    async request(path,payload){
      await this.load();
      const [route,query='']=path.split('?'),filters=Object.fromEntries(new URLSearchParams(query));
      if(payload===undefined){
        if(route==='news')return this.snapshot(filters);
        if(route==='news/sources')return {sources:this.sources(),interval_seconds:300};
        if(route==='news/detail'){const row=this.allRows().find(item=>item.id===filters.id);if(!row)throw new Error('这条新闻已不在列表，请刷新');return row;}
      }
      if(route==='news/refresh'){await this.load(true);return {started:false,public_site:true,cached:this.readerError};}
      if(route==='news/sources'){
        if(!payload.id||!this.data.sources.some(source=>source.id===payload.id)||typeof payload.enabled!=='boolean')throw new Error('自定义订阅请在下载版中添加');
        const preferences={...this.preferences,[payload.id]:payload.enabled};this.save('sources',preferences);this.preferences=preferences;return {sources:this.sources()};
      }
      const row=this.allRows().find(item=>item.id===payload?.id);
      if(!row)throw new Error('新闻记录不存在');
      if(route==='news/save'){
        if(typeof payload.saved!=='boolean')throw new Error('收藏设置错误');
        const bookmarks={...this.bookmarks};if(payload.saved)bookmarks[row.id]=row;else delete bookmarks[row.id];
        this.save('bookmarks',bookmarks);this.bookmarks=bookmarks;return {saved:true};
      }
      if(route==='news/feedback'){
        if(![...CATEGORIES,'待核对'].includes(payload.category))throw new Error('分类无效');
        const corrections={...this.corrections,[row.id]:payload.category};this.save('corrections',corrections);this.corrections=corrections;return {saved:true};
      }
      throw new Error('该功能请使用下载版');
    }
    exportCSV(filters){
      const cell=value=>{let text=String(value??'');if(/^[=+@\-\t\r]/.test(text.trimStart()))text="'"+text;return '"'+text.replace(/"/g,'""')+'"';};
      const fields=['title','category','source_name','url','published_at','correction','score'];
      return '\ufeff'+[fields,...this.select(filters).slice(0,5000).map(row=>fields.map(field=>row[field]))].map(row=>row.map(cell).join(',')).join('\r\n');
    }
  }
  return {PublicBackend,validate};
});
