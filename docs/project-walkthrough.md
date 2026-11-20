# 新闻分类项目源码与运行说明

本说明对应 NewsFlow 当前的下载版与 ECS 公网版，用于按源码追踪输入、处理、输出和保存。模型实验采用历史标题数据，订阅新闻用于实际预测。界面名称为最新新闻、标题分类、批量分类、分类实验、历史与纠错、设计与原理。

## 在 PyCharm 打开完整项目

选择 Open，打开项目目录 `C:\Users\30909\bishe\newsflow`，不是只打开网页文件。解释器选择本项目 `.venv\Scripts\python.exe`；没有该环境时先运行 `python run.py --setup-only` 准备。首次安装依赖需要联网。不要在演示前临时强制重训。

运行入口有不同职责：

| 入口 | 作用 | 会不会训练 |
| --- | --- | --- |
| `run.py` 的 `main` | 环境检查、载入模型、启动本机 HTTP 服务和新闻更新 | 环境或训练核心不匹配时可能训练；正常载入不训练 |
| `scripts/train.py` 的 `main` | 校验原始数据，清洗、提取特征、训练、选参、校准、测试 | 会训练 |
| `scripts/verify_models.py` 的 `main` | 用现有模型重新核对全部测试样本、原报告和 CSV | 不训练 |
| `scripts/update_ecs_site.py` 的 `main` | 在 ECS 发布公开快照；`--bootstrap` 安装网页资源 | 不训练 |
| `scripts/run_review_demo.py` 的 `main` | 用公开归档案例演示真实模型和独立 SQLite，不自动采集 | 不训练 |

本机启动为 `python run.py`，默认 `http://127.0.0.1:8510`；ECS 地址为 `https://47.115.130.110/newsflow/`。公网阅读版与完整本机实验程序的功能不同，不能把浏览器内的接口适配误当成公网 Python API。

实时列表中的旧案例可能被条数或时间限制移出。备用演示为 `python scripts/run_review_demo.py`，默认8523；先完成项目环境准备，再运行。页面有归档说明，点击“我的收藏”搜索福州，可操作真实模型、接口和独立数据库；不把归档数据称为当前实时新闻。

## 各文件负责什么

| 文件 | 主要职责 | 应能解释的细节 |
| --- | --- | --- |
| `run.py` | 应用入口 | 项目根目录、解释器、启动端口、模型自检 |
| `newsroom/data.py` | 标题与数据 | 标签映射、归一化、跨集合去重和冲突检查 |
| `newsroom/ml.py` | 分类核心 | TF-IDF、三个分类器、选参、校准、预测和特征贡献 |
| `newsroom/model_reports.py` | 报告生成 | 由已有指标生成可读报告，不训练；核对矩阵总数 |
| `newsroom/feeds.py` | 读取订阅 | HTTPS、地址检查、超时、大小限制、RSS/Atom 解析 |
| `newsroom/sources.json` | 内置来源目录 | 名称、稳定 ID、订阅链接与发布方地址 |
| `newsroom/feed_catalog.py` | 来源目录校验 | 结构、ID、数量与 URL 合法性 |
| `newsroom/live_news.py` | 更新协调 | 三个抓取线程、逐来源错误处理、调用本地模型 |
| `newsroom/news_store.py` | 新闻存储 | 来源表、文章表、按链接合并、收藏、人工类别 |
| `newsroom/store.py` | 单条历史 | 标题预测历史、人工标签、备注和持久化 |
| `newsroom/server.py` | 本机 HTTP | 静态资源白名单、同源检查、单条/批量/新闻接口 |
| `newsroom/public_site.py` | 公网输出 | 临时数据库整理、快照、网页模板、报告导出 |
| `newsroom/ecs_site.py` | ECS 发布 | 读取上次快照、临时文件写入、原子替换 |
| `newsroom/deepseek.py` | 可选手动 API | 单条标题发送给第三方；不属于本地模型训练 |
| `web/index.html` | 本机网页 | 输入、新闻、批量、历史、实验和原理各区块 |
| `web/public/index.html` | 公网网页 | 阅读与实验报告，下载完整版 |
| `web/app.js` | 本机页面动作 | 收集输入、请求 API、显示预测和历史 |
| `web/live-news.js` | 新闻页面动作 | 筛选、详情、收藏、人工核验和轮询 |
| `web/live-news-ui.js` | 新闻视图 | 转义、时间显示、条目与状态标记 |
| `web/public-backend.js` | 公网浏览器适配 | 读取 JSON、浏览器保存、筛选与导出 |
| `web/public-app.js` | 公网启动和报告 | 页面导航、读取报告、三模型报告下载 |
| `web/workspace.js` `ui-data.js` `improvements.js` `deepseek-ui.js` | 其他本机交互 | 分布统计、预览、结果是否过期、手动 API 展示 |
| `web/style.css` `polish.css` `newsflow.css` `public.css` | 样式 | 布局、间距、文字和响应式覆盖 |
| `scripts/prepare_data.py` | 恢复数据 | 固定上游版本与文件哈希校验 |
| `scripts/package.py` | 源码交付 | 包含程序、数据、模型、报告；排除密钥和个人缓存 |
| `deploy/ecs/` | 部署模板 | Nginx、新闻定时器、证书续期与资源限制 |
| `tests/` | 验证代码 | 数据边界、预测、存储、接口、发布和前端行为 |

其他脚本用于画图、版本对照、来源检查和旧材料生成，按实际职责查看文件开头与 `main`。`scripts/build_docs.py` 保留了早期版本的文本模板；不应覆盖当前整改后的论文和讲稿。

逐文件索引在 `docs/source-index.csv`，列出程序、脚本、网页和测试的文件说明，以及 Python 定义和行号。它帮助查找，不代替对每段函数的实际阅读。

## 从标题到分类

例如输入“中国队夺得比赛冠军”。`ModelService.predict` 先检查是否为空或超长，再用 `normalize` 统一文字。已有特征转换器调用 `transform`，只使用训练时的词表与 IDF，不能对每条新新闻重新 `fit`。

训练时 `build_features` 创建词 TF-IDF 和字词联合 TF-IDF。Jieba 分词给出词语，字符通道补充连续字符片段。稀疏向量中没有命中的特征为零；只保存非零位置和数值。

线性类别分数可写为 `w·x+b`。`x` 来自当前标题，`w` 和 `b` 从训练学出。LR 与 SVM 都有线性权重，但训练损失不同；NB 用类别条件概率统计。不能把“三个模型”理解成“两个非线性模型加一个线性模型”。

模型包 `artifacts/models.joblib` 是一个容器，含 `nb`、`lr`、`svm` 三套特征转换器、原始分类器和校准器。没有 YOLO 的 `best.pt`。默认模型由 `report.json` 的 `recommended_model` 指定为 `svm`，训练代码在最终测试前按 selection 宏 F1 设置它。

`predict_proba` 输出校准后概率，选择最高类，并检查阈值与前两类差值。没有命中特征时返回 unknown；命中特征也不能保证输入属于五类。`explain` 展示部分特征相对第二类别的原始权重贡献，不是新闻真实性判断。

## 从订阅到网页

`sources.json` 给出订阅链接；`fetch_feed` 读取，`parse_feed` 提取标题、链接、摘要和发布时间。`LiveNewsService._perform_refresh` 为来源分别提交任务，将每条标题前 200 字交给推荐本地模型，再由 `NewsStore.ingest` 合并与保存。

本机页面请求 Python 接口，公网页面读取 ECS 已发布的 JSON。ECS 用临时 SQLite 整理七天内条目，每轮完成后约两分钟再次检查；网页约二十秒检查已发布快照。公网检查更新不直接触发采集任务。

列表先呈现新闻标题、类别、来源和发布时间。正常结果的概率放在详情，待核对和人工类别仍保留。没有摘要时不填重复占位文字；需要阅读内容时打开发布方原文。这个布局是设计选择，没有用户实验测量效率提升。

## 演示与问答

先打开工程，再运行一个标题、查看模型报告、搜索一条实际新闻、核验并刷新。每次说清输入在哪里、哪个函数处理、输出在哪里、保存到哪个文件。遇到不懂的参数，回到当前调用和库的定义，不把算法名称当作解释。

个人实现与学习使用 AI 辅助和成熟库；对尚未掌握的数学推导如实说明。生成注释或讲稿不能代替本人理解代码。
