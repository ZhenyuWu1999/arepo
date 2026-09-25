# Yee + boost：384²扩展与static/moving匹配对照

作者：Codex；请求：Zhenyu。2026-09-24。

本轮补充第四个分辨率，并比较已确认的lab-frame reference与匹配static mesh。没有修改thesis、生产solver或默认Config。

## 方法与证据范围

同一冻结源码，N/Roe split+lumped、LDA/P1-U Gauss3+mixed-stage F1。Moving采用当前Arpaia几何、new-connectivity双sweep、现有mesh regularization，无topology repair。Static使用同一物理residual表示和时间质量选择，sigma=0。Static添加VORONOI_STATIC_MESH、移除moving专用flags及两个不可用的mesh-shaping参数，不改变其它物理参数。

使用SWIFT glass48以1×1、2×2、4×4、8×8周期铺接产生48²、96²、192²、384²节点，最后一档147456节点。这是同一铺接家族，不是四个独立松弛点集。旧helper精确复现前三档所有位置/流体IC arrays后生成384。所有static/moving对具有相同IC、初始状态、物理参数和实际步数。

Yee beta5，gamma1.4，box10，boost=(1,0)，t1，CFL.2，dt caps1/256、1/512、1/1024、1/2048。384 memory cap1024MiB，其它512MiB，此项只影响资源上限。单MPI rank，每进程OMP/BLAS各1线程，最大4个并发。

新建2个static二进制并完成12个新native runs：2static uniform、8static science、2moving384。复用2个已验证moving二进制、其uniform gates和6个moving48/96/192 science结果，未冒充新重跑。所有新run完成，保存rho/p为正，没有负质量或A2终止。Static坐标、VertexVelocity和median-dual面积保持不变。

误差在实际最终节点坐标上比较解析解，用最终median-dual area=m/rho归一化加权。Velocity L1是二维Euclidean向量误差。主结果采用全部四点的等权log-log最小二乘拟合：log(E)=log(C)+p log(h)，h=10/Nx。所得p是h/dt共同加密的整体观测阶，不是固定h时间阶或渐近阶的证明。逐段斜率只保留为附录诊断。本轮未增加384时间步减半；§105的96²减半检查仅约束该分辨率。

## 四点整体拟合收敛阶

全部四点等权拟合，不删除或降低任何数据点权重。图中符号为原始误差，直线为拟合结果，R²在log空间计算。

| Scheme / mesh | rho p | rho R² | velocity p | velocity R² |
|---|---:|---:|---:|---:|
| N_static | 0.9720 | 0.999869 | 0.9279 | 0.999849 |
| N_moving | 0.8995 | 0.998959 | 0.9044 | 0.999156 |
| LDA_static | 1.6870 | 0.997134 | 1.7738 | 0.999240 |
| LDA_moving | 1.7358 | 0.999061 | 1.4065 | 0.988995 |

## 原始四点误差

| Scheme / mesh | rho L1: 48 / 96 / 192 / 384 |
|---|---|
| N_static | 0.00400703415 / 0.00209061884 / 0.00104923979 / 0.000533659634 |
| N_moving | 0.0030303958 / 0.00170138888 / 0.000910300699 / 0.000467114363 |
| LDA_static | 0.000615304231 / 0.000167928767 / 5.13447574e-05 / 1.85295624e-05 |
| LDA_moving | 0.00106156351 / 0.000296614377 / 8.77569384e-05 / 2.88754894e-05 |

| Scheme / mesh | velocity L1: 48 / 96 / 192 / 384 |
|---|---|
| N_static | 0.0141707058 / 0.00753584076 / 0.00399099827 / 0.00205251108 |
| N_moving | 0.00758102718 / 0.00424185962 / 0.00224552121 / 0.00115947949 |
| LDA_static | 0.00236450255 / 0.000674677964 / 0.000186334252 / 6.02720806e-05 |
| LDA_moving | 0.00128675945 / 0.000381868366 / 0.000146264275 / 6.8714846e-05 |

![Convergence](/Users/zhenyuwu/arepo_rd/local_runs/yee_static_moving_384_20260924_v1/figures/yee_static_moving_convergence.png)

## 同分辨率moving/static误差比

小于1表示moving误差较小，大于1表示static误差较小。

| Scheme | Nx | rho moving/static | velocity moving/static |
|---|---:|---:|---:|
| N | 48 | 0.756269 | 0.534979 |
| N | 96 | 0.813821 | 0.562891 |
| N | 192 | 0.867581 | 0.562646 |
| N | 384 | 0.875304 | 0.564908 |
| LDA | 48 | 1.725266 | 0.544199 |
| LDA | 96 | 1.766311 | 0.566001 |
| LDA | 192 | 1.709170 | 0.784956 |
| LDA | 384 | 1.558347 | 1.140078 |

![Error ratio](/Users/zhenyuwu/arepo_rd/local_runs/yee_static_moving_384_20260924_v1/figures/yee_static_moving_error_ratio.png)

## 守恒与解释边界

| Scheme / mesh | Relative total-mass drift: 48 / 96 / 192 / 384 |
|---|---|
| N_static | 0 / 0 / 1.44652e-16 / 0 |
| N_moving | -1.61965e-05 / -3.70181e-06 / -2.48036e-06 / -6.0648e-07 |
| LDA_static | 0 / 0 / -1.44652e-16 / -1.44652e-16 |
| LDA_moving | -1.49573e-05 / -3.85379e-06 / -1.48254e-06 / -2.86961e-07 |

本对照考察当前完整实现。Moving减少相对网格的bulk advection，并不保证每个变量的误差都更小。网格几何、拓扑及endpoint更新也会变化；不能把观测误差差异直接分解成某一个来源。本轮没有禁用翻边、改变regularization或加入拓扑修正的归因实验。

原有384以下frame对照不能替代本轮moving/static对照，历史static Roe-LDA结果也不能替代当前Gauss3-LDA。当前所有曲线明确区分N/Roe与LDA/Gauss3组合。

## 可复现记录

档案：`/Users/zhenyuwu/arepo_rd/local_runs/yee_static_moving_384_20260924_v1`

新run保留输入、param、binary/config/source hashes、native日志、初始/.5/最终三份快照。分析与验证入口见README.md。复用run的绝对路径保存在campaign.json，读取前校验来源。

源码包SHA256：`b2a915f657bfc46ae6cce1cc315ea3776fafb74e8cd3e8d08b6d7a43302dd9c6`。

未commit/push，未修改thesis或默认配置。


## 第四点的结论与后续诊断

四点整体拟合的rho/velocity阶为：N static .972/.928、moving .900/.904；
LDA static1.687/1.774、moving1.736/1.407。主图保留全部原始点，并绘制每组一条
log-log最小二乘拟合直线。相邻区间斜率只作为诊断，不能把192→384的一段直接
当作总体收敛阶，也不能仅凭第四点判断LDA已发生持续降阶。

384²同分辨率误差对照仍成立：N moving相对static的rho/velocity L1分别降低
12.47%/43.51%；LDA moving为static的1.558/1.140倍。这是该分辨率的误差比较，
不是对渐近阶的判定。LDA绝对误差仍显著低于N。

用户指出单个分辨率点可能偏离整体趋势，需要进一步加密（例如768²）检查偏离
是否持续；受时间限制，本轮不再追加该计算。因此目前只报告全四点拟合的观测阶，
不以最后一个区间的斜率断言LDA渐近收敛阶降低。

全部2048步完成，384 moving N/LDA分别耗时10402.2/10381.0秒（约2小时53分钟），
匹配static分别1901.7/1906.7秒（约32分钟），全程总耗时比约5.47/5.44。
这是本机并发运行数据，不是严格控制负载的性能benchmark。

保存快照和日志中的predictor rho/p均为正；所有science failure列表为空。
384 moving的element residual conservation最大绝对defect：N5.227e−16、LDA1.233e−15。
这与endpoint总质量漂移不同：N−6.065e−7、LDA−2.870e−7，而static约机器精度。
不能用element residual守恒或总质量漂移较小来推出误差二阶收敛。

补查native_diagnostics.json发现LDA moving的F1 lumped fallback次数为
48/96/192/384：0/0/71/31898。384的31898次约占294912×2048个corrector-element
更新的0.00528%，不能仅凭次数认定它造成速度降阶。SVD记录包含数值rank3情况，
当前日志没有空间定位或误差贡献分解。Static LDA没有这类fallback。
已有48–192的lab/comoving对照不能代替384的frame敏感性验证。

可在讨论中列出以下可能机制，均未经过针对性的归因实验：

- 空间与时间误差混合：h和dt同步减半，有限分辨率下不同误差项可能叠加或部分抵消。
- Moving网格的几何形状、regularization和拓扑变化会改变误差系数，其影响可能随分辨率变化。
- 相对网格速度较小时的矩阵条件数与数值秩判定，以及少量F1 temporal lumping fallback，可能影响误差。

这些只能作为后续检查方向。当前没有独立多组glass、384半dt或768²数据来区分
有限分辨率波动与持续趋势，也没有证据指定其中某一项为原因。不追加新模拟。

两张PNG已视觉检查，无遮挡/裁切，四条曲线与summary.json一致。本次结果分析未编辑thesis。


## 附录：相邻区间斜率（仅供诊断）

这些局部斜率不作为主收敛阶，也不单独用于判断持续降阶。

| Method | interval | rho slope | velocity slope |
|---|---|---:|---:|
| N_static | 48→96 | 0.9386 | 0.9111 |
| N_static | 96→192 | 0.9946 | 0.9170 |
| N_static | 192→384 | 0.9754 | 0.9594 |
| N_moving | 48→96 | 0.8328 | 0.8377 |
| N_moving | 96→192 | 0.9023 | 0.9176 |
| N_moving | 192→384 | 0.9626 | 0.9536 |
| LDA_static | 48→96 | 1.8735 | 1.8093 |
| LDA_static | 96→192 | 1.7096 | 1.8563 |
| LDA_static | 192→384 | 1.4704 | 1.6283 |
| LDA_moving | 48→96 | 1.8395 | 1.7526 |
| LDA_moving | 96→192 | 1.7570 | 1.3845 |
| LDA_moving | 192→384 | 1.6037 | 1.0899 |
