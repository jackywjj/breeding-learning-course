# 07-3｜REML 与方差组分 / REML and variance components

[目录 / Contents](00-目录.md) · [返回主文 / Main chapter](07-0-育种值计算与BLUP.md)

我把估方差和算育种值当作两个任务来追，分别查它们的输入、运行日志和产出。  
I trace estimating variances and predicting breeding values as separate tasks, checking the inputs, logs, and outputs for each.

原始来源是 [Masuda：REML 方差组分估计](https://masuday.github.io/blupf90_tutorial/vc_aireml.html)，本次可读页面为 2026 年 8 月版本。  
The original source is [Masuda: REML variance-component estimation](https://masuday.github.io/blupf90_tutorial/vc_aireml.html), with the readable page dated August 2026.

本篇于 **2026-10-18** 核对来源，来源要点采用概括，教学数据与演算均为自拟。  
Sources were checked on **2026-10-18**, source points are summarized, and teaching data and calculations are original.

> **我想弄懂的事｜方差参数从哪里来，为什么“算出 EBV”不等于“估计过遗传力”？**  
> **What I want to understand | Where do variance parameters come from, and why does EBV output not prove that heritability was estimated?**

## 01 · 来源要点 / Source points

原文把“solving”与“variance component estimation”分开，并介绍 AI 与 EM 两类 REML 迭代算法。  
The source separates “solving” from “variance component estimation” and introduces AI and EM REML iterations.

页面说明其版本中，给定方差求解与估计方差需要不同运行设置，但本篇不据此声称本地版本已经验证。  
The page describes different settings for solving with supplied variances and estimating them in that version, without establishing behavior of a local installation.

## 02 · 两个统计任务 / Two statistical tasks

**BLUP 任务**在协方差结构给定时预测随机效应，**方差组分任务**根据数据估计这些结构中的未知参数。  
The **BLUP task** predicts random effects given covariance structures, while **variance-component estimation** estimates their unknown parameters from data.

例如模型 $y=Xb+Za+e$ 可以需要 $\sigma_A^2$ 和 $\sigma_e^2$，多性状时还需要协方差。  
For example, $y=Xb+Za+e$ can require $\sigma_A^2$ and $\sigma_e^2$, plus covariances in a multi-trait model.

初始方差只是迭代的起点，输入过某个值不表示数据支持该值。  
Starting variances are only iteration inputs, and supplying a value does not establish support for it in the data.

## 03 · 似然的直觉 / Intuition for likelihood

**似然**把观察数据固定，比较不同参数假设下这些数据出现的相对支持程度。  
**Likelihood** holds the observed data fixed and compares their relative support under different parameter assumptions.

**最大似然 ML**选择使似然最大的参数，不能直接解释为参数本身的概率。  
**Maximum likelihood (ML)** selects parameters maximizing likelihood, which is not directly a probability of the parameters themselves.

**限制或残差最大似然 REML**基于消除固定效应影响的数据组合构造似然，以处理估计固定效应带来的信息损失。  
**Restricted or residual maximum likelihood (REML)** constructs likelihood from data combinations eliminating fixed effects to account for information used in estimating them.

## 04 · 用第03章数据理解自由度 / Understand degrees of freedom using Chapter 03

暂时只考虑独立正态记录、一个未知均值和一个未知方差，不涉及遗传分解。  
Temporarily consider only independent normal records with one unknown mean and one unknown variance, without genetic decomposition.

对 $x=[700,800,800,900]$，$n=4$、均值为 800、离差平方和 $SS=20{,}000$。  
For $x=[700,800,800,900]$, $n=4$, the mean is 800, and the squared-deviation sum is $SS=20{,}000$.

这个简单问题中，ML 方差为 $SS/n=5000$，REML 方差为 $SS/(n-1)=6666.67$。  
In this simple problem, ML variance is $SS/n=5000$ and REML variance is $SS/(n-1)=6666.67$.

用 $v$ 表示待估方差，忽略与 $v$ 无关的常数时，REML 对数似然可写如下。  
Writing the unknown variance as $v$ and omitting constants independent of $v$, the REML log-likelihood is as follows.

$$
\ell_R(v)=-\frac{n-1}{2}\log(v)-\frac{SS}{2v}+\mathrm{constant}
$$

$\log$ 是自然对数，保留似然大小顺序，方便把乘法化为加法。  
$\log$ is the natural logarithm, preserving likelihood ordering while turning multiplication into addition.

这个例子说明自由度修正，但一般动物模型的 REML 不是把所有表型方差简单除以 $n-1$ 就完成。  
This illustrates a degrees-of-freedom correction, but REML in a general animal model is not merely dividing overall phenotype variation by $n-1$.

## 05 · 为什么亲缘与记录结构不可缺 / Why relationships and record structure matter

动物模型通过亲属之间的相似及环境设计，区分加性遗传方差与其他方差来源。  
An animal model uses relatives' resemblance and environmental design to distinguish additive genetic variance from other components.

若每个家系完全对应唯一场区，可能难以把家系与场区影响分开，增加迭代次数不能自动修复这种混杂。  
If every family belongs to one unique site, family and site effects can be hard to separate, and extra iterations do not automatically repair this confounding.

同窝和永久环境遗漏时，某些共同偏离可能错误进入遗传方差，因此模型设计影响遗传力解释。  
Omitting litter or permanent environment can misattribute shared deviations to genetic variance, affecting heritability interpretation.

## 06 · 怎样解释迭代与收敛 / Interpret iteration and convergence

**迭代**是按规则从当前参数更新下一组参数，**收敛**表示达到指定的数值停止条件。  
**Iteration** updates parameters according to a rule, and **convergence** means a specified numerical stopping condition has been met.

收敛不证明模型正确，也不保证预测未来表现准确，应同时检查边界估计、标准误和验证结果。  
Convergence does not establish a correct model or accurate future prediction, so boundary estimates, standard errors, and validation also need inspection.

**边界估计**例如某方差接近 0，可能反映信号弱、设计不足或模型问题，不能统一解释成不存在遗传作用。  
A **boundary estimate**, such as a near-zero variance, can reflect weak signal, insufficient design, or model problems rather than universally proving no genetic effect.

## 07 · 估计后如何连接 BLUP / Connect estimates to BLUP

若一个自拟模型得到 $\sigma_A^2=300$、$\sigma_e^2=700$，则 $h^2=0.3$、$\lambda=700/300\approx2.3333$。  
If a hypothetical model gives $\sigma_A^2=300$ and $\sigma_e^2=700$, then $h^2=0.3$ and $\lambda=700/300\approx2.3333$.

这些组分进入 BLUP 的信息权重，但参数估计本身仍有不确定性，不能把输入后的准确度当成已知真值。  
These components enter BLUP weighting, but their estimates remain uncertain and resulting accuracies are not known truths.

这里的数值仅用于连接概念，本次没有对真实猪群运行 REML 或 BLUPF90。  
These numbers connect concepts only, and no real-herd REML or BLUPF90 run was performed.

## 08 · 怎样从日志确认估过方差组分 / Verify Variance Estimation from Run Logs

日志有 EBV 时，我会另外查任务设置、迭代记录及最终方差输出，以确认本次是否执行过方差估计。  
If a log shows EBVs, I also check task settings, iterations, and final variance output to determine whether this run estimated variances.

估计方差与按给定方差预测育种值是不同任务，日志里同一组参数可能只是输入时的设定值。  
Estimating variances and predicting breeding values from supplied variances are different tasks, and parameters in a log may simply have been provided as inputs.
