# 1.2 工作空间改进实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 增强新闻分类的批量分析与人工核对体验，完成清晰雅观的本地界面。
**Architecture:** 原生页面保持既有API，纯数据辅助函数负责筛选、排序和统计；页面脚本负责交互，CSS负责响应式视觉。
**Tech Stack:** Python、HTML/CSS/JavaScript、Node内置测试、固定版本Lucide SVG。
**Spec:** docs/superpowers/specs/2026-10-22-workspace-polish-design.md

## Global Constraints
- `python run.py`；无新增运行依赖或在线页面资源。
- 模型、数据、实验成绩不变；原版目录只读。
- 新版为1.2.0，旧发行包保留。

## Review Focus
- 无效与未识别行不参与类别分母，0条有预测时显示0而不是NaN。
- 类别、状态、搜索组合一致，全部导出不受过滤影响。
- 已人工标注的低概率记录不出现在待核对队列。
- 批量阈值独立于单条阈值，请求期间变更继续拒绝旧响应。
- 390px页面、长标题、缺失剪贴板权限不破坏正常分类。

### Task 1: 数据视图与行为
**Files:** 新增web/ui-data.js、tests/workspace.test.cjs；修改web/app.js、web/improvements.js、web/index.html。
**Interfaces:** summary(rows) -> {categories,total,predicted,review,invalid,unknown}；selectBatch(rows,{search,status,category}) -> rows；selectHistory(rows,{search,filter,sort}) -> rows；pendingBatch(rows) -> rows。CommonJS测试与浏览器共用。
- [ ] 写并运行失败测试：两个体育预测（含review）和一条科技、空标题、unknown得到分母3；按类别与状态交集；已标注记录排除；低概率排序；批量API收到独立阈值。
- [ ] 实现辅助函数，批量分类读取batch-threshold，renderBatch与renderHistory调用辅助函数。
- [ ] 全部前端与Python测试通过。

### Task 2: 工作空间视觉与交互
**Files:** 重写web/style.css，新增web/workspace.js，修改web/index.html与newsroom/server.py静态白名单；新增third_party/lucide/LICENSE与来源记录。
**Interfaces:** renderBatch()之后渲染真实类别分布；新增按钮调用既有download接口；区分单条与批量阈值。
- [ ] 获取固定提交SVG与许可证；统一导航、输入、结果、表格、状态和小屏样式。
- [ ] 实现分布条、按类别筛选、待核对导出、单条复制、Ctrl+Enter和历史排序。
- [ ] Edge验证单条、批量、待核对、历史标注、实验、390px布局；修复真实问题。

### Task 3: 交付验证
**Files:** README、docs/GitHub参考与改进.md、docs/verification、newsroom/__init__.py、scripts/package.py。
- [ ] 独立代码审阅与必要修复；全套测试、语法检查、模型哈希核对。
- [ ] 文档说明参考项目、许可证、实际新增功能与边界；生成1.2包，清单和解压启动验证。
- [ ] 提交可审阅代码，报告截图、功能和测试证据。
