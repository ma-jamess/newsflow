const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname,'../web/app.js'),'utf8');

function controls(configured=true){
  const elements={model:{value:'deepseek'},threshold:{value:'0.65',disabled:false},'threshold-value':{},'deepseek-note':{}};
  const bootstrap={report:{recommended_model:'svm'},model_names:{nb:'朴素贝叶斯',lr:'逻辑回归',svm:'SVM',deepseek:'DeepSeek V4.1 Flash 1017'},deepseek:{configured}};
  const context=vm.createContext({state:{bootstrap},esc:x=>x,$:id=>elements[id]});
  vm.runInContext(source.slice(source.indexOf('function optionModels'),source.indexOf('function overview')),context);
  return {context,elements};
}

test('configured DeepSeek defaults for single titles while batch offers only local models',()=>{
  const {context}=controls();
  assert.match(context.optionModels(true),/value="deepseek" selected/);
  assert.ok(!context.optionModels().includes('value="deepseek"'));
  assert.match(context.optionModels(),/value="svm" selected/);
});

test('missing key disables online selection and keeps local default',()=>{
  const {context}=controls(false);
  assert.match(context.optionModels(true),/value="deepseek"[^>]*disabled/);
  assert.match(context.optionModels(true),/value="svm" selected/);
});

test('switching models disables and restores the local threshold with clear processing context',()=>{
  const {context,elements}=controls();
  context.updateModelContext();
  assert.equal(elements.threshold.disabled,true);
  assert.equal(elements['threshold-value'].textContent,'不适用');
  assert.ok(elements['deepseek-note'].textContent.includes('发送本条标题'));
  elements.model.value='svm';
  context.updateModelContext();
  assert.equal(elements.threshold.disabled,false);
  assert.equal(elements['threshold-value'].textContent,'0.65');
  assert.ok(elements['deepseek-note'].textContent.includes('本机处理'));
});
