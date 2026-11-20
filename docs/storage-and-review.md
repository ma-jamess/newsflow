# 新闻数据保存与人工核验

本机实验程序和公网阅读版使用不同的保存方式。分类完成、网页关闭、重新打开之间的数据关系必须按所用版本说明。

| 数据 | 本机完整版 | ECS 公网阅读版 |
| --- | --- | --- |
| 原始训练标题与标签 | `data/raw/train.txt` `dev.txt` `test.txt` `class.txt` | 不提供给浏览器预测，随完整项目下载 |
| 三模型与报告 | `artifacts/models.joblib` `report.json` | 服务器模型在 `/opt/newsflow/artifacts`；浏览器只读取报告 JSON |
| 自动采集新闻 | `runtime/news.sqlite3` | 生成快照时用临时 SQLite，发布 `/var/lib/newsflow/site/data/news.json` |
| 单条手动预测历史 | `runtime/history.sqlite3` 的 history 表 | 公网版不提供此功能 |
| 新闻收藏 | SQLite `news_articles.saved` | 此浏览器 localStorage 的 `newsflow.public.v1.bookmarks` |
| 新闻人工类别 | SQLite `news_articles.correction` | 此浏览器 localStorage 的 `newsflow.public.v1.corrections` |
| 来源显示偏好 | 数据库来源启停 | 此浏览器 localStorage 的 `newsflow.public.v1.sources` |
| 断网阅读缓存 | 新闻数据库 | 经过校验的 `newsflow.public.v1.snapshot` |

## 文章表如何保存

`NewsStore.ingest` 对规范化链接计算稳定 ID，保存标题、摘要、发布时间、来源、收录时间和模型结果。模型结果序列化为 JSON，存在数据库 result 字段，不能把网页上看到的内容当成唯一数据来源。

同一 ID 更新标题与预测，但不覆盖原来的 saved 和 correction 字段。训练标题去重使用另一套归一化 key；文章链接去重不等于事件语义聚类。

## 人工核验发生在哪里

点击新闻详情的类别选择与保存，`web/live-news.js` 提交 `news/feedback`。

本机版进入 `newsroom/server.py` 的 `/api/news/feedback`，调用 `NewsStore.feedback` 更新 correction；查询时显示类别优先使用人工类别，原始 result 保留。

公网版进入 `web/public-backend.js` 的浏览器请求适配。它校验类别，再写 localStorage；`decorate` 用人工类别覆盖当前展示，或者以“待核对”标记保留原预测。没有向 ECS 写入个人类别。

人工核验应先阅读标题、摘要和原文，根据任务的五类定义判断。只有地名或跨领域内容时，不能凭城市名称强行确定类别；可以标记“待核对”。标注操作不是自动在线学习，模型包不会随之修改。

## 重开页面会怎样

本机数据库留在运行目录，正常刷新或服务重启仍可读取。公网刷新会重新读取此浏览器的个人设置，新闻快照更新也会保留它们；清理站点数据会删除，换浏览器、设备或网站地址不会自动同步。匿名公网用户之间互不共享个人标注。

本机批量预测默认不自动写单条历史，需要导出保留该批结果。公网可导出当前筛选的新闻。原实验 CSV 与实际新闻个人标注是不同数据，不将纠错直接混入旧测试集。
