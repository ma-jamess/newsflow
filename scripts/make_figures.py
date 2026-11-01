"""用已有真实报告生成可用于论文和答辩的配图。需 matplotlib。"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    report = json.loads((ROOT / 'artifacts' / 'report.json').read_text(encoding='utf-8'))
    target = ROOT / 'thesis' / 'figures'
    target.mkdir(exist_ok=True)
    plt.rcParams.update({'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'DejaVu Sans'], 'axes.unicode_minus': False,
                          'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
    models = list(report['models'].values())
    names = ['词特征朴素贝叶斯', '字词联合逻辑回归', '字词联合线性SVM']
    x = np.arange(3)
    fig, ax = plt.subplots(figsize=(8.8, 4.5), layout='constrained')
    for offset, metric, label, color in [(-.18, 'accuracy', '准确率', '#087d74'), (.18, 'macro_f1', '宏平均F1', '#93b9ac')]:
        values = [m['test'][metric] * 100 for m in models]
        bars = ax.bar(x + offset, values, .34, label=label, color=color)
        ax.bar_label(bars, labels=[f'{v:.2f}' for v in values], fontsize=10, padding=4)
    ax.set(xticks=x, xticklabels=names, ylim=(90, 100), ylabel='百分比 / %', title='三种模型在同一独立测试集上的表现')
    ax.legend(loc='upper left', frameon=False)
    fig.savefig(target / '模型指标对比.png', dpi=200); plt.close(fig)

    selected = report['models'][report['recommended_model']]
    matrix = np.asarray(selected['test']['confusion_matrix'])
    fig, ax = plt.subplots(figsize=(6.3, 5.3), layout='constrained')
    ax.imshow(matrix, cmap='Greens')
    ax.set(xticks=range(5), yticks=range(5), xticklabels=report['categories'], yticklabels=report['categories'],
           xlabel='预测类别', ylabel='真实类别', title='推荐线性SVM的独立测试混淆矩阵')
    for i in range(5):
        for j in range(5):
            ax.text(j, i, str(matrix[i, j]), ha='center', va='center', color='white' if i == j else '#254b3b')
    fig.savefig(target / '测试混淆矩阵.png', dpi=200); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.8), layout='constrained')
    ax.axis('off')
    boxes = [(0.18,.8,'网页界面\n单条 / 批量 / 实验 / 核对'),(.63,.8,'Python HTTP服务\n输入检查 / 同源请求 / 导出'),(.18,.3,'模型服务\nTF-IDF / 三算法 / 校准 / 解释'),(.63,.3,'项目数据\n公开语料 / 模型报告 / SQLite')]
    for x0,y,text in boxes:
        ax.text(x0,y,text,ha='center',va='center',transform=ax.transAxes,bbox={'boxstyle':'round,pad=1','facecolor':'#edf5f1','edgecolor':'#80a897'},linespacing=1.9)
    for a,b in [((.34,.8),(.46,.8)),((.63,.65),(.26,.39)),((.63,.65),(.63,.43)),((.35,.3),(.47,.3))]:
        ax.annotate('',xy=b,xytext=a,xycoords='axes fraction',arrowprops={'arrowstyle':'->','color':'#087d74','lw':1.5})
    ax.set_title('中文新闻标题分类系统的模块关系',pad=12)
    fig.savefig(target / '系统架构.png', dpi=200); plt.close(fig)
    print('已生成三幅独立实验配图')


if __name__ == '__main__':
    main()
