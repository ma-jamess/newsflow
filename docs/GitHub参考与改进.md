# GitHub参考与1.2改进

2026年10月22日通过GitHub CLI搜索并读取以下仓库README与许可证。

| 项目 | 可借鉴内容 | 本次采用 |
| --- | --- | --- |
| [Tabler](https://github.com/tabler/tabler) | MIT，Bootstrap后台UI；导航、卡片、表单与表格 | 参考信息层次，自主编写CSS，未安装或复制其模板 |
| [Lucide](https://github.com/lucide-icons/lucide) | 一致的SVG线条图标，ISC及部分Feather衍生图标MIT条款 | 保存固定提交5个SVG，保留完整许可证 |
| [Label Studio](https://github.com/HumanSignal/label-studio) | Apache-2.0，文本标注、预测辅助与任务组织 | 借鉴人工核对流程，未引入其代码或服务 |
| [modAL](https://github.com/modAL-python/modAL) | MIT，scikit-learn主动学习与不确定样本查询 | 借鉴低概率优先核对，未安装或实现再训练闭环 |

1.2新增：批量五类分布、类别/状态/搜索交集筛选、整批待核对导出、批量独立阈值、历史未标注核对队列与低概率排序、Ctrl+Enter提交、结果复制、页内使用指南。

分布以有类别预测的标题为分母，包含需核对的预测，不包含无效与未识别行；全无效时为0。待核对导出包含review、unknown、invalid，不受页面过滤影响。已人工标注记录从未标注队列移出，低概率只代表核对线索。

界面统一深青导航、白色卡片、浅灰背景，增加中文文字对比与字号，统一按钮、表格与状态；小屏纵向布局，表格在容器内滚动，支持键盘焦点和减少动画。

Lucide固定提交20aef31db93fe4d9f398dbb15b120d99c48eef95，使用newspaper、layers、chart-column、clock、workflow；clock在本项目命名为history.svg。许可证和来源见third_party/lucide。页面无CDN、在线字体或新运行依赖。

模型、权重、特征、数据划分与96.93%历史测试准确率未变。大模型更换、实时抓取、标注后再训练需要独立评估与数据治理，留作后续扩展；当前人工标注仍只留档。
