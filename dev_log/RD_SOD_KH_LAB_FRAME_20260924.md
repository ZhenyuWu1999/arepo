# Moving Sod / smooth KH：关闭 element co-moving frame 的对照

作者：Codex；请求：Zhenyu。日期：2026-09-24。

## 结论

关闭co-moving后，N/Roe split与LDA/Gauss3均完成Sod到t=.08和smooth KH到t10，没有负质量或A2失败。Sod误差基本不变，KH长期轨迹和统计已有可测差异。可以将co-moving保留为可选优化，但完整moving方案的长期准确性与全局守恒仍未完成验证。

## 比较范围

按当前论文选择，比较 **N/Roe split** 和 **LDA/Gauss3 contour**。每个方案新跑lab frame，并与已归档co-moving结果配对。这里lab frame仍使用移动网格，只是直接用lab conserved variables计算元素矩阵和残差。

复用2026-09-24前一轮精确冻结源码。配置唯一差别是移除RD_ELEMENT_COMOVING_FRAME；IC和参数除输出路径外相同，控制二进制和所有配置/源码hash已核验。控制结果是复用档案，不冒充新重跑。N保留完整U−Uhat mesh correction，LDA保留Gauss3和mixed-stage F1，当前Arpaia geometry和new-connectivity双sweep均不改。

- Smooth KH：glass48²、unit box、gamma1.4、tanh宽度.025、rho1/2、p2.5、vx±.5、vy=.1sin(4πx)，RD spectral CFL=.3、dt cap=.02、目标t10。
- Sod：periodic glass128²，单管有效初始Nx约64、gamma1.4、原Sod CFL=.08、dt cap=1/3000、raw t=.08，对应tube time=.16。
- 单rank、OMP/BLAS各1线程，最多4并发。未改算法、稳定化或断言容差。相同CFL和dt cap下，各自解决定实际步长，长期步数可以不同。

旧Gresho boost10首步失败对应早期LDA/Roe split/lab，并不是当前LDA/Gauss3的直接证据。本次直接回答当前方案是否因关闭frame而退化，不对所有boost、分辨率、CFL、MPI作推广。

## Sod：原始时间 t=.08

| Scheme | Frame | 完成 | rho L1 | vx L1 | plateau vx std | vx min/max |
|---|---|---|---:|---:|---:|---:|
| N | lab | True | 0.023602714 | 0.0551430074 | 0.0139773418 | -2.16432e-08 / 1.01087 |
| N | comoving | True | 0.0235932958 | 0.0550656556 | 0.0139149688 | -2.16432e-08 / 1.01104 |
| LDA | lab | True | 0.0169419415 | 0.0443405738 | 0.0258285426 | -0.737816 / 1.05913 |
| LDA | comoving | True | 0.0169389427 | 0.0442895771 | 0.0258498167 | -0.737231 / 1.05818 |

L1以当前median-dual area=m/rho在raw x∈(.25,.75)内归一化加权，与对应位置/时间的解析Riemann解比较。平台速度std相对于区域加权均值，区域为ξ=2(x−.25)∈[.70,.76]。LDA的速度undershoot须一并保留，不能因完成就称其无振荡。

## Smooth KH：长期演化

| Scheme | Frame | 完成t10 | 最后保存时间 | rho min/max | p min | 相对总质量漂移 | 横向动能 |
|---|---|---|---:|---:|---:|---:|---:|
| N | lab | True | 10 | 1.06459 / 2.27642 | 2.33786 | 0.012339292 | 0.057295065 |
| N | comoving | True | 10 | 1.10966 / 2.0884 | 2.35701 | 0.013818743 | 0.072158964 |
| LDA | lab | True | 10 | 0.842624 / 2.09448 | 2.07284 | 0.012230991 | 0.080798708 |
| LDA | comoving | True | 10 | 0.892303 / 2.06077 | 2.06316 | 0.011883883 | 0.093596063 |

KH没有在这里使用解析参照解。形态、横向动能、密度/压力下限、质量漂移分别记录；不能把逐点轨迹差异直接当作精度误差，也不能把形态看起来相似当作严格等价。

## 配对场差异

按ParticleID比较，坐标取周期最短差，只在输出时间完全相同时计算，未插值或外推。速度mean absolute对所有粒子和两个分量取平均。

| Scheme | Problem | 最后共同保存时间 | velocity mean absolute | density mean absolute | position mean absolute |
|---|---|---:|---:|---:|---:|
| N | kh | 10 | 0.260219 | 0.121082 | 0.21859 |
| N | sod | 0.08 | 6.72516e-05 | 1.81086e-05 | 5.61263e-06 |
| LDA | kh | 10 | 0.315209 | 0.152944 | 0.20638 |
| LDA | sod | 0.08 | 0.000157756 | 3.7608e-05 | 4.12636e-06 |

所有时间点的差异和场统计保留在JSON。早期接近舍入的扰动可能随非线性演化及改变的几何/拓扑放大，长期结果不以机器精度逐点相等作为验收标准。具体放大机制未在这次试验中单独隔离。

## 验证边界与建议

新运行4个uniform门禁全部通过，rho/p/v最大变化1.1102e−15。完整求解器的A2等断言保持启用。保存状态的正性、原生运行完成和空间residual总和检查，与全局更新守恒和收敛性是不同性质。

这组对照支持暂不将co-moving作为论文参考方案的必选组成部分，代码保留为数值条件改善的可选项。依据是两组lab方案都完成了Sod与KH，Sod密度L1相对变化分别仅约0.040%（N）和0.018%（LDA），速度L1变化均小于0.2%。LDA shock的undershoot仍然存在，两种frame都没有消除它。

对KH长期结果的支持更有限：lab终点横向动能相对co-moving低约20.6%（N）和13.7%（LDA），涡位置/细节已有明显差异。这不等于已证明lab更差，也不能称两者长期精度等价；本次没有高分辨率参考或ensemble来裁决。早期相近、后期分离的轨迹与非线性放大相容，但尚未独立分解roundoff、rank分支、时间步和topology的贡献。

所有KH仍有约1.19–1.38%的终点总质量漂移：lab N/LDA约1.234%/1.223%，co-moving N/LDA约1.382%/1.188%。因此整体moving RD仍需继续验证，co-moving是否列为baseline与全局守恒问题应分开处理。当前测试足以支持论文简化该技术性选择，不能支持“lab frame在所有情况下与co-moving同样准确”的更强结论。

这轮未修改thesis、生产solver或默认配置，未commit/push。共4个新独立二进制、8次新原生运行，与8个已有co-moving控制（4 uniform、4 science）配对。

## 档案

- [完整统计](/Users/zhenyuwu/arepo_rd/local_runs/sod_kh_lab_frame_20260924_v1/summary.json)
- [复现说明及设置](/Users/zhenyuwu/arepo_rd/local_runs/sod_kh_lab_frame_20260924_v1/README.md)
- [配置和来源核验](/Users/zhenyuwu/arepo_rd/local_runs/sod_kh_lab_frame_20260924_v1/verification.json)

![Sod lab与co-moving](/Users/zhenyuwu/arepo_rd/local_runs/sod_kh_lab_frame_20260924_v1/figures/sod_frame_profiles.png)

![Smooth KH演化](/Users/zhenyuwu/arepo_rd/local_runs/sod_kh_lab_frame_20260924_v1/figures/kh_frame_evolution.png)

![KH诊断](/Users/zhenyuwu/arepo_rd/local_runs/sod_kh_lab_frame_20260924_v1/figures/kh_frame_diagnostics.png)
