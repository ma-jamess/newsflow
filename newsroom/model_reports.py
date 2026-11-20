"""Readable reports from the recorded experiment, with no fitting or inference."""

MODELS = {'nb': '朴素贝叶斯', 'lr': '逻辑回归', 'svm': '线性 SVM'}


def _cell(value):
    return str(value).replace('|', '／').replace('\n', ' ').replace('\r', ' ')


def model_report(report, kind):
    if kind not in MODELS:
        raise ValueError('不支持的模型')
    model = report['models'][kind]
    counts = report['split_counts']
    test = model['test']
    classes = report['categories']
    correct = sum(test['confusion_matrix'][i][i] for i in range(len(classes)))
    total = sum(sum(row) for row in test['confusion_matrix'])
    if total != counts['test'] or abs(correct / total - test['accuracy']) > 1e-8:
        raise ValueError('测试数量与指标不一致')
    feature = '词 TF-IDF' if model['feature_kind'] == 'word' else '词与字符联合 TF-IDF'
    parameter = 'alpha' if kind == 'nb' else 'C'
    selected = report['recommended_model'] == kind
    lines = [f'# {MODELS[kind]}验证报告', '',
             f"本报告来自已有实验记录。训练记录时间为 {report['created_at']}。下载或生成报告不会重新训练。",
             '', '## 实验与模型', '',
             f'- 方案：{feature} + {MODELS[kind]} + sigmoid 概率校准。',
             f'- 参数：{parameter}={model["parameter"]}；实际特征维度 {model["feature_count"]:,}。',
             f'- 训练 {counts["train"]:,} 条；开发 {counts["dev"]:,} 条；测试 {counts["test"]:,} 条。',
             f'- 开发集分为选参 {report["development_split"]["selection_count"]:,} 条和校准 {report["development_split"]["calibration_count"]:,} 条。',
             '- 词表与 IDF 只用训练集拟合；算法与参数按选参集确定；校准只使用校准集。',
             f'- 本方案{"是" if selected else "不是"}默认推荐；推荐记录为 `{report["recommended_model"]}`，依据独立选参集宏 F1。',
             '- 使用 scikit-learn 的 CPU 算法；不是 YOLO、BERT 或 DeepSeek 的训练实验。',
             '', '## 候选参数与选择依据', '',
             '| 参数 | 选参集宏 F1 | 本次记录的拟合秒数 |', '| --- | ---: | ---: |']
    for row in report['candidates']:
        if row['model'] == kind:
            lines.append(f'| {row["parameter"]} | {row["selection_macro_f1"]:.8f} | {row["fit_seconds"]:.3f} |')
    lines.extend(['', '耗时来自原实验机器，不能保证其他机器相同。最高分只是本次候选中的选择，没有证明参数普遍最优。',
                  '', '## 独立测试结果', '',
                  '| 指标 | 校准后的结果 |', '| --- | ---: |',
                  f'| 正确数 / 测试总数 | {correct:,} / {total:,} |',
                  f'| 错误数 | {total - correct:,} |',
                  f'| 准确率 | {test["accuracy"] * 100:.4f}% |',
                  f'| 宏 F1 | {test["macro_f1"]:.6f} |',
                  f'| ECE | {test["ece"]:.6f} |',
                  f'| 多类 Brier | {test["brier"]:.6f} |',
                  f'| 校准前准确率 | {model["before_calibration"]["accuracy"] * 100:.4f}% |',
                  '', '准确率为正确数除以总数。宏 F1 是各类 F1 的等权平均。ECE 衡量分组置信度与实际正确比例的偏差；Brier 使用各类概率平方误差求和后对样本平均。校准不保证提高准确率。',
                  '', '## 分类别结果', '',
                  '| 类别 | 精确率 | 召回率 | F1 | 样本数 |', '| --- | ---: | ---: | ---: | ---: |'])
    for label in classes:
        row = test['per_class'][label]
        lines.append(f'| {label} | {row["precision"]:.6f} | {row["recall"]:.6f} | {row["f1-score"]:.6f} | {int(row["support"])} |')
    lines.extend(['', '## 混淆矩阵', '', '行是真实类别，列是预测类别。', '',
                  '| 真实类别 / 预测类别 | ' + ' | '.join(classes) + ' |',
                  '| --- | ' + ' | '.join(['---:'] * len(classes)) + ' |'])
    for label, values in zip(classes, test['confusion_matrix']):
        lines.append('| ' + label + ' | ' + ' | '.join(str(n) for n in values) + ' |')
    lines.extend(['', '## 错误样本示例', '',
                  '| 标题 | 数据集标签 | 模型预测 | 最高校准概率 |', '| --- | --- | --- | ---: |'])
    for row in model.get('errors', [])[:8]:
        lines.append(f'| {_cell(row["title"])} | {_cell(row["label"])} | {_cell(row["prediction"])} | {row["score"]:.6f} |')
    lines.extend(['', f'全部测试预测保存在 `artifacts/{kind}_test_predictions.csv`；示例不是新增评测。',
                  '', '## 方案比较与局限', '',
                  'NB 使用词特征，LR 和 SVM 使用字词联合特征，这是三套完整方案的对比，不是只改变分类器的严格消融。LR 和 SVM 都学习线性判别函数，NB 是基于条件概率的生成式方案。',
                  '这份实验只说明固定历史标题测试集上的表现。实时订阅、五类之外的内容、正文分类和长期分布变化未由这些指标验证；高概率仍可能错分。没有统计显著性检验，也没有独立证明字符通道或 0.7 权重的单独收益。',
                  '', '## 可追溯文件', '',
                  '- 数据与标签：`data/raw/manifest.json`、`data/raw/class.txt`、`newsroom/data.py`。',
                  '- 特征、分类器、选参、校准与测试：`newsroom/ml.py`。',
                  '- 训练入口：`scripts/train.py`；已有模型测试复核：`scripts/verify_models.py`。',
                  '- 完整实验：`artifacts/report.json`。模型包：`artifacts/models.joblib`，包含三套转换器、原始分类器和校准器。',
                  f'- 模型包 SHA-256：`{report["model_sha256"]}`。', ''])
    return '\n'.join(lines)
