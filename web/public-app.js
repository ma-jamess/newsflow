'use strict';
const state={bootstrap:null};
const el=id=>document.getElementById(id);
let storage;
try{storage=window.localStorage;}catch{}
const publicBackend=new NewsflowPublic.PublicBackend({fetch:window.fetch.bind(window),storage});
function toast(message){el('toast').textContent=message;el('toast').classList.remove('hidden');setTimeout(()=>el('toast').classList.add('hidden'),4000);}
async function api(path,payload){const data=await publicBackend.request(path,payload);if(!publicBackend.readerError)el('startup-error').classList.add('hidden');return data;}
async function download(path,payload,name){
  const blob=new Blob([publicBackend.exportCSV(payload)],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function navigate(page){
  page=page==='evaluation'?'evaluation':'news';
  document.querySelectorAll('.page').forEach(node=>node.classList.toggle('hidden',node.id!=='page-'+page));
  document.querySelectorAll('button[data-page]').forEach(node=>node.classList.toggle('active',node.dataset.page===page));
  document.body.dataset.page=page;delete document.body.dataset.newsDetail;
  if(location.hash!=='#'+page)history.replaceState(null,'','#'+page);
  if(page==='evaluation')loadReport();
  window.scrollTo({top:0,behavior:'instant'});
}
async function loadReport(){
  try{
    const response=await fetch('data/report.json',{cache:'no-cache'});
    if(!response.ok)throw new Error();
    const report=await response.json(),escape=LiveNewsUI.escape;
    el('public-report').innerHTML='<div class="table-wrap"><table><thead><tr><th>模型</th><th>测试准确率</th><th>宏 F1</th><th>ECE</th></tr></thead><tbody>'+Object.values(report.models).map(model=>'<tr><td>'+escape(model.name)+'</td><td>'+escape((model.test.accuracy*100).toFixed(4))+'%</td><td>'+escape(model.test.macro_f1.toFixed(6))+'</td><td>'+escape(model.test.ece.toFixed(5))+'</td></tr>').join('')+'</tbody></table></div><p class="muted">推荐模型来自独立选参集；完整数据划分、校准、混淆矩阵和训练步骤随源码提供。</p>';
  }catch{el('public-report').textContent='报告暂时无法读取，请稍后重试；完整实验记录也在下载项目中。';}
}
async function init(){
  state.bootstrap={public_site:true,model_names:{nb:'朴素贝叶斯',lr:'逻辑回归',svm:'线性 SVM'},download_url:'https://github.com/ma-jamess/newsflow/archive/refs/heads/main.zip'};
  try{
    await publicBackend.load(true);
    const data=publicBackend.data,base=LiveNewsUI.safeLink(data.source_url)||'https://github.com/ma-jamess/newsflow';
    state.bootstrap={public_site:true,model_names:{nb:'朴素贝叶斯',lr:'逻辑回归',svm:'线性 SVM'},download_url:base+'/archive/refs/heads/main.zip'};
  }catch(error){el('startup-error').textContent=error.message;el('startup-error').classList.remove('hidden');}
  navigate(location.hash.slice(1));
}
document.querySelectorAll('button[data-page]').forEach(button=>button.onclick=()=>navigate(button.dataset.page));
window.addEventListener('hashchange',()=>navigate(location.hash.slice(1)));
el('help-open').onclick=()=>el('help-dialog').showModal();el('help-close').onclick=()=>el('help-dialog').close();
window.NewsroomReady=init();
