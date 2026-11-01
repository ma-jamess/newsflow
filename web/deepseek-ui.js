'use strict';
(function(root){
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function markup(result){
    const names={ok:'分类完成',review:'需人工核对',unknown:'待核对类别'};
    const status=Object.hasOwn(names,result.status)?result.status:'review';
    const notice=status==='unknown'?'不强制归入五类，请结合正文人工核对。':status==='review'?'标题存在歧义，建议结合正文人工核对。':'';
    return `<div class="card-title"><h2>DeepSeek 分类结果</h2><span class="status ${status}">${names[status]}</span></div>
      <div class="result-hero"><div><small>按标题语义判断</small><div class="result-label">${escape(result.category)}</div></div></div>
      <div class="subheading"><span>判断理由</span><span class="label-muted">思考模式</span></div>
      <p class="deepseek-reason">${escape(result.reason)}</p>
      <p class="explanation-note">理由由大模型生成，仍可能判断有误。这里未进行概率校准，请以人工核对为准。</p>
      ${notice?`<div class="notice">${notice}</div>`:''}
      <div class="result-meta"><span>DeepSeek V4.1 Flash 1017 · ${escape(result.elapsed_ms)} ms</span><button id="result-correct" class="text-button">人工核对 →</button></div>`;
  }
  const api={markup};
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.DeepSeekUI=api;
})(globalThis);
