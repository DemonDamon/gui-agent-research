# GUI Agent 技术调研资料汇总

## AutoGLM 核心技术要点

### 1. 项目概述
- **开发者**: 智谱AI + 清华大学
- **定位**: ChatGLM 家族的基础智能体系列，用于 GUI 自动化控制
- **目标场景**: Web 浏览器 + Android 手机

### 2. 核心架构设计
- **中间接口设计 (Intermediate Interface Design)**
  - 分离规划(Planning)和定位(Grounding)行为
  - 规划层：需要灵活性和错误恢复能力
  - 定位层：强调动作准确性
  - 实验显示：该设计在 VAB-WebArena-Lite 上将 GPT-4o 性能从 18.2% 提升到 27.3%

- **自进化在线课程强化学习 (Self-Evolving Online Curriculum RL)**
  - 解决错误恢复问题
  - 解决指令和轨迹数据稀缺问题
  - 采用 Actor-Critic RL 框架
  - KL约束策略更新 + 置信度过滤经验回放

### 3. 技术栈
- **基础模型**: ChatGLM 家族 (GLM-4-9B)
- **多模态模型**: 大型多模态模型 (LMM) 用于 GUI 理解
- **训练技术**:
  - 预训练：利用弱监督决策信号
  - 行为克隆 (Supervised Fine-tuning)
  - 课程学习：从简单到复杂任务
  - 奖励建模：ORM 和 PRM
  - 强化学习：在线 RL

### 4. 性能指标
- **Web 浏览**:
  - VAB-WebArena-Lite: 55.2% 成功率 (第二次尝试 59.1%)
  - OpenTable 真实任务: 96.2% 成功率
- **Android 控制**:
  - AndroidLab: 36.2% 成功率
  - 中文 APP 常见任务: 89.7% 成功率

### 5. 开源项目 Open-AutoGLM
- **模型**: AutoGLM-Phone-9B, AutoGLM-Phone-9B-Multilingual
- **框架**: 基于 ADB 控制 Android 设备
- **支持操作**: Launch, Tap, Type, Swipe, Back, Home, Long Press, Double Tap, Wait, Take_over
- **支持应用**: 50+ 款主流中文应用

---

## 豆包手机核心技术要点

### 1. 产品概述
- **开发者**: 字节跳动 + 中兴通讯
- **硬件**: nubia M153 工程样机
- **定位**: 技术预览版，系统级 GUI Agent

### 2. 核心技术 - UI-TARS 模型系列

#### UI-TARS 1.0 (2026年1月)
- 字节 Seed 团队 + 清华联合开源
- 四大核心能力：感知、动作、推理、记忆
- 四大关键创新：
  1. 大规模 GUI 截图数据集 + 五大感知任务
  2. 跨平台统一动作空间
  3. 600万高质量 GUI 教程 + System-2 深思型推理
  4. 数百台虚拟机自动收集交互轨迹 + DPO 优化

#### UI-TARS 1.5 (2025年4月)
- 新增强化学习驱动的推理机制
- 执行动作前进行思考推演
- GUI 定位任务刷新 SOTA

#### UI-TARS 2.0 (2025年9月)
- **架构**: 532M 参数视觉编码器 + 23B 激活参数 MoE LLM
- **四大核心技术**:
  1. 可扩展数据飞轮 (Data Flywheel)
  2. 长时序稳定优化训练框架 (异步 rollout + 流式更新 + 增强 PPO)
  3. 混合 GUI 中心环境 (Hybrid GUI-centered Environment)
  4. 统一沙盒平台

### 3. 端云协同架构
- **标准模式**: 浅层 VLM，响应 <500ms，System-1 直觉反应
- **Pro 模式**: Deep Reasoning + Tool Use，System-2 深度推理
- **影子系统**: Virtual Display 虚拟化设计，后台并行运行

### 4. 硬件集成 (中兴贡献)
- 硬件平台: nubia M153
- 系统级权限: INJECT_EVENTS 用于模拟用户操作
- 隐私保护: 基于 Activity Hierarchy 抓取，非物理屏幕输出流

### 5. 系统级 GUI Agent 四层挑战
1. **感知层**: 毫秒级元素识别，抗动态干扰
2. **规划层**: 跨 App 信息流转，自我反思能力
3. **决策层**: 强泛化能力，细粒度操作
4. **系统层**: 响应速度，权限壁垒

---

## 技术对比要点

| 维度 | AutoGLM | 豆包手机 (UI-TARS) |
|------|---------|-------------------|
| 开发者 | 智谱AI + 清华 | 字节跳动 + 中兴 |
| 基础模型 | ChatGLM 家族 | MoE LLM 架构 |
| 核心创新 | 中间接口设计 + 自进化 RL | 数据飞轮 + 混合环境 |
| 部署形态 | 开源框架 + API | 系统级集成 |
| 目标平台 | Web + Android | 移动端优化 |
| 推理模式 | 单一模式 | 标准/Pro 双模式 |

