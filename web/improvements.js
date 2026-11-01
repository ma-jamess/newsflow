'use strict';

// 应用展示层补充功能；预测与评估仍使用原模型，不按测试结果调参。
let comparisonTitle = null;
let comparisonThreshold = null;

async function inputPayload(){
  const file=$('csv-file').files[0];
  if(file){
    if(file.size>5*1024*1024)throw new Error('文件不能超过5 MB');
    const bytes=new Uint8Array(await file.arrayBuffer());
    let binary='';
    for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
    return {file:btoa(binary)};
  }
  const text=$('batch-text').value;
  if(!text.trim())throw new Error('请选择 CSV 或输入多行标题');
  return {titles:text.split(/\r?\n/)};
}

async function previewInput(){
  const button=$('batch-preview');
  const revision=state.batchRevision;
  button.disabled=true;
  $('batch-error').textContent='';
  try{
    const data=await api('preview',await inputPayload());
    if(revision!==state.batchRevision){$('batch-error').textContent='输入已改变，请重新预览。';return;}
    $('preview-output').classList.remove('hidden');
    $('preview-output').innerHTML=`<div class="notice">读取 ${data.total} 条，${data.invalid_count} 条标题无效。预览前 ${data.rows.length} 条；此步骤只检查输入，尚未分类。</div><div class="table-wrap"><table><thead><tr><th>序号</th><th>标题</th><th>真实类别</th><th>输入检查</th></tr></thead><tbody>${data.rows.map((r,i)=>`<tr><td>${i+1}</td><td class="title-cell">${esc(r.title)||'（空标题）'}</td><td>${esc(r.label)||'—'}</td><td>${esc(r.message)}</td></tr>`).join('')}</tbody></table></div>`;
  }catch(error){$('batch-error').textContent=error.message;}
  finally{button.disabled=false;}
}

async function compareTitle(){
  const button=$('compare-submit');
  button.disabled=true;
  $('classify-error').textContent='';
  const title=$('title-input').value;
  const threshold=Number($('threshold').value);
  try{
    const data=await api('compare',{title,threshold});
    comparisonTitle=data.title;
    comparisonThreshold=threshold;
    $('comparison-output').classList.remove('hidden');
    $('comparison-output').innerHTML=`<div class="card-title"><h2>同一标题的三算法对照</h2><span class="status ${data.agreement?'':'review'}">${data.agreement?'三种判断一致':'判断存在分歧'}</span></div><p class="submitted-title">${esc(data.title)}</p><p id="compare-stale" class="notice hidden">输入或阈值已改变，下面仍是上次提交的算法对照；请重新对照。</p><div class="table-wrap"><table><thead><tr><th>算法</th><th>预测类别</th><th>校准概率</th><th>核对状态</th></tr></thead><tbody>${data.rows.map(r=>`<tr><td>${esc(state.bootstrap.model_names[r.model])} ${r.model===data.recommended_model?'<span class="status">推荐</span>':''}</td><td><strong>${esc(r.prediction)||'—'}</strong></td><td>${pct(r.score,1)}</td><td><span class="status ${r.status}">${statusNames[r.status]}</span></td></tr>`).join('')}</tbody></table></div><p class="muted">这里用同一输入查看三种已有模型；分歧可供人工核对，不通过投票改写推荐模型，不记录为三次历史。各模型即使一致也可能分错。</p>`;
    updateStaleResult();
  }catch(error){$('classify-error').textContent=error.message;}
  finally{button.disabled=false;}
}

const originalRenderResult=renderResult;
renderResult=function(result){
  originalRenderResult(result);
  const note=document.createElement('div');
  note.className='submitted-summary';
  const label=document.createElement('small');label.textContent='本次提交的标题';
  const title=document.createElement('p');title.className='submitted-title';title.textContent=result.title;
  const stale=document.createElement('p');stale.id='result-stale';stale.className='notice hidden';
  stale.textContent='输入、算法或阈值已改变，当前仍显示上次结果；请重新分类。';
  note.append(label,title,stale);
  const heading=$('result').querySelector('.card-title');
  if(heading)heading.after(note);else $('result').prepend(note);
  state.resultThreshold=result.requestThreshold;
  updateStaleResult();
};

function updateStaleResult(){
  const stale=$('result-stale');
  if(stale&&state.result)stale.classList.toggle('hidden',state.result.title===$('title-input').value&&state.result.model===$('model').value&&state.resultThreshold===Number($('threshold').value));
  const compareStale=$('compare-stale');
  if(compareStale)compareStale.classList.toggle('hidden',comparisonTitle===$('title-input').value&&comparisonThreshold===Number($('threshold').value));
}

function invalidatePreview(){
  state.batchRevision++;
  $('preview-output').classList.add('hidden');
  $('batch-output').classList.add('hidden');
  $('batch-error').textContent='';
}

function invalidateBatchResult(){
  state.batchRevision++;
  $('batch-output').classList.add('hidden');
}

const originalRenderMatrix=renderMatrix;
renderMatrix=function(){
  originalRenderMatrix();
  if(!$('errors-download')){
    const button=document.createElement('button');
    button.id='errors-download';button.className='secondary';button.textContent='下载所选算法全部误分类 ↓';
    button.onclick=safely(()=>download('errors',{model:$('matrix-model').value},$('matrix-model').value+'_全部误分类.csv'));
    $('error-samples').before(button);
  }
};

// 用简明说明补足指标含义，适合第一次接触模型的使用者。
const originalRenderEvaluation=renderEvaluation;
renderEvaluation=function(){
  originalRenderEvaluation();
  const summary=document.createElement('p');summary.className='notice';
  summary.textContent='准确率看整批预测有多少正确；宏 F1 先评价每个类别再平均；混淆矩阵显示哪些类别容易混淆。分数越高也不保证某条标题一定正确。';
  $('evaluation-content').prepend(summary);
};

$('compare-submit').onclick=compareTitle;
$('batch-preview').onclick=previewInput;
$('title-input').addEventListener('input',updateStaleResult);
$('model').addEventListener('change',updateStaleResult);
$('threshold').addEventListener('input',updateStaleResult);
$('batch-text').addEventListener('input',invalidatePreview);
$('csv-file').addEventListener('change',invalidatePreview);
$('batch-model').addEventListener('change',invalidateBatchResult);
$('batch-threshold').addEventListener('input',invalidateBatchResult);
