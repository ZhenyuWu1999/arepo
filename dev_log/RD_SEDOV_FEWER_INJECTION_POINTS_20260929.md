# Sedov：1、7、21 点注入对照及 SWIFT 初值核对

作者：Codex。日期：2026-09-29。用户要求尝试更少注入点，并核实 SWIFT 是否
只向一个粒子注入。对应 log3 §160；本轮没有修改数值求解器。

## SWIFT 实际设置

本机 `/Users/zhenyuwu/SWIFT/examples/HydroTests/SedovBlast_2D/makeIC.py`
与本次下载的[官方上游文件](https://github.com/SWIFTSIM/SWIFT/blob/master/examples/HydroTests/SedovBlast_2D/makeIC.py)
逐字节一致，SHA256 为
`6dbe2abe9dba78b8e5aea7a1243b916c264b54b96d72ea6be845163e95ea6fe8`。
本机 SWIFT commit 为 `8dc43c3c1f08755250a2c0edd141d78120d00b21`。

该二维例子设定 N_inject=21，将粒子按到 (0.5,0.5) 的距离排序，选择最近21个。
所有 SPH 粒子质量 m=1/16384，热粒子的比内能赋为 E₀/(21m)，因此热区总能量为1。
其余粒子使用 p₀=1e−6、ρ₀=1、γ=5/3。注释 “Make the central particle detonate”
使用了单数，但实际切片是 index[0:N_inject]，不能据注释判断为单粒子。
这个结论针对指定的 SedovBlast_2D 例子，不是所有 SWIFT 测试的统一规定。

我们之前的21点初值正是参照此选择。RD节点质量是各自 median-dual 面积，略有差异，
因此使用统一比内能 u_hot=1/Σm_hot；它与 SWIFT 的等质量情形等价地保证热区总能量1。
赋值会替换热节点原背景内能；冷区保留背景，所以盒子总能量略大于1，约1.0000015。
本次未运行 SWIFT hydro，只核对其初值生成器和参数。

## 控制变量与归档

相同16384点玻璃网格、周期单位盒、γ=5/3、ρ₀=1、p₀=1e−6、E_hot=1、v₀=0。
选择最近的1点或7点；不移动玻璃节点，不平滑热区，不提高背景压力。
moving mesh 使用标准 regularization，lab frame，Rusanov 空间分布和 lumped RK2，
adaptive equal timesteps，CFL=0.1、cap=0.01，终点 t=0.05。

| 热节点数 | 热节点总质量 | 热区初始压力 | 热节点到盒中心的最大距离 |
| --- | ---: | ---: | ---: |
| 1 | 6.08969682e−5 | 10947.4525 | 0.00365316 |
| 7 | 4.26327880e−4 | 1563.7417 | 0.01129803 |
| 21，既有参考 | 1.27985351e−3 | 520.8929 | 0.01959655 |

单点为 ID8256，坐标 (0.50006805,0.49634748)。最后一列描述节点位置相对盒中心，
不是 P1基函数的完整支持半径。图中径向坐标分别以各初始注入超额能量的质心为中心，
避免把单点偏离 (0.5,0.5) 的几何偏移误判为激波不对称。21点参考也用同样规则重画。
散点保留全部节点，曲线为90个径向bin的算术平均；解析参考为二维柱对称 Sedov，
E=1、R∝t^(1/2)，不是三维球对称解。有限热区初值并非精确点源初值。

两套配置分别为无 repair 与原 unlimited connectivity repair 加一致的 predictor。
复用既有冻结 binary，没有重新编译或改变求解器：

- 无 repair：`99f9f6507482df57247086e68315790a99a6761de82f86f79f616cf5daf29816`，
  来自 `sedov_positivity_20260929_v2`。
- 原 repair：`bbba3d6878bd65d9a04991c74caaf6e79948b901239f16b8470dfee362afd852`，
  来自 `sedov_topology_repair_20260929_v1`。

档案 `../local_runs/sedov_injection_sweep_20260929_v1/` 按方法保存各自 source.tar/
provenance、Config、generated header、binary、build log/linkage，并保存所有新IC、
参数、运行日志/快照和预先冻结的运行脚本。两个新的uniform gate通过后才运行science。
OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=1，最多4个单rank进程；repair失败后剩2个。
入口为 `examples/Sedov_2d/run_injection_sweep.py` 和 `analyze_injection_sweep.py`。

## 完成结果：无 repair

1点和7点均完成t=0.05，分别3189/3142步，运行约461/456秒。两个新uniform gate
逐点误差均1.11e−15。以下21点为已核验的既有同配置参考，并非本轮重新运行。

| 热节点数 | 最终ρ_min | 最终ρ_max | ΔM/M | ΔE/E |
| --- | ---: | ---: | ---: | ---: |
| 1 | 0.19576226 | 2.61579026 | −0.237630% | −2.576317% |
| 7 | 0.19778682 | 2.64779585 | −0.239931% | −2.665694% |
| 21 | 0.19600852 | 2.63043575 | −0.239707% | −2.414700% |

最终p_min均约1e−6。新两组全部12662个物理stage的ρ和内能密度为正；最大实际
stage CFL为0.107438/0.108569，低于实现检查的凸组合上界1；最小b为0.497257/
0.497358。名义CourantFac=0.1不意味着每个stage测得的系数都≤0.1。

三组径向平均曲线基本重合，密度峰值显著低于解析强激波跳跃4，内区速度和压力
也有系统性偏差；减小注入点数没有明显改善激波展宽。二维图仍接近圆形，并有
沿激波环的起伏。本轮没有计算专门的角向各向异性误差，不能宣称严格球/圆对称，
也不把低阶Rusanov的结果推广到LDA或Roe N。

以各自注入能量质心计算、按最终median-dual面积加权的全盒L1：

| 热节点数 | 密度L1 | 压力L1 |
| --- | ---: | ---: |
| 1 | 0.0486541 | 0.1080871 |
| 7 | 0.0490214 | 0.1072873 |
| 21 | 0.0482647 | 0.1035865 |

这些是固定分辨率的初值敏感性对照，不是收敛阶或守恒验证；误差同时受离散耗散、
热区初始分布、几何转移及能量损失影响。解析参考始终用初始E=1，不用损失后的能量
重新调节激波半径。参考shock radius为0.25799461。

## 原 repair 仍失败

| 热节点数 | 最后接受时刻 | 失败时刻 | repair 后最低压力 |
| --- | ---: | ---: | ---: |
| 1 | 0.0050537109375 | 0.00506591796875 | −0.02073846 |
| 7 | 0.00543212890625 | 0.0054443359375 | −0.01911174 |

两组都在ID7932和7977出现负压，与21点原repair的失败节点相同。失败检查位于
`rd_ale_apply_topology_repair()`，早于本步Rusanov残差及RK更新。此前分别接受887/
860步，1774/1720个物理stage全部正性/CFL/b检查通过；成功非零repair步183/221
（不是flip数），修正总量审计最大1.665335e−15/3.330669e−16。

最后接受状态的相对能量变化为−2.34960039e−6/−1.89219730e−6，质量变化
−1.70152026e−9/−1.88483507e−9；这是很早的终止时刻，不能与无repair在t=0.05的
表格直接作精度排名。减少注入点没有修复原unlimited remap的正性问题。
下一步改造仍应区分物理残差保正和同一时刻connectivity转移保正。

## 输出与检查

本轮共6次原生尝试：2个uniform gate成功、2个无repair Sedov完成、2个repair
Sedov数值失败。共22个新保存快照均有限且ρ/p/质量为正；两组失败发生在下一步
repair，不能用正的已保存快照掩盖失败。全部4组science共16156个已接受stage
正性检查通过。

`analysis/verification.json` 保存每组完整状态、快照hash、二进制/Config/source.tar/
IC/参数核验、初始能量积分、stage范围、失败行和最终误差。初值的native面积与独立
周期Delaunay面积一致到既有容差，热区总能量为1。图片均已视觉检查：

- `analysis/injection_profiles.png`：1/7/21点径向散点、平均线及解析解，350dpi。
- `analysis/injection_density.png`：三组二维密度及解析激波圆，300dpi。
- `analysis/injection_budgets.png`：质量/能量随时间，包括明确标为失败的repair段。

初次分析对uniform非零速度要求直接等于IC，触发1 ulp差异：native初始化先存m v再除m。
已改为对这一实际round trip逐值bitwise核对，所有节点完全相同；坐标也bitwise一致。
没有放宽数值断言、修改数据或重跑物理。初版分析脚本、错误说明和修正版hash均保存。
Python语法检查通过；本轮不改solver，因此未重复与此初值变化无关的代数单测。
结束时无活动solver，没有修改thesis、默认Config，没有commit/push或COSMA操作。
