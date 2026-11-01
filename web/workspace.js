'use strict';

// 视图操作只使用本次预测和本机历史，不修改模型或正式实验报告。
const baseBatchView=renderBatch;
renderBatch=function(){
  baseBatchView();
  const data=NewsUI.summary(state.batch);
  $('batch-insights').innerHTML=`<div class="card-title"><div><span class="eyebrow">BATCH OVERVIEW</span><h2>这一批新闻，分布在哪里</h2></div><span class="label-muted">${data.predicted} 条有类别预测</span></div><div class="category-distribution">${categories.map((category,index)=>{
    const count=data.categories[category];
    const percent=data.predicted?count/data.predicted*100:0;
    return `<button class="category-bar category-${index}" data-category="${category}" aria-label="筛选${category}类别"><span class="category-caption"><span>${category}</span><b>${count}<small> 条</small></b></span><span class="bar-track"><span class="bar-fill" style="width:${percent}%"></span></span><span class="category-percent">${percent.toFixed(1)}%</span></button>`;
  }).join('')}</div><p class="muted">比例以有类别预测的 ${data.predicted} 条为分母，包含需人工核对的预测；${data.invalid+data.unknown} 条无效或未识别输入不参与比例。点击类别可筛选明细。</p>`;
  $('batch-insights').querySelectorAll('[data-category]').forEach(button=>button.onclick=()=>{
    $('batch-category').value=button.dataset.category;
    state.batchPage=0;
    renderBatch();
    $('batch-insights').querySelector(`[data-category="${button.dataset.category}"]`).focus({preventScroll:true});
  });
  const pending=NewsUI.pendingBatch(state.batch).length;
  $('batch-review-export').disabled=pending===0;
  $('batch-review-export').textContent=`导出待核对 (${pending})`;
};

const baseResultView=renderResult;
renderResult=function(result){
  baseResultView(result);
  if(!result.prediction&&result.model!=='deepseek')return;
  const group=$('result').querySelector('.result-meta');
  const button=document.createElement('button');
  button.type='button';button.className='text-button';button.textContent='复制结果';
  button.onclick=async()=>{
    const text=result.model==='deepseek'
      ?`标题：${result.title}\n预测：${result.category}\n判断理由：${result.reason}\n模型：${state.bootstrap.model_names[result.model]}\n状态：${statusNames[result.status]}`
      :`标题：${result.title}\n预测：${result.prediction}\n模型概率：${pct(result.score,1)}\n算法：${state.bootstrap.model_names[result.model]}\n状态：${statusNames[result.status]}`;
    try{
      await navigator.clipboard.writeText(text);
      toast('分类结果已复制');
    }catch{
      toast('浏览器未允许复制，请手工选择结果文字');
    }
  };
  group.append(button);
};

$('batch-threshold').addEventListener('input',()=>{
  $('batch-threshold-value').textContent=Number($('batch-threshold').value).toFixed(2);
});
$('batch-review-export').onclick=safely(()=>download('export',{rows:NewsUI.pendingBatch(state.batch)},'新闻待核对清单.csv'));
$('title-input').addEventListener('keydown',event=>{
  if(event.ctrlKey&&event.key==='Enter'){
    event.preventDefault();
    if(!$('classify-submit').disabled)$('classify-form').requestSubmit();
  }
});
$('help-open').onclick=()=>$('help-dialog').showModal();
$('help-close').onclick=()=>$('help-dialog').close();
$('help-dialog').addEventListener('click',event=>{if(event.target===$('help-dialog'))$('help-dialog').close();});
