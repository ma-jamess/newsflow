# Codex 毕设实现计划

**Goal:** 独立交付 Python 一键启动的五类新闻标题分类系统及全部源码。
**Architecture:** 标准库 HTTP 服务调用模型服务；静态网页显示结果；SQLite 存放历史和纠错。独立训练、只在训练集提取特征、dev 分开选参/校准、test 最终评估。
**Tech Stack:** Python、scikit-learn、jieba、NumPy、SQLite、HTML/CSS/JS。
**Spec:** docs/design.md

## Global Constraints

旧项目只读。仅在新目录写入。默认 Edge。支持 `python run.py`。无外部模型调用。保留公开数据来源。所有实验数据真实生成。

## Review Focus

- 校准集不能混入训练，测试集不能用于推荐算法或阈值选择。
- CSV 中文编码、重复表头、空标题、超长、公式、超过上限的行为。
- 首次启动依赖缺失、旧模型版本、模型篡改和端口被其他服务占用。
- 解释对应当前标题的实际线性特征，不能用类别关键词冒充。
- 纠错持久化，XSS 字符串作为文本展示，跨源请求不得写历史。

## Tasks

- [x] 1. 数据与输入：先写归一化、去重冲突、哈希、CSV 边界测试；运行失败；实现 `newsroom/data.py` 与 `newsroom/csvio.py`；测试通过。
- [x] 2. 模型实验：先写特征仅训练拟合、校准集隔离、预测一致性、未知词及模型篡改测试；失败后实现 `newsroom/ml.py`、`scripts/train.py`、`scripts/prepare_data.py`；运行全量真实实验。
- [x] 3. 本地服务：先写 SQLite 纠错持久化、API 输入与同源令牌测试；失败后实现 `newsroom/store.py`、`newsroom/server.py`、`run.py`；验证 JSON、上传、导出与端口行为。
- [x] 4. 界面：实现五页统一界面，Edge 操作单条、批量、实验、历史纠错、方法；检查截图。
- [x] 5. 交付：编写 README、技术报告、比较报告、答辩讲稿；生成独立源码 ZIP；全套测试、启动验证、原版哈希复核；独立审阅并解决重要发现。

## 执行记录

实现方式由本会话自行完成；使用 writing-plans、test-driven-development、security-review 和 verification-before-completion 对关键行为进行验证。独立新项目目录满足隔离要求，无需在旧仓库创建 worktree。

最终独立审阅记录：环境隔离、CSV空行、SQLite连接关闭三个发现分别以失败测试复现并修复；20项测试通过。Minor：历史导出上限5000条，保留该限制并在README明示。浏览器自动文件选择因扩展权限受限，使用本地HTTP接口完成文件上传与导出实测，没有更改权限。Windows安装的 Word 负责论文预览导出，Poppler渲染10页，逐页视觉检查通过。
