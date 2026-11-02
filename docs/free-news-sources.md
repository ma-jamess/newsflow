# 免费新闻来源与可用性记录

2026-11-02 在 GitHub Actions 的实际采集网络检查了 91 个公开候选：43 个返回近期中文条目，3 个返回中文条目但未标注发布时间，45 个未通过读取或时效检查。这只是读取检查：随后复核确认新浪财经的无日期订阅实际是 2008 年存档，将其排除；再合并 cnBeta 的重复地址和 BBC 的简繁体重复频道。最终云端复查还排除了新华网的旧存档，并接入已恢复可读的联合国中文 RSS，仍为 43 个频道；这 43 个均通过最终检查。

按直接发布方合并后是 25 个发布方，另有 Google 中文新闻聚合；43 是订阅频道数，不是媒体家数。这份清单涵盖本轮检查可用的免费来源，后续可继续扩充。

最终复查：[检查 #41413021242](https://github.com/ma-jamess/newsflow/actions/runs/41413021242)，[最终 JSON 报告](source-audit-final-2026-11-02.json)，45 个候选可用，合并两组重复订阅后为 43 个。

初次云端执行记录：[来源检查 #41405334588](https://github.com/ma-jamess/newsflow/actions/runs/41405334588)。原始检查结果见 [JSON 报告](source-audit-2026-11-02.json)，候选输入见 [候选目录](free-source-candidates.json)。本机与云端网络可能不同，因此没有仅凭本机超时排除国际中文来源。

订阅候选参考了 GitHub 的 [awesome_rss_chinese](https://github.com/midmirror/awesome_rss_chinese)，实际启用以本次读取和时效校验为准。

## 已接入频道

| 频道／发布方 | 内容 | 订阅地址 | 检查结果 |
| --- | --- | --- | --- |
| IT之家 | 现有来源 | [RSS/Atom](https://www.ithome.com/rss/) | 近期中文条目 |
| 少数派 | 现有来源 | [RSS/Atom](https://sspai.com/feed) | 近期中文条目 |
| 中新网 · 体育 | 现有来源 | [RSS/Atom](https://www.chinanews.com.cn/rss/sports.xml) | 近期中文条目 |
| 中新网 · 财经 | 现有来源 | [RSS/Atom](https://www.chinanews.com.cn/rss/finance.xml) | 近期中文条目 |
| 中新网 · 教育 | 现有来源 | [RSS/Atom](https://www.chinanews.com.cn/rss/edu.xml) | 近期中文条目 |
| 中新网 · 即时 | 现有来源 | [RSS/Atom](https://www.chinanews.com.cn/rss/scroll-news.xml) | 近期中文条目 |
| 中新网 · 国内 | 综合 | [RSS/Atom](https://www.chinanews.com.cn/rss/china.xml) | 近期中文条目 |
| 中新网 · 国际 | 国际中文 | [RSS/Atom](https://www.chinanews.com.cn/rss/world.xml) | 近期中文条目 |
| 中新网 · 社会 | 综合 | [RSS/Atom](https://www.chinanews.com.cn/rss/society.xml) | 近期中文条目 |
| 中新网 · 健康 | 健康 | [RSS/Atom](https://www.chinanews.com.cn/rss/health.xml) | 近期中文条目 |
| 爱范儿 | 科技 | [RSS/Atom](https://www.ifanr.com/feed) | 近期中文条目 |
| 极客公园 | 科技 | [RSS/Atom](https://www.geekpark.net/rss) | 近期中文条目 |
| 36氪 | 财经 | [RSS/Atom](https://www.36kr.com/feed) | 时间未标注 |
| 钛媒体 | 财经 | [RSS/Atom](https://www.tmtpost.com/rss.xml) | 近期中文条目 |
| 雷峰网 | 科技 | [RSS/Atom](https://www.leiphone.com/feed) | 近期中文条目 |
| Solidot | 科技 | [RSS/Atom](https://www.solidot.org/index.rss) | 近期中文条目 |
| cnBeta | 科技 | [RSS/Atom](https://rss.cnbeta.com.tw/) | 近期中文条目 |
| 小众软件 | 科技 | [RSS/Atom](https://www.appinn.com/feed) | 近期中文条目 |
| 异次元软件 | 科技 | [RSS/Atom](https://www.iplaysoft.com/feed) | 近期中文条目 |
| 阮一峰科技周刊 | 科技 | [RSS/Atom](https://www.ruanyifeng.com/blog/atom.xml) | 近期中文条目 |
| 机核 | 娱乐 | [RSS/Atom](https://www.gcores.com/rss) | 近期中文条目 |
| 游研社 | 娱乐 | [RSS/Atom](https://www.yystv.cn/rss/feed) | 近期中文条目 |
| 触乐 | 娱乐 | [RSS/Atom](https://www.chuapp.com/feed) | 近期中文条目 |
| 泛科学 | 科教 | [RSS/Atom](https://pansci.asia/feed) | 近期中文条目 |
| BBC中文简体 | 国际中文 | [RSS/Atom](https://feeds.bbci.co.uk/zhongwen/simp/rss.xml) | 近期中文条目 |
| 德国之声中文 | 国际中文 | [RSS/Atom](https://rss.dw.com/rdf/rss-chi-all) | 近期中文条目 |
| 法国国际广播中文 | 国际中文 | [RSS/Atom](https://www.rfi.fr/cn/rss) | 近期中文条目 |
| 韩联社中文 | 国际中文 | [RSS/Atom](https://cn.yna.co.kr/RSS/news.xml) | 近期中文条目 |
| 俄罗斯卫星通讯社中文 | 国际中文 | [RSS/Atom](https://sputniknews.cn/export/rss2/archive/index.xml) | 近期中文条目 |
| 公视新闻网 | 综合 | [RSS/Atom](https://news.pts.org.tw/xml/newsfeed.xml) | 近期中文条目 |
| 自由时报 · 即时 | 综合 | [RSS/Atom](https://news.ltn.com.tw/rss/all.xml) | 近期中文条目 |
| 中新网 · 文化 | 文化 | [RSS/Atom](https://www.chinanews.com.cn/rss/culture.xml) | 近期中文条目 |
| 联合国中文新闻 | 国际中文 | [RSS/Atom](https://news.un.org/feed/subscribe/zh/news/all/rss.xml) | 近期中文条目 |
| Google新闻 · 综合 | 综合 | [RSS/Atom](https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans) | 近期中文条目 |
| Google新闻 · 国际 | 国际中文 | [RSS/Atom](https://news.google.com/rss/headlines/section/topic/WORLD?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans) | 近期中文条目 |
| Google新闻 · 国内 | 国内 | [RSS/Atom](https://news.google.com/rss/headlines/section/topic/NATION?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans) | 近期中文条目 |
| Google新闻 · 科技 | 科技 | [RSS/Atom](https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans) | 近期中文条目 |
| Google新闻 · 财经 | 财经 | [RSS/Atom](https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans) | 近期中文条目 |
| Google新闻 · 体育 | 体育 | [RSS/Atom](https://news.google.com/rss/headlines/section/topic/SPORTS?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans) | 近期中文条目 |
| Google新闻 · 娱乐 | 娱乐 | [RSS/Atom](https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans) | 近期中文条目 |
| Google新闻 · 科学 | 科学 | [RSS/Atom](https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans) | 近期中文条目 |
| Google新闻 · 健康 | 健康 | [RSS/Atom](https://news.google.com/rss/headlines/section/topic/HEALTH?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans) | 近期中文条目 |
| Google新闻 · 教育 | 科教 | [RSS/Atom](https://news.google.com/rss/search?q=%E6%95%99%E8%82%B2&hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans) | 近期中文条目 |

最终接入的来源中，36氪未提供可解析的文章发布时间。仍可读取，但页面显示“时间未标注”，不把抓取时间当成发布时间。阮一峰科技周刊按来源实际日期排序，较旧内容可能不在默认 72 小时视图内。

## 合并的重复订阅

- cnBeta 保留 `https://rss.cnbeta.com.tw/`，合并 `https://www.cnbeta.com.tw/backend.php`。
- BBC 默认使用简体中文 RSS，繁体地址在候选清单保留供需要者替换。

## 未接入候选

新浪财经的 `rollnews.xml` 返回 2008-06-12 存档；新华网的 `news_politics.xml` 在最终检查中返回 80 条路径含旧日期的无日期存档。两个订阅都已从内置目录排除。初始 JSON 报告中的 `unknown_time` 只说明当时没有解析到日期；最终选择见 [来源选择记录](source-selection-2026-11-02.json)。回归检查会排除无发布时间但原文路径含明确旧日期目录的文章，保持 `published_at` 为空。


这些地址是候选路径，当前未通过检查；失败不等于发布方没有新闻。没有使用需要登录、付费密钥或绕过访问限制的接口。

| 候选 | 检查结果 | 候选地址 |
| --- | --- | --- |
| 新浪财经 | 2008-06-12 存档，复核后排除 | [候选](https://rss.sina.com.cn/finance/rollnews.xml) |
| 新华网 | 80 条旧日期存档，最终复查后排除 | [候选](https://www.xinhuanet.com/politics/news_politics.xml) |
| 中新网 · 娱乐 | 没有有效条目 | [候选](https://www.chinanews.com.cn/rss/ent.xml) |
| 中新网 · 文化 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.chinanews.com.cn/rss/cul.xml) |
| 中新网 · 港澳 | 没有有效条目 | [候选](https://www.chinanews.com.cn/rss/gangao.xml) |
| 中新网 · 台湾 | 没有有效条目 | [候选](https://www.chinanews.com.cn/rss/taiwan.xml) |
| 中新网 · 华人 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.chinanews.com.cn/rss/huaren.xml) |
| 36氪 | 连接、容量或 RSS 格式检查失败 | [候选](https://36kr.com/feed) |
| 虎嗅 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.huxiu.com/rss/0.xml) |
| 品玩 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.pingwest.com/feed) |
| 快科技 | 连接、容量或 RSS 格式检查失败 | [候选](https://news.mydrivers.com/rss.aspx) |
| 超能网 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.expreview.com/rss) |
| 3DM游戏 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.3dmgame.com/rss/feed.xml) |
| 科学网新闻 | 连接、容量或 RSS 格式检查失败 | [候选](https://news.sciencenet.cn/xml/news-0.aspx) |
| 科学网新闻 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.sciencenet.cn/xml/news.aspx?di=0) |
| 果壳 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.guokr.com/rss/) |
| 科学公园 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.scipark.net/feed) |
| 新浪科技 | 没有七天内条目 | [候选](https://rss.sina.com.cn/tech/rollnews.xml) |
| 新浪教育 | 连接、容量或 RSS 格式检查失败 | [候选](https://rss.sina.com.cn/edu/rollnews.xml) |
| 新浪体育 | 连接、容量或 RSS 格式检查失败 | [候选](https://rss.sina.com.cn/sports/global.xml) |
| 新浪娱乐 | 连接、容量或 RSS 格式检查失败 | [候选](https://rss.sina.com.cn/ent/rollnews.xml) |
| NHK中文新闻 | 连接、容量或 RSS 格式检查失败 | [候选](https://www3.nhk.or.jp/nhkworld/zh/news/rss.xml) |
| 香港电台 · 本地 | 连接、容量或 RSS 格式检查失败 | [候选](https://rthk.hk/rthk/news/rss/c_expressnews_clocal.xml) |
| 香港电台 · 国际 | 连接、容量或 RSS 格式检查失败 | [候选](https://rthk.hk/rthk/news/rss/c_expressnews_cinternational.xml) |
| 香港电台 · 财经 | 连接、容量或 RSS 格式检查失败 | [候选](https://rthk.hk/rthk/news/rss/c_expressnews_cfinance.xml) |
| 香港电台 · 体育 | 连接、容量或 RSS 格式检查失败 | [候选](https://rthk.hk/rthk/news/rss/c_expressnews_csport.xml) |
| 中央社 · 即时 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.cna.com.tw/rss/aall.aspx) |
| 中央社 · 财经 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.cna.com.tw/rss/afe.aspx) |
| 中央社 · 体育 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.cna.com.tw/rss/aspt.aspx) |
| 中央社 · 文化 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.cna.com.tw/rss/acul.aspx) |
| 中華日報 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.cdns.com.tw/feed) |
| 中文维基新闻 | 连接、容量或 RSS 格式检查失败 | [候选](https://zh.wikinews.org/w/index.php?title=Special:NewsFeed&feed=rss) |
| SBS中文 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.sbs.com.au/language/chinese/zh-hans/rss) |
| 日经中文 | 连接、容量或 RSS 格式检查失败 | [候选](https://cn.nikkei.com/rss.xml) |
| 澎湃新闻 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.thepaper.cn/rss_news.xml) |
| 新华网 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.xinhuanet.com/rss/news.xml) |
| 人民网 | 没有七天内条目 | [候选](https://www.people.com.cn/rss/politics.xml) |
| 凤凰网 | 连接、容量或 RSS 格式检查失败 | [候选](https://news.ifeng.com/rss/index.xml) |
| 中国教育新闻网 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.jyb.cn/rss.xml) |
| 中新网 · 娱乐 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.chinanews.com.cn/rss/entertainment.xml) |
| 中新网 · 港澳 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.chinanews.com.cn/rss/ga.xml) |
| 中新网 · 台湾 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.chinanews.com.cn/rss/tw.xml) |
| 中新网 · 华人 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.chinanews.com.cn/rss/hr.xml) |
| 科学网 | 连接、容量或 RSS 格式检查失败 | [候选](https://news.sciencenet.cn/xml/news.aspx?di=0) |
| 香港电台 · 本地 | 连接、容量或 RSS 格式检查失败 | [候选](https://www.rthk.hk/rthk/news/rss/c_expressnews_clocal.xml) |
| NHK中文新闻 | 连接、容量或 RSS 格式检查失败 | [候选](https://www3.nhk.or.jp/nhkworld/zh/news/zh.xml) |

## 更新目录与复查

修改 `newsroom/sources.json` 可以维护内置来源。已有来源应保留 `id`，新来源使用新的唯一 ID；目录最多 128 项，必须是公开 HTTPS RSS/Atom，不含账号或 API 密钥。修改目录不会清除当前浏览器的收藏、纠错和来源显示偏好。

在 GitHub 仓库的 Actions 选择 **Check free news sources → Run workflow**，完成后下载 `free-source-audit` 报告。这个手动检查工作流只读取候选与上传报告，不会部署网页。网站更新继续由 **Publish NewsFlow** 的五分钟调度执行。

本地复查可运行：

```powershell
python scripts/check_news_sources.py --input docs/free-source-candidates.json --output source-audit.json
```

复查只在确有七天内的已标日期文章时标记 `current`；有日期但全部过旧的混合订阅不因其他条目缺日期而被标记为当前新闻。完全没有日期、且未发现存档证据的订阅标记 `unknown_time`，不会补写日期。

来源连接失败时保留已有新闻，其余来源继续更新。全站最多发布 1,000 条，先为每个来源保留最多十条近期文章，再按全站发布时间补齐；来源很多时按总容量减少每源保留数量。只读取标题、文本摘要和原文链接，新闻文字权利属于各发布方。
