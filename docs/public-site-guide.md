# NewsFlow 公网使用与部署

当前部署状态：GitHub 授权已完成，正在进行首次公网部署和验证。Pages 使用 Actions 发布并强制 HTTPS。

网址：**https://ma-jamess.github.io/newsflow/**。源码：**https://github.com/ma-jamess/newsflow**。

公网版由 GitHub Pages 提供 HTTPS 网页，关闭本机或 Python 窗口不影响网址。`127.0.0.1:8510` 是下载版的本机地址，只有程序运行时才能访问；它不能用作给别人分享的站点。

## 在线使用

按五个类别浏览新闻，组合搜索和来源筛选，打开详情查看原文、订阅摘要、模型概率与特征依据。可收藏、人工改类别和导出当前筛选 CSV。

收藏保存文章快照，旧文章从自动列表移除后仍可在收藏中查看。收藏、人工类别和来源显示开关只保存在当前浏览器；刷新页面和后续数据发布会保留。换设备或清理站点数据不会同步。浏览器禁止存储或空间不足时会明确提示保存失败。

“实验报告”展示固定历史测试集的 NB/LR/SVM 指标；不代表当前新闻准确率。任意标题分类、CSV 批量处理、重新训练和完整历史功能，在下载的 Python 项目中运行。可选付费提供方仅在下载版手动使用，公网新闻任务不读取任何个人密钥或数据库。

## 新闻更新与故障回退

工作流约每 5 分钟尝试抓取新闻，GitHub 的调度可能延后。页面每 20 秒检查已发布数据；手动检查不会让匿名读者运行后台任务。来源发布时间、采集完成时间和浏览器检查不是同一时间。

部分来源失败时，沿用上一公开快照中的新闻并更新其余来源。全部来源失败但有可用缓存时，页面标明来源失败和缓存；没有任何可用新闻则构建失败，GitHub Pages 保留上一成功部署。断网且浏览器已有快照时显示缓存；首次访问没有数据时可重试。

只有标题和短文本摘要，原文链接指向发布方。原发布方拥有新闻内容权利；固定数据和图标的上游许可证保留。

## 在自己的仓库部署

Fork 本项目或创建自己的公开仓库。在 Settings → Pages 选择 GitHub Actions。`.github/workflows/pages.yml` 支持 main 推送、手动运行和五分钟调度。工作流从 GitHub Pages 配置读取正确的站点子路径，构建器从 `GITHUB_REPOSITORY` 生成源码与下载链接。

工作流只安装固定的 `requirements.txt`，加载已有本地模型，使用临时 SQLite。构建只需要 contents/read 和 pages/read，部署仅 pages/write 与 id-token/write；第三方 Actions 固定到 commit SHA。免费方案不需要部署密钥、新闻 API 密钥或个人 Python 后台进程。

本地检查公开页面：

```powershell
.venv\Scripts\python scripts/build_public_site.py --repository 用户名/仓库名
.venv\Scripts\python -m http.server 8513 --bind 127.0.0.1 --directory site
```

初次工作流读取不到已发布 JSON 时，使用 `public_data/news-seed.json` 的干净公开快照作为后备；正常抓取仍会替换和更新数据。生成的 `site/` 不加入源码仓库；仓库不包含 runtime、个人收藏、密钥、环境、浏览器下载或 QA。
