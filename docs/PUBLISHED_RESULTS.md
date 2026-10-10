# 论文定量结果 / Published results

[中文主页](../README.zh-CN.md) · [English overview](../README.md) · [论文图集](PAPER_FIGURES.md)

以下数值摘录自 [Water 2025, 17(9), 1248](https://doi.org/10.3390/w17091248) 的 Tables 5、7、8、9。Traditional 指传统堰流公式方法，DTPM 指动态趋势预测方法。

## 总体结果 / Overall agreement — Table 7

相关系数按原表列示，不将其标为 R²；相对误差沿用论文定义，不重新命名为 MAPE。

### 2003

| 港闸 / Gate | 相关系数 Traditional | 相关系数 DTPM | 相对误差 Traditional | 相对误差 DTPM |
|---|---:|---:|---:|---:|
| 射阳河 / Sheyang | 0.48 | 0.83 | 9.71% | 2.61% |
| 黄沙港 / Huangsha | -0.05 | 0.77 | 11.82% | 1.70% |
| 新洋港 / Xinyang | -0.26 | 0.75 | 36.00% | 5.69% |
| 斗龙港 / Doulong | 0.72 | 0.90 | 8.15% | 2.02% |
| 平均 / Mean | 0.22 | 0.81 | 16.42% | 3.00% |

### 2006

| 港闸 / Gate | 相关系数 Traditional | 相关系数 DTPM | 相对误差 Traditional | 相对误差 DTPM |
|---|---:|---:|---:|---:|
| 射阳河 / Sheyang | 0.06 | 0.91 | 19.77% | 2.43% |
| 黄沙港 / Huangsha | 0.11 | 0.56 | 6.53% | 1.03% |
| 新洋港 / Xinyang | 0.44 | 0.87 | 9.24% | 1.33% |
| 斗龙港 / Doulong | 0.79 | 0.94 | 3.39% | 0.51% |
| 平均 / Mean | 0.35 | 0.82 | 9.73% | 1.32% |

## 五折交叉验证 / Five-fold cross-validation — Table 5

| 港闸 / Gate | 平均相对误差 / Mean relative error | 标准差 / Reported SD |
|---|---:|---:|
| Doulong | 5.96% | 0.052 |
| Huangsha | 6.43% | 0.074 |
| Sheyang | 13.95% | 0.146 |
| Xinyang | 9.57% | 0.089 |

论文将每站数据分成五个子集，逐折使用四个训练、一个测试。标准差数值按 Table 5 保留；原表列头标注 m³/s，正文称其为相对误差统计。本页不另行转换单位，也不将标准差解释为置信区间。

## 开关闸样本 / Gate-operation samples — Table 8

流量单位 m³/s。下表将原表带符号的相对误差取绝对值，以比较误差大小；流量数值及误差百分数保留论文精度。由于原表流量显示位数有限，不用显示值重新计算百分数。时间及开关状态按 Table 8 列示。

| Gate | Time | Operation | Observed Q | Traditional Q | Absolute error | DTPM Q | Absolute error |
|---|---|---|---:|---:|---:|---:|---:|
| Doulong | 2006-07-06 12:35 | 关闭 / close | 477 | 399 | 16.43% | 440 | 7.80% |
| Doulong | 2006-07-06 14:07 | 开启 / open | 464 | 429 | 7.45% | 453 | 2.38% |
| Doulong | 2006-07-06 19:35 | 关闭 / close | 394 | 299 | 24.06% | 408 | 3.53% |
| Doulong | 2006-07-06 21:34 | 开启 / open | 274 | 318 | 16.18% | 265 | 3.11% |
| Doulong | 2006-07-07 14:00 | 关闭 / close | 485 | 387 | 20.19% | 455 | 6.09% |
| Doulong | 2006-07-07 15:02 | 开启 / open | 478 | 381 | 20.40% | 456 | 4.59% |
| Xinyang | 2006-07-05 00:40 | 关闭 / close | 811 | 811 | 0.05% | 799 | 1.51% |
| Xinyang | 2006-07-05 02:00 | 开启 / open | 911 | 792 | 13.04% | 825 | 9.45% |
| Xinyang | 2006-07-05 02:10 | 关闭 / close | 615 | 1703 | 176.88% | 529 | 14.06% |
| Xinyang | 2006-07-06 05:40 | 开启 / open | 559 | 697 | 24.63% | 717 | 28.28% |
| Xinyang | 2006-07-06 22:30 | 关闭 / close | 721 | 694 | 3.74% | 692 | 4.04% |
| Xinyang | 2006-07-06 23:14 | 开启 / open | 716 | 681 | 4.92% | 722 | 0.87% |

DTPM 在斗龙港全部 6 个样本中误差较小；新洋港 6 个样本中有 3 个较小。两站所列样本的最大绝对误差均降低，但不等于每一次启闭都更准确。 / DTPM improves all six listed Doulong events and three of six listed Xinyang events. Lower maxima do not imply improvement at every event.

## 分工况结果 / Operational scenarios — Table 9

| Gate | Scenario | Mean relative error Traditional | Mean relative error DTPM | SD Traditional (reported) | SD DTPM (reported) |
|---|---|---:|---:|---:|---:|
| Doulong | 高水位 / High water | 15.27% | 8.98% | 0.09 | 0.04 |
| Doulong | 低水位 / Low water | 17.90% | 6.03% | 0.08 | 0.04 |
| Doulong | 快速开闸 / Rapid opening | 11.95% | 5.66% | 0.11 | 0.03 |
| Doulong | 缓慢开闸 / Slow opening | 12.49% | 2.68% | 0.08 | 0.01 |
| Xinyang | 高水位 / High water | 13.18% | 4.80% | 0.09 | 0.03 |
| Xinyang | 低水位 / Low water | 27.95% | 4.86% | 0.26 | 0.05 |
| Xinyang | 快速开闸 / Rapid opening | 8.42% | 6.64% | 0.09 | 0.02 |
| Xinyang | 缓慢开闸 / Slow opening | 28.89% | 11.50% | 0.15 | 0.10 |

Table 9 的标准差列头在原文标注为 m，此处保留数值及其来源，不与 Table 5 的标准差合并。 / Table 9 labels its SD columns in metres; values are retained as reported and are not pooled with Table 5.

## 误差带与置信区间 / Error bands and confidence intervals

Figure 10 用误差带展示相对误差大小，正文未给出置信水平或置信区间构造方法。因此，图中的带状区域不标为“95% 置信区间”；本项目也不从汇总标准差推算置信区间。

The figure presents error bands without a stated confidence level or interval-construction procedure. They are therefore described as error bands, rather than 95% confidence intervals.

### 来源注记 / Source notes

- Table 7 的 2006 年平均传统方法相关系数为 0.35，本页采用表值；附近正文另有 0.33 的表述。
- Table 8 的 176.88% 样本标为 2006-07-05 02:10、close；附近正文出现不同时间和操作表述。本页按表格报告该条样本，不把它改称开闸样本。
- 各表数值属于各自的统计范围，跨表比较需先核对样本与指标定义。
