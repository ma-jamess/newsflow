"""根据真实实验生成论文初稿、对比说明和答辩讲稿。需 python-docx。"""
import csv
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def percent(value):
    return f'{value * 100:.4f}%'


def main(comparison_only=False):
    report = json.loads((ROOT / 'artifacts' / 'report.json').read_text(encoding='utf-8'))
    reference = json.loads((ROOT / 'docs' / 'reference-report.json').read_text(encoding='utf-8-sig'))
    best = report['models'][report['recommended_model']]
    old = reference['models']['lr']['test']
    accuracy_delta = (best['test']['accuracy'] - old['accuracy']) * 100
    errors_old = round((1 - old['accuracy']) * report['split_counts']['test'])
    errors_new = round((1 - best['test']['accuracy']) * report['split_counts']['test'])
    comparison = f'''# 两版中文新闻标题分类系统比较

本报告比较用户提供的参考成品和本次独立实现。它说明可验证的系统差异，不用于评判模型提供商的整体能力。参考路径只用于本次读取，运行新版不依赖它。

## 同一测试集的实测比较

两版4,989条测试标题与真实标签逐条、同顺序一致。验证记录在 docs/verification.json。清洗后训练89,887条、验证4,986条、测试4,989条，去除重复138条，跨划分重复为0。

| 项目 | 参考版本 | Codex 版本 |
| --- | --- | --- |
| 最佳模型 | 词 TF-IDF 逻辑回归 C=4 | 字词联合 LinearSVC C=1 加 Sigmoid 校准 |
| 测试准确率 | {percent(old['accuracy'])} | {percent(best['test']['accuracy'])} |
| 测试宏 F1 | {old['macro_f1']:.6f} | {best['test']['macro_f1']:.6f} |
| 错误数 | {errors_old} / 4989 | {errors_new} / 4989 |
| 校准 ECE | 未记录 | {best['test']['ece']:.6f} |
| 多类 Brier | 未记录 | {best['test']['brier']:.6f} |

准确率提高{accuracy_delta:.4f}个百分点，错误减少{errors_old-errors_new}条。参考版本未记录校准质量，因此不能宣称新版 ECE 相比原版具体降低多少。SVM 校准前准确率为{percent(best['before_calibration']['accuracy'])}，校准后为{percent(best['test']['accuracy'])}；校准略改变分类结果，不等于准确率必然提升。

## 设计差异

| 维度 | 参考版本源码观察 | 新版实现 |
| --- | --- | --- |
| 启动 | python run.py，Streamlit，默认8502 | python run.py，标准库 HTTP，默认8510，Edge |
| 算法 | 朴素贝叶斯、逻辑回归 | 朴素贝叶斯、字词联合逻辑回归、字词联合 SVM |
| 特征 | jieba 词与词二元组 | 词与词二元组，加2至4字的字符片段 |
| 数据边界 | 训练拟合、整份dev选参、test评估 | 训练拟合、dev分层一半选参一半校准、test评估 |
| 分类说明 | 分词和五类分数 | 分词、校准概率、实际特征权重贡献 |
| 核对提醒 | 固定0.55 | 可调整阈值，类别分数接近时也提示 |
| 批量 | CSV 上传与导出 | CSV / 多行粘贴，搜索、分页、状态筛选，真实标签评估 |
| 历史纠错 | 所读源码无持久化模块 | 独立 SQLite、人工标注、导出 |
| 实验记录 | 准确率、F1、混淆矩阵、错误 | 以上，加校准前后、ECE、Brier、固定阈值覆盖率 |
| 本地接口 | Streamlit 页面 | 同源 JSON 接口、Host 与请求令牌校验 |

两版均保留了去重、校验和安全 CSV 导出等正确做法。新版增加的功能不代表原版存在相应错误。

## 比较的适用范围

这是同数据、同测试集的完整系统比较。训练特征、验证集用法、算法和校准同时改变，没有对每项增量做独立消融。因此结果不能单独证明字特征、SVM 或校准各贡献了多少，也不是大语言模型能力的全面竞赛。

语料年代较早，测试结果不能代表2026年的所有中文新闻。标签中有跨领域和疑似噪声样本，高概率错分仍然存在。正式部署需要新的独立标注集和类别范围扩展。

## 原版保存

只复制公开数据与参考实验 JSON，应用代码和模型重新实现、重新训练。提供的成品目录所有文件均记录 SHA-256，最终复核必须一致。比较报告、验证记录、模型和数据全部放在新项目，原版未被运行或编辑。
'''
    paired_path = ROOT / 'docs' / 'paired-comparison.json'
    if paired_path.exists():
        paired = json.loads(paired_path.read_text(encoding='utf-8'))
        counts = paired['counts']
        comparison += f'''
## 逐条对照与取长补短（1.1）

就这两份成品而言，Codex 版在本测试集分类效果、解释、校准与历史纠错上更完整；DeepSeek 版源码更紧凑，上传前预览、完整错误下载和论文配图更便于演示。选择用于毕设展示的成品时，Codex 1.1 功能更丰富；理解和维护代码时，参考版的简洁结构也值得借鉴。

| 同一条标题的结果 | 条数 |
| --- | ---: |
| 两版都正确 | {counts['both_correct']} |
| Codex 正确、DeepSeek 错误 | {counts['new_correct_old_wrong']} |
| DeepSeek 正确、Codex 错误 | {counts['old_correct_new_wrong']} |
| 两版都错误 | {counts['both_wrong']} |

逐条净减少 {counts['new_correct_old_wrong']-counts['old_correct_new_wrong']} 条错误，并非所有标题都改善。完整差异在 `docs/逐条差异.csv`，输入预测文件的 SHA-256 与各类别召回率在 `docs/paired-comparison.json`。两版逐条准确率差为 {paired['accuracy_delta_percentage_points']:.6f} 个百分点；旧 JSON 指标有小数截断，正文四位百分比展示不受影响。

1.1 已借鉴并补齐：分类前预览前10条、总数和无效数；下载所选算法全部误分类；同一标题三算法对照；显示已提交标题，输入、算法或阈值变更时提醒更新结果；从实际报告独立生成指标图、混淆矩阵与系统架构图。

三算法对照不写历史、不投票替换默认模型；人工纠错不自动训练。此次没有修改模型权重、特征、参数、校准器或数据划分，没有用这79条差异样本继续调参，准确率仍沿用同一次独立实验。1.0 源码包保留，1.1 完整包包含新增源码、配图和验证记录。

配图在 `thesis/figures/`，均由 `scripts/make_figures.py` 使用本项目报告生成，未复制参考版图片。生成方式、图轴与使用说明见该目录 README。图和中文对比报告可直接供论文补充使用；已有 DOCX 保留为技术初稿。
'''
    (ROOT / 'docs' / '版本对比.md').write_text(comparison, encoding='utf-8')
    if comparison_only:
        print('已更新版本对比；论文初稿保持原文件')
        return

    chapters = [
('摘要', [
f'本课题设计并实现一个在个人计算机上运行的中文新闻标题分类系统，面向体育、科技、教育、财经、娱乐五类新闻。系统将标题转化为 TF-IDF 特征，分别训练朴素贝叶斯、逻辑回归和线性支持向量机，提供单条分类、批量处理、效果评估、特征解释和人工纠错功能。开发目标是把模型训练与应用操作连成可复现的流程，并将判断依据和适用边界呈现给使用者。',
f'实验使用固定版本的公开 THUCNews 标题子集，清洗后训练集89,887条，验证集4,986条，测试集4,989条。验证集进一步分为2,493条选参样本和2,493条校准样本。特征只在训练集拟合，模型参数和推荐算法依据选参集确定，校准器使用独立校准样本，最后在测试集评估。推荐字词联合线性 SVM 的校准后测试准确率为{percent(best["test"]["accuracy"])}，宏平均 F1 为{best["test"]["macro_f1"]:.6f}。',
'应用采用 Python 标准库 HTTP 服务、原生网页和 SQLite 数据库，使用 python run.py 启动，默认在 Edge 中打开。所有推断在本机完成，不依赖外部生成式人工智能服务。系统采用输入校验、同源请求校验、模型哈希校验及安全 CSV 导出，便于在毕业设计演示中使用。',
'实验结果表明，该方案可以对给定语料中的五类标题进行有效分类。语料较早、标签噪声和类别范围有限仍是主要约束。本文结论描述该数据集上的实现与结果，不将应用集成工作表述为新的分类算法。',
'关键词：中文新闻标题；文本分类；TF-IDF；线性支持向量机；概率校准；模型解释',
'Abstract',
f'This project implements a local Chinese news headline classifier for sports, technology, education, finance and entertainment. Word and character TF-IDF features are evaluated with Naive Bayes, logistic regression and a linear support vector machine. Parameter selection and probability calibration use disjoint development subsets. On an independent test set of 4,989 headlines, the recommended calibrated linear SVM achieves {percent(best["test"]["accuracy"])} accuracy and {best["test"]["macro_f1"]:.6f} macro F1. A Python HTTP service, browser interface and SQLite database support prediction, batch export, evaluation, feature explanations and human corrections. The conclusions are limited to the historical five-category dataset.']),
('第一章 绪论', [
'新闻标题通常只有几十个字，却承担了内容概括和栏目归属的作用。人工整理标题需要不断识别主题，面对成批数据时容易遗漏或出现标准不一致。自动分类可以在整理新闻、教学实验和信息检索中提供初步归类结果，但标题信息有限，系统应同时提供核对入口，不能把模型输出当作最终事实。',
'本课题的研究对象是中文新闻标题，输入为一段短文本，输出为预先定义的五类标签之一。课题不包含新闻真实性检测、全文摘要或开放领域多标签识别。选择五类新闻是为了控制标注和实现范围，使数据准备、特征处理、算法对比和界面演示能在普通计算机上完成。',
'中文标题分类有三个具体困难。第一，中文缺少天然词边界，分词可能受到新词、人名和机构名影响。第二，标题没有正文语境，例如体育明星参加综艺节目时，体育和娱乐主题容易交叉。第三，用户看到一个高分值时容易理解为必然正确，而未校准分数可能与真实正确率存在偏差。',
'因此系统采用词特征与字符片段联合表示，并增加独立概率校准。词语保留相对完整的主题概念，字符片段补充分词失败时的信息。界面展示实际特征贡献与类别概率，并对低分和相近类别给出人工核对提示。人工核对结果另行保存，使演示过程中的更正有记录可查。',
'本课题的贡献主要是应用设计和实验规范：将公开数据清洗、参数选择、校准、独立测试与本地界面组织成完整项目；保留源数据版本、校验值和实验明细；提供可运行源码和一键入口。TF-IDF、朴素贝叶斯、逻辑回归、SVM 和 Sigmoid 校准均为已有方法，本文不声称提出新的分类算法。',
'论文按照背景、技术、需求、数据、模型、实现、验证和总结展开。所有定量结果来自本项目训练脚本生成的报告；文中不存在预设准确率或通过挑选测试集结果更改推荐模型的过程。']),
('第二章 相关技术与总体需求', [
'TF-IDF 将文本映射为稀疏向量。词频反映特征在标题内的出现情况，逆文档频率降低训练语料中普遍出现词语的权重。本系统采用 sublinear_tf 处理重复出现的特征，词表示包含一元和二元词组。词表与 IDF 必须在训练集上拟合，不能先对全部数据拟合后划分，否则验证和测试文本的信息会进入训练过程。',
'朴素贝叶斯估计类别与特征条件分布，训练速度快，适合作为文本分类基准。逻辑回归学习线性类别得分并输出概率。线性 SVM 根据分类间隔优化权重，对高维稀疏文本特征适用，但原始 decision_function 不是概率，需要额外校准才能给出可比较的概率分布。',
'本系统通过 CalibratedClassifierCV 和 FrozenEstimator 固定已训练的基础分类器，再在独立校准集上拟合 Sigmoid 参数。校准的目标是让模型分数更接近实际正确率。校准可能改变部分类别的排序和预测，不保证准确率提升，因此报告同时记录校准前后指标。',
'应用需求包括五个页面。标题分类页需要输入、选择算法、显示类别和概率；批量处理页需要上传 CSV 或粘贴多行，逐行保留状态并导出；实验页展示数据规模和指标；历史页保存单条分类和人工标注；原理页说明处理路径和局限。界面不要求用户了解服务端实现细节才能完成分类。',
'非功能需求包括本机运行、无需 GPU、启动简便、实验可复现、错误可定位和原版项目独立。入口采用标准库检查依赖并使用项目虚拟环境，默认端口8510，区别于参考版本8502。HTTP 服务只监听127.0.0.1，模型与历史文件保存在新项目目录。',
'系统允许200字以内标题，每批最多5000条，CSV 文件最多5 MB。支持 UTF-8 和 GB18030 两种常见中文编码。无效标题不强行赋予标签，结果中保留错误原因；没有任何已学特征的标题返回未识别状态。标题属于五类之外时，模型仍可能输出五类中最接近的一类，这是需明确说明的边界。']),
('第三章 数据准备与实验划分', [
'公开数据取自 Chinese-Text-Classification-Pytorch 仓库的 THUCNews/data 子集。项目固定提交6cb26819af7b646275aff8a4693676f2849e67f6，保存 class、train、dev、test 文件、上游说明与许可证。manifest.json 记录各文件 URL、字节数和 SHA-256，恢复数据时与预期哈希比较，防止使用不同文件后继续沿用旧实验记录。',
'数据准备先根据 class.txt 将上游标签索引映射为中文五类，只保留所选类别。归一化包括 HTML 实体解码、去除标签、Unicode NFKC、英文小写和空白合并。去重键进一步忽略标点，从而识别只在标点上变化的相同标题。无有效字符、空标题或超长标题被剔除。',
'标签冲突需要在去重前处理。如果同一个归一化标题对应不同标签，该标题相关记录全部剔除，避免任意选择一个标签。没有冲突时，按训练、验证、测试顺序保留一份标题。这一规则与参考系统一致，便于做同测试集的系统比较。去重只解决完全相同或标点差异标题，近义改写和同一事件的不同标题仍可能出现在多个划分中。',
f'本次清洗后训练集{report["split_counts"]["train"]:,}条，验证集{report["split_counts"]["dev"]:,}条，测试集{report["split_counts"]["test"]:,}条。清洗记录显示重复移除{report["data_audit"]["duplicate_rows_removed"]}条，冲突移除{report["data_audit"]["conflicting_rows_removed"]}条，跨划分重复为0。各类别实际数量记录在 report.json 的 data_audit.class_counts 中。',
'验证集按五类标签分层，使用 random_state=42 分为选参和校准两部分，各2,493条。选参部分用于比较候选参数和选择推荐算法；校准部分仅用于拟合概率转换参数。代码记录双方索引，测试断言二者不相交。没有把校准样本加入基础分类器训练，也没有用测试指标确定算法。',
'本实验保留原始 train/dev/test 划分，不重新随机切分全量语料。最终测试集4,989条与参考成品测试预测文件中的标题、标签和顺序完全一致。不同划分或新语料上的表现尚未评估，因此这个比较只支持当前数据上的结论。']),
('第四章 特征建模与分类实验', [
'词特征使用 jieba.lcut，设置 HMM=False 以保持分词行为固定，过滤不含文字或数字的纯符号词元。词 TF-IDF 使用一元与二元组，min_df=2，最多40,000个特征。该表示用于朴素贝叶斯，也构成联合特征的一部分。',
'字符表示直接对归一化文本提取长度2至4的片段，min_df=3，最多70,000个特征。FeatureUnion 拼接词和字符向量，词权重1.0，字符权重0.7。字符片段能够在未知组合词和分词粒度不合适时保留部分信息，但也增加词表和模型体积。该权重和范围为本次预先实现的工程选择，没有依据测试集搜索。',
'候选参数为朴素贝叶斯 alpha取0.1、0.5、1.0；逻辑回归 C取1.0、4.0；线性 SVM C取0.5、1.0、2.0。每种算法先在训练特征上拟合，在验证选参集上计算宏 F1，保留得分最高参数；平分时保留先出现的候选。推荐算法也依据同一选参指标确定。',
'基础模型固定后，在验证校准集上拟合 Sigmoid 校准器。本实验使用每类的校准概率再归一化为五类分布。模型服务使用校准后最大概率对应的类别进行预测，并同时保留未经校准的分类器权重用于解释。',
'评估包含准确率、宏平均 F1、每类精确率和召回率、混淆矩阵、多类 Brier 分数和10个区间的 ECE。Brier 为每个样本各类别概率与独热标签的平方差之和再取均值；ECE 按最大概率分箱，计算平均概率与实际正确率偏差的加权和。本报告的 Brier 是多类总和定义，不能与采用类别平均定义的其他报告直接比数值。',
'解释使用当前标题的稀疏 TF-IDF 特征值乘以预测类别和第二候选类别的权重差。朴素贝叶斯使用特征对数概率差，逻辑回归和 SVM 使用线性系数差。页面展示贡献最大的正向词和字符片段。该方法回答原始类别得分受到哪些特征影响；不声称展示校准概率的增量，也不把类别固定关键词冒充当前输入的模型解释。']),
('第五章 系统设计与实现', [
'系统分为界面、服务、模型和持久化四部分。web/index.html、style.css 和 app.js 构成网页；newsroom/server.py 提供固定静态文件及 JSON 接口；ml.py 管理模型与解释；store.py 保存历史与纠错。数据清洗和 CSV 处理分别独立，便于在单条与批量预测中复用一致规则。',
'run.py 根据自身文件位置确定项目根目录，先选择项目虚拟环境，再检查依赖、源数据和模型。默认创建项目自己的 .venv，避免把依赖安装到其他项目的虚拟环境。模型报告保存训练环境与核心源码签名；版本或核心代码改变时重新训练。模型文件在 joblib.load 前比较 SHA-256，仅接受项目自己生成的文件，不提供模型上传接口。',
'接口包括健康检查、页面初始化、单条预测、批量预测、历史读取、人工标注和导出。单条预测校验标题后返回类别、概率、状态、分词、解释和记录编号。批量输入通过同一 ModelService.predict 完成，逐行显示无效或未识别状态。批量分类不自动保存为历史，避免一次上传大量记录淹没单条核对界面。',
'SQLite history 表记录时间、标题、预测、概率、状态、算法、人工更正和备注。所有 SQL 参数通过占位符绑定。每次数据库操作采用上下文管理，提交或回滚后关闭连接。人工更正必须属于五类，备注最多500字，记录不存在时返回明确错误。纠错记录不直接混入训练或测试数据。',
'本机服务限制 Host 为127.0.0.1和实际端口，浏览器 POST 要求同源并携带随机请求令牌。静态文件路径使用白名单，不能按用户路径读取任意文件。响应加入 CSP 和 nosniff，页面对用户标题、备注和错误样本转义后展示。CSV 导出对以等号、加号、减号或@开头的单元格加前导单引号，降低电子表格公式执行风险。',
'界面采用侧栏和工作区，桌面可并列显示输入与结果，小屏改为纵向布局。批量表提供搜索、状态筛选和每页25条分页。实验页可切换模型查看混淆矩阵与分类别指标。人工核对通过弹窗完成，历史页可以修改标注并导出最近5000条；数据库中更早的记录仍保留。']),
('第六章 测试结果与讨论', [
f'完整训练与最终评估耗时约{report["total_seconds"]:.1f}秒，模型包约{report["model_bytes"]/1024/1024:.1f} MB，测试环境 Python {report["environment"]["python"]}、scikit-learn {report["environment"]["scikit-learn"]}。耗时受到机器性能和依赖版本影响，不能作为其他机器的保证。',
'三种模型的校准后独立测试结果如下。推荐算法在最终测试前已经锁定，测试结果仅用于描述性能。',
f'朴素贝叶斯 alpha=0.1，准确率{percent(report["models"]["nb"]["test"]["accuracy"])}，宏 F1 {report["models"]["nb"]["test"]["macro_f1"]:.6f}；字词联合逻辑回归 C=4，准确率{percent(report["models"]["lr"]["test"]["accuracy"])}，宏 F1 {report["models"]["lr"]["test"]["macro_f1"]:.6f}；字词联合线性 SVM C=1，准确率{percent(best["test"]["accuracy"])}，宏 F1 {best["test"]["macro_f1"]:.6f}。',
f'推荐 SVM 的 ECE 为{best["test"]["ece"]:.6f}，多类 Brier 为{best["test"]["brier"]:.6f}。固定阈值0.65下，最大概率达标样本覆盖率为{percent(best["test"]["coverage_at_065"])}，覆盖样本准确率为{percent(best["test"]["accuracy_at_065"])}。这一覆盖统计只按概率阈值计算，不包含界面额外的前两类概率差条件，也不是五类之外的检测能力。',
f'与参考成品比较，参考逻辑回归准确率为{percent(old["accuracy"])}，新版为{percent(best["test"]["accuracy"])}，提高{accuracy_delta:.4f}个百分点；错误由{errors_old}条减少到{errors_new}条。同测试集比较能够说明整体方案在这批数据上改进，但没有消融实验，不能拆分字符特征、分类器和校准的单独贡献。',
'自动测试覆盖归一化、跨划分重复与冲突处理、CSV 编码和格式、行数上限、公式保护、模型哈希篡改、特征词表隔离、验证与校准索引隔离、单条批量一致、未知特征、SQLite 标注持久化、连接关闭、同源接口和项目环境选择。最终20项测试通过，开发环境中的 pytz 产生一项上游弃用警告，未导致测试失败。',
'浏览器验收在 Microsoft Edge 中完成单条科技示例、包含五类与空标题的多行批量输入、人工标注和实验页面。CSV 文件通过本地 HTTP 接口完成六行上传与导出验收，五条有效真实标签正确分类，一条空标题保留无效状态。浏览器自动选文件受扩展权限限制，未用自动浏览器上传来替代接口验证；应在使用者浏览器中手动选择文件再演示。',
'错误样本中存在跨主题和疑似噪声标签，例如被标成教育的名人相关标题可能被系统预测为娱乐。错误分析必须同时考虑标题信息不足和原始标签质量，不能直接把每次模型与标签不同都归因于算法缺陷。高概率错分仍存在，表明校准与核对入口都不能替代新的独立数据验证。']),
('第七章 总结与后续工作', [
'本课题完成了五类中文新闻标题的本地分类应用和独立训练流程。Python 一键入口、三种算法、字词联合特征、独立校准、线性解释、批量处理和人工纠错在同一项目中可运行，并提供全部源码、公开数据副本、训练报告和测试预测明细。',
f'独立测试中，推荐字词联合 SVM 的准确率达到{percent(best["test"]["accuracy"])}，宏 F1 为{best["test"]["macro_f1"]:.6f}。与同测试集参考版本相比，系统整体准确率提高{accuracy_delta:.4f}个百分点。该提升是本次数据与配置下的实测结果，不扩大为所有领域或全部时间范围的能力结论。',
'后续首先应建立新的独立新闻标题集，按当前新闻来源和时间采样，明确标注规则并进行多人复核。其次可以做消融比较，分别去除字符特征、校准或更换分类器，观察每项变化的影响。扩展类别时需要重新训练与校准，不能只在界面添加类别名称。',
'人工纠错可以作为后续标注工作的候选数据，但在再训练前需要去重、复核并分出新的验证和测试集。应冻结旧测试报告以保留历史比较，而不是吸收旧测试错误训练后继续把旧测试当作独立评价。',
'如需更强语义理解，可以在相同独立数据集上比较预训练中文编码模型。但额外模型的资源消耗、离线部署成本和复现性需要同时评估。对本毕业设计而言，传统稀疏特征模型已经能够在普通计算机上展示完整分类流程，适合解释代码、观察错误和讨论实验纪律。']),
('参考资料与复现说明', [
'[1] 649453932. Chinese-Text-Classification-Pytorch. 固定提交 6cb26819af7b646275aff8a4693676f2849e67f6。项目内 data/raw/README.md、LICENSE、manifest.json 保留本实验实际使用的来源与校验信息。',
'[2] Salton G, Buckley C. Term-weighting approaches in automatic text retrieval. Information Processing and Management, 1988, 24(5): 513–523。',
'[3] Cortes C, Vapnik V. Support-vector networks. Machine Learning, 1995, 20: 273–297。',
'[4] Platt J C. Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods. Advances in Large Margin Classifiers, 1999。',
'[5] Pedregosa F, et al. Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 2011, 12: 2825–2830。',
'[6] scikit-learn 1.6.1，实验实际安装版本。TfidfVectorizer、FeatureUnion、LinearSVC、FrozenEstimator、CalibratedClassifierCV 的调用方式以随项目源码与该版本 API 为准。',
'本稿是基于实际项目生成的论文技术初稿，未套用学校排版模板，文献条目提交前仍需按学校引用规范逐项核对。没有填写指导教师、院系、学号或未经用户提供的个人信息。',
'复现命令：python run.py；强制重训：python run.py --retrain；运行测试：.venv/Scripts/python -m pytest -q。关键源码为 newsroom/ml.py、data.py、server.py，实验报告为 artifacts/report.json，完整测试预测在 artifacts/*_test_predictions.csv。'])]
    thesis = ROOT / 'thesis'
    thesis.mkdir(exist_ok=True)
    markdown = '# 基于机器学习的中文新闻标题分类系统设计与实现\n\n季金航\n\n论文技术初稿 根据本项目实测结果生成\n\n'
    markdown += '\n\n'.join('## ' + title + '\n\n' + '\n\n'.join(paragraphs) for title, paragraphs in chapters)
    (thesis / '论文初稿.md').write_text(markdown, encoding='utf-8')

    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(.8)
    section.left_margin = section.right_margin = Inches(.85)
    for name in ['Normal', 'Title', 'Heading 1', 'Heading 2']:
        style = doc.styles[name]
        style.font.name = 'Times New Roman'
        style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体' if name == 'Normal' else '黑体')
        style.font.color.rgb = RGBColor(0, 0, 0)
    doc.styles['Normal'].font.size = Pt(11)
    doc.styles['Normal'].paragraph_format.line_spacing = 1.5
    doc.styles['Normal'].paragraph_format.space_after = Pt(9)
    doc.styles['Normal'].paragraph_format.first_line_indent = Pt(22)
    doc.styles['Title'].font.size = Pt(23)
    for style_name in ['Title', 'Heading 1', 'Heading 2']:
        for border in list(doc.styles[style_name].element.xpath('./w:pPr/w:pBdr')):
            border.getparent().remove(border)
    doc.styles['Heading 1'].font.size = Pt(17)
    p = doc.add_paragraph('基于机器学习的中文新闻标题分类系统设计与实现', 'Title')
    for border in list(p._p.xpath('./w:pPr/w:pBdr')):
        border.getparent().remove(border)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(80)
    for text in ['季金航', '论文技术初稿', '根据独立项目源码与实测实验生成', '2026年10月']:
        p = doc.add_paragraph(text)
        p.paragraph_format.first_line_indent = Pt(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(16)
    p = doc.add_paragraph('五类中文新闻标题  三种机器学习算法\n完整源码  本地运行  可复现实验')
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(60)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for title, paragraphs in chapters:
        doc.add_page_break()
        doc.add_heading(title, level=1)
        for text in paragraphs:
            doc.add_paragraph(text)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run('季金航  中文新闻标题分类系统  ')
    run.font.size = Pt(9)
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    footer._p.append(field)
    doc.save(thesis / '毕业论文初稿_季金航_Codex.docx')
    speech = f'''# 答辩演示讲稿

## 约三分钟介绍

我的题目是《基于机器学习的中文新闻标题分类系统设计与实现》。系统对体育、科技、教育、财经、娱乐五类新闻标题进行分类，使用 Python 一键启动，在本机浏览器中操作。

我先使用固定版本的公开新闻标题数据，清洗空标题和异常格式，并在训练、验证、测试之间去重。特征词表只在训练集学习。为了避免校准与选参混在一起，把验证集按类别分成两半，一半选择参数和推荐算法，一半做概率校准。

模型包括词特征朴素贝叶斯、字词联合逻辑回归和字词联合线性 SVM。词特征保留新闻主题词，字符片段可以补充分词不理想时的信息。最终推荐 SVM，在4,989条独立测试标题上准确率{percent(best['test']['accuracy'])}、宏 F1 {best['test']['macro_f1']:.6f}。

应用能做单条分类、CSV和多行批量、实验评估、特征解释与人工纠错。解释来自当前标题的实际 TF-IDF 特征和类别系数差，不是简单罗列关键词。人工纠错保存在本项目 SQLite 中，不会自动修改训练模型。

这项工作的重点是完整实现与可复现实验，并没有提出新的算法。语料较早、类别只有五类，高分也可能错。未来应补充新新闻的独立标注集，再做特征和算法的消融比较。

## 现场演示顺序

1. 执行 python run.py，展示 Edge 打开的五个页面。
2. 点击科技示例，分类后说明五类概率和特征贡献。
3. 将核对阈值提高，说明分数只是倾向；点击人工核对保存类别。
4. 上传 examples/batch-demo.csv，或粘贴五类标题和一条空标题；查看逐行状态和导出。
5. 实验页展示训练89,887 / 选参2,493 / 校准2,493 / 测试4,989，切换混淆矩阵。
6. 历史页查看刚才标注，说明纠错不污染测试集。
7. 打开 newsroom/ml.py 的选参、校准、最终测试位置及 report.json，说明源码可复现。

## 常见问题

**为什么没有直接使用大模型？** 本项目选择可在普通计算机离线运行、容易解释和复现实验的方案；大模型不是必须条件。可在以后用同一独立数据集比较。

**为什么用字词联合？** 分词提供完整词语，字符片段补充分词粒度问题。当前整体结果改善，但没有消融实验，不能单独量化每一种特征的贡献。

**分数是准确率吗？** 单条分数是校准后的模型概率倾向；准确率是整批有真实标签数据上的统计。两者不能混为一谈。

**为什么需要单独校准集？** 分类器拟合和分数校准是不同阶段，校准器不能用最终测试集拟合。独立校准样本减少评估泄漏。

**如何避免数据泄漏？** 跨划分去重，词表只用训练集，选参只用dev_selection，校准只用dev_calibration，test最后评估；相关边界有自动测试。

**错误可能来自哪里？** 标题语境不足、跨主题、噪声标签、数据年代差异。系统提供人工核对，但不是开放领域分类器。

**怎么比较两版？** 两版4,989条测试标题和标签完全一致，新版较参考最佳记录准确率提升{accuracy_delta:.4f}个百分点。训练方案有区别，只能比较整体系统结果。
'''
    (thesis / '答辩讲稿.md').write_text(speech, encoding='utf-8')
    print('已生成：论文 Markdown / DOCX、答辩讲稿、版本对比')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='从真实实验生成文档')
    parser.add_argument('--comparison-only', action='store_true', help='只更新版本对比报告')
    main(comparison_only=parser.parse_args().comparison_only)
