'use strict';
const NewsUI = (() => {
  const labels = ['体育','科技','教育','财经','娱乐'];
  const needsReview = row => ['review','unknown','invalid'].includes(row.status);
  function summary(rows) {
    const categories = Object.fromEntries(labels.map(label => [label,0]));
    for (const row of rows) if (labels.includes(row.prediction)) categories[row.prediction]++;
    return {categories,total:rows.length,predicted:Object.values(categories).reduce((a,b)=>a+b,0),
      review:rows.filter(r=>r.status==='review').length,invalid:rows.filter(r=>r.status==='invalid').length,
      unknown:rows.filter(r=>r.status==='unknown').length};
  }
  function selectBatch(rows,{search='',status='',category=''}={}) {
    return rows.filter(r=>r.title.toLowerCase().includes(search.toLowerCase())&&(!status||r.status===status)&&(!category||r.prediction===category));
  }
  function pendingBatch(rows) { return rows.filter(needsReview); }
  function selectHistory(rows,{search='',filter='',sort='recent'}={}) {
    const selected=rows.filter(r=>r.title.toLowerCase().includes(search.toLowerCase())&&
      (!filter||(filter==='corrected'?Boolean(r.correction):filter==='pending'?needsReview(r)&&!r.correction:r.status==='review')));
    if(sort==='uncertain') selected.sort((a,b)=>(a.score??-1)-(b.score??-1)||b.id-a.id);
    else selected.sort((a,b)=>b.id-a.id);
    return selected;
  }
  return {summary,selectBatch,pendingBatch,selectHistory};
})();
if(typeof module!=='undefined') module.exports=NewsUI;
