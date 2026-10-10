# 研究方法 / Research method

[中文主页](../README.zh-CN.md) · [English overview](../README.md) · [Results](PUBLISHED_RESULTS.md)

## 1. 观测与工程条件 / Observations and geometry

研究使用四座潮汐港闸的闸上水位 $Z_u$、闸下水位 $Z_d$、实测流量 $Q$ 与测量时间 $t$。工程条件包括闸门开启总宽度 $B$ 与闸底高程 $Z_0$。数据按站点、时间组织，采样间隔由时间戳确定。

The method combines timestamped upstream/downstream levels and discharge with opening width and sill elevation. Measurements must use compatible elevation datums and consistent time units.

## 2. 用物理关系构造训练目标 / Coefficient target

淹没出流关系为：

$$
Q=\phi B(Z_d-Z_0)\sqrt{2g(Z_u-Z_d)}
$$

在该公式适用的水力条件下，由观测反算历史系数：

$$
\phi=\frac{Q}{B(Z_d-Z_0)\sqrt{2g(Z_u-Z_d)}}
$$

论文 §3.2、Table 2 以斗龙港为例：$B=80\,\mathrm{m}$，$Z_0=-3\,\mathrm{m}$，$g=9.8\,\mathrm{m/s^2}$。网络学习的是随水流条件变化的系数。

The observed discharge supplies the coefficient target through the physical relationship. Geometry and water-level conditions remain part of the final discharge calculation.

## 3. 六项输入 / Six predictors

$$
\mathbf{x}_t=\left[Z_u,Z_d,\frac{\partial Z_u}{\partial t},\frac{\partial Z_d}{\partial t},\frac{\partial(Z_u-Z_d)}{\partial t},\frac{\partial Q}{\partial t}\right]_t
$$

两项水位刻画状态，四项变化率刻画动态趋势。变化率的离散表达为 $\Delta v/\Delta t$，其中 $\Delta t$ 来自实际测量时间。比如同样下降 0.1 m，10 分钟内发生与 1 小时内发生所代表的变化速度不同。

这不是把时间戳或时间间隔直接列为第七项输入。流量 $Q$ 的作用包括计算流量变化率和反算目标系数。水位差变化率与两个水位变化率存在代数联系；六列描述的是论文采用的输入形式，并不表示六个相互独立的观测量。

The two level features encode hydraulic state; four rates encode temporal change. Use actual elapsed time rather than assuming equally spaced observations. The head-difference rate is algebraically related to the two level rates.

## 4. 时序配对与训练 / Target alignment and training

论文 §3.2 与专利说明书实施例将六项输入与后续时刻的出流系数配对，训练 BP 网络。论文采用一个隐藏层，神经元数为 6–5–1；学习率 0.7、动量 0.5、连接率 1.0、训练系数精度 0.001，最大训练次数 10,000。

激活函数在论文正文中描述为隐藏层和输出层采用 tanh；Table 4 使用配置名称 “Double Sigmoid Cutoff Function”。训练方法的原配置名称为 “High-Precision Processing Method”。这些名称按论文保留，不将其自行对应到某个软件库的优化器或停止准则。

The published workflow pairs the six predictors with a subsequent coefficient. The reported architecture and settings are documented in the overview. Their exact software configuration labels are retained rather than equated with an unspecified optimizer in another library.

## 5. 由系数得到流量 / From coefficient to discharge

训练完成后，输入水位与趋势特征，得到预测系数 $\hat\phi$，并在对应水位、闸门开启宽度等条件下代回堰流公式计算流量。用于训练的目标、预测时可取得的观测，以及流量计算所需的水位应在时间上明确对应。

The predicted coefficient is substituted into the weir equation. An application must specify the availability and time alignment of the hydraulic conditions used in that equation; coefficient prediction alone does not supply future water levels.

## 6. 评价 / Evaluation

论文从四个层面评价方法：

1. 2003、2006 年四座港闸的总体相关系数与相对误差（Table 7）。
2. 每站五折交叉验证的平均相对误差与标准差（Table 5）。
3. 斗龙港、新洋港选定启闭时刻的计算流量及误差（Figure 10、Table 8）。
4. 高水位、低水位、快速开闸、缓慢开闸四种工况的误差（Table 9）。

原文五折验证按每站五个子集、四折训练一折测试描述。总体结果、交叉验证与启闭样本使用不同统计范围，应分别解读。原文没有为 Figure 10 的误差带指定 95% 等置信水平。

Evaluation covers overall agreement, five-fold validation, individual operational transitions and four hydraulic/operational scenarios. These are distinct summaries and should not be substituted for one another.

## 7. 复用方法 / Using the method in another study

可在能够设置输入、目标和网络参数的学习工具中采用上述流程：整理当地观测；构造趋势特征与系数目标；从案例参数开始试验；使用独立资料检查误差；单独考察启闭及其他关键工况。参数应随站点、样本量和时间分辨率重新验证。专利也提出使用其他学习模型的可能性，本文报告的实证结果来自 BP 网络。

The reusable contribution is the feature–coefficient–hydraulic calculation workflow. A new application should tune and validate the model for its own station and operating conditions. Alternative learning models are discussed in the patent; the paper's reported experiments use BP.

## 来源 / Sources

- Zhang et al. (2025), [Water 17(9), 1248](https://doi.org/10.3390/w17091248), §3.2, Tables 2–5, §4.
- [CN119578220A](https://patents.google.com/patent/CN119578220A/zh), 权利要求 1–5、说明书实施例 1。

### 数值使用注记 / Numerical interpretation

论文 Table 3 的变化率单位标题与部分示例数值的时间尺度并不一致，部分水位差变化率示例也不直接等于两个水位变化率之差。因此本页按正文定义说明特征；将方法实现到新数据时，应使用明确的差分定义和时间单位，不能直接把示例表当作已统一单位的训练矩阵。

Some numerical examples in Table 3 do not directly match its stated units or the difference between the two level-rate columns. The definitions above follow the method text; any numerical implementation needs explicit differencing and unit conventions.
