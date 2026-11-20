# 新闻来源与抓取入口

下表与内置 sources.json 对照，含 43 个频道，不等于 43 家媒体。来源目录依据已有公开订阅和可用性检查整理，详细历史取舍在 docs/free-news-sources.md。

运行状态来自 2026-11-20T08:18:52.540095+00:00 的公开快照，只说明当时状态，不保证未来始终可读。

抓取入口为 newsroom/feeds.py 的 fetch_feed 和 parse_feed；更新调用在 newsroom/live_news.py 的 _perform_refresh。来源频道不直接决定分类答案。

| 序号 | 名称 | RSS 或 Atom 链接 | 内容范围 | 当时状态 |
| ---: | --- | --- | --- | --- |
| 1 | IT之家 | https://www.ithome.com/rss/ | 科技与数码 | 有近期新闻 |
| 2 | 少数派 | https://sspai.com/feed | 数字生活与文化 | 有近期新闻 |
| 3 | 中新网 · 体育 | https://www.chinanews.com.cn/rss/sports.xml | 体育赛事 | 有近期新闻 |
| 4 | 中新网 · 财经 | https://www.chinanews.com.cn/rss/finance.xml | 财经与产业 | 有近期新闻 |
| 5 | 中新网 · 教育 | https://www.chinanews.com.cn/rss/edu.xml | 学校与教育 | 有近期新闻 |
| 6 | 中新网 · 即时 | https://www.chinanews.com.cn/rss/scroll-news.xml | 综合资讯，五类外内容需核对 | 有近期新闻 |
| 7 | 中新网 · 国内 | https://www.chinanews.com.cn/rss/china.xml | 综合 · 免费公开订阅 | 有近期新闻 |
| 8 | 中新网 · 国际 | https://www.chinanews.com.cn/rss/world.xml | 国际中文 · 免费公开订阅 | 有近期新闻 |
| 9 | 中新网 · 社会 | https://www.chinanews.com.cn/rss/society.xml | 综合 · 免费公开订阅 | 有近期新闻 |
| 10 | 中新网 · 健康 | https://www.chinanews.com.cn/rss/health.xml | 健康 · 免费公开订阅 | 有近期新闻 |
| 11 | 爱范儿 | https://www.ifanr.com/feed | 科技 · 免费公开订阅 | 有近期新闻 |
| 12 | 极客公园 | https://www.geekpark.net/rss | 科技 · 免费公开订阅 | 有近期新闻 |
| 13 | 36氪 | https://www.36kr.com/feed | 财经 · 免费公开订阅 | 时间未标注 |
| 14 | 钛媒体 | https://www.tmtpost.com/rss.xml | 财经 · 免费公开订阅 | 有近期新闻 |
| 15 | 雷峰网 | https://www.leiphone.com/feed | 科技 · 免费公开订阅 | 有近期新闻 |
| 16 | Solidot | https://www.solidot.org/index.rss | 科技 · 免费公开订阅 | 有近期新闻 |
| 17 | cnBeta | https://rss.cnbeta.com.tw/ | 科技 · 免费公开订阅 | 有近期新闻 |
| 18 | 小众软件 | https://www.appinn.com/feed | 科技 · 免费公开订阅 | 有近期新闻 |
| 19 | 异次元软件 | https://www.iplaysoft.com/feed | 科技 · 免费公开订阅 | 有近期新闻 |
| 20 | 阮一峰科技周刊 | https://www.ruanyifeng.com/blog/atom.xml | 科技 · 免费公开订阅 | 有近期新闻 |
| 21 | 机核 | https://www.gcores.com/rss | 娱乐 · 免费公开订阅 | 有近期新闻 |
| 22 | 游研社 | https://www.yystv.cn/rss/feed | 娱乐 · 免费公开订阅 | 有近期新闻 |
| 23 | 触乐 | https://www.chuapp.com/feed | 娱乐 · 免费公开订阅 | 有近期新闻 |
| 24 | 泛科学 | https://pansci.asia/feed | 科教 · 免费公开订阅 | 有近期新闻 |
| 25 | BBC中文简体 | https://feeds.bbci.co.uk/zhongwen/simp/rss.xml | 国际中文 · 免费公开订阅 | 读取失败 |
| 26 | 德国之声中文 | https://rss.dw.com/rdf/rss-chi-all | 国际中文 · 免费公开订阅 | 读取失败 |
| 27 | 法国国际广播中文 | https://www.rfi.fr/cn/rss | 国际中文 · 免费公开订阅 | 读取失败 |
| 28 | 韩联社中文 | https://cn.yna.co.kr/RSS/news.xml | 国际中文 · 免费公开订阅 | 读取失败 |
| 29 | 俄罗斯卫星通讯社中文 | https://sputniknews.cn/export/rss2/archive/index.xml | 国际中文 · 免费公开订阅 | 有近期新闻 |
| 30 | 公视新闻网 | https://news.pts.org.tw/xml/newsfeed.xml | 综合 · 免费公开订阅 | 读取失败 |
| 31 | 自由时报 · 即时 | https://news.ltn.com.tw/rss/all.xml | 综合 · 免费公开订阅 | 读取失败 |
| 32 | 中新网 · 文化 | https://www.chinanews.com.cn/rss/culture.xml | 文化 · 免费公开订阅 | 有近期新闻 |
| 33 | 联合国中文新闻 | https://news.un.org/feed/subscribe/zh/news/all/rss.xml | 国际中文 · 免费公开订阅 | 近期未更新 |
| 34 | Google新闻 · 综合 | https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans | 综合 · 免费公开订阅 | 读取失败 |
| 35 | Google新闻 · 国际 | https://news.google.com/rss/headlines/section/topic/WORLD?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans | 国际中文 · 免费公开订阅 | 读取失败 |
| 36 | Google新闻 · 国内 | https://news.google.com/rss/headlines/section/topic/NATION?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans | 国内 · 免费公开订阅 | 读取失败 |
| 37 | Google新闻 · 科技 | https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans | 科技 · 免费公开订阅 | 读取失败 |
| 38 | Google新闻 · 财经 | https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans | 财经 · 免费公开订阅 | 读取失败 |
| 39 | Google新闻 · 体育 | https://news.google.com/rss/headlines/section/topic/SPORTS?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans | 体育 · 免费公开订阅 | 读取失败 |
| 40 | Google新闻 · 娱乐 | https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans | 娱乐 · 免费公开订阅 | 读取失败 |
| 41 | Google新闻 · 科学 | https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans | 科学 · 免费公开订阅 | 读取失败 |
| 42 | Google新闻 · 健康 | https://news.google.com/rss/headlines/section/topic/HEALTH?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans | 健康 · 免费公开订阅 | 读取失败 |
| 43 | Google新闻 · 教育 | https://news.google.com/rss/search?q=%E6%95%99%E8%82%B2&hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans | 科教 · 免费公开订阅 | 读取失败 |

订阅内容及原文权利属于发布方。自定义来源须使用公开 HTTPS RSS/Atom；公网来源开关仅控制当前浏览器显示，完整本机版可添加订阅。
