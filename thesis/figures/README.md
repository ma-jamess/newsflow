# 论文与答辩配图

三幅图由本项目 `scripts/make_figures.py` 从 `artifacts/report.json` 生成。来源是已完成的独立实验，不使用参考版图片，不重新训练。

- `模型指标对比.png`：三种算法的测试准确率与宏 F1，以百分比展示。纵轴从90%起，比较细小差异时应同时引用图上数值，避免把柱高差当成倍数差。
- `测试混淆矩阵.png`：推荐字词联合线性 SVM 的4,989条测试结果。行为真实类别，列为预测类别，单元格为标题数量，对角线为正确分类。
- `系统架构.png`：网页、Python HTTP服务、模型服务与数据存储的模块关系。它是结构说明，不是性能测量。

在项目根目录复现：

```powershell
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python scripts/make_figures.py
```

图中文字使用 Windows 微软雅黑或黑体。输出200 DPI PNG，可插入论文或答辩幻灯片；图注应说明数据集与实验边界。现有 DOCX 仍是技术初稿，新增配图作为独立附件提供。
