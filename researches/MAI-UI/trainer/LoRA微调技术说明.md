# Qwen3-VL LoRA 微调技术说明

本文档说明在对 Qwen3-VL / MAI-UI 等视觉语言模型进行 LoRA 微调时的关键技术细节。

## 1. 训练警告信息解读

在启动训练时，可能会出现以下警告信息，均为正常现象：

| 警告信息 | 说明 | 影响 |
|---------|------|------|
| `FutureWarning: tokenizer is deprecated` | Transformers 5.0 版本后将移除 `tokenizer` 参数，建议改用 `processing_class` | 当前无影响，将来升级库时需修改代码 |
| `kernel version 3.10.0 below 5.5.0` | Linux 内核版本较老（CentOS 7 默认），PyTorch 建议更高版本 | 极端情况下可能导致进程挂起，大多数情况正常 |
| `model already on multiple devices` | 模型已分布到多卡，跳过额外的设备移动 | 正常行为，多卡训练符合预期 |
| `tokenizer has new PAD/BOS/EOS tokens` | tokenizer 和模型配置的特殊 token 不一致，已自动对齐 | 自动修复，无需担心 |
| `use_cache=True incompatible with gradient checkpointing` | 梯度检查点和 KV cache 互斥，自动关闭缓存 | 正常行为，梯度检查点用于节省显存 |

### 1.1 关于 Tokenizer PAD/BOS/EOS Tokens 对齐的详细说明

训练时可能看到如下提示：

```
The tokenizer has new PAD/BOS/EOS tokens that differ from the model config and generation config. 
The model config and generation config were aligned accordingly, being updated with the tokenizer's values. 
Updated tokens: {'bos_token_id': None}.
```

**这是正常行为，不需要担心。** 原因如下：

1. **Qwen 系列模型不使用传统 BOS token**
   
   Qwen/Qwen2/Qwen3 模型采用 **ChatML 格式**，使用 `<|im_start|>` 和 `<|im_end|>` 标记对话边界，而不是传统的 BOS（Beginning of Sentence）token：
   
   ```
   <|im_start|>user
   你好<|im_end|>
   <|im_start|>assistant
   你好！<|im_end|>
   ```

2. **`bos_token_id: None` 是设计如此**
   
   因为 Qwen 使用 ChatML 格式，不需要单独的 BOS token，所以 `bos_token_id = None` 是正确的配置。

3. **系统自动对齐配置**
   
   Transformers 库检测到 tokenizer 和模型配置不一致时，会自动将模型配置更新为 tokenizer 的值，确保一致性。这是一个**自动修复**的过程，不需要手动干预。

**结论**：这些警告不会阻止训练运行，可以正常继续训练。

---

## 2. LoRA 微调范围说明

### 2.1 当前配置的 target_modules

```yaml
target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj
  - gate_proj
  - up_proj
  - down_proj
```

这些模块均属于 **语言模型（LLM）部分**：

- `q_proj / k_proj / v_proj / o_proj` → Self-Attention 层
- `gate_proj / up_proj / down_proj` → Feed-Forward Network (FFN) 层

### 2.2 Qwen3-VL 模型架构

```
Qwen3-VL / MAI-UI
│
├── Visual Encoder (视觉编码器)
│   ├── Patch Embedding
│   ├── Transformer Blocks
│   │   ├── Self-Attention (qkv, proj)
│   │   └── MLP (fc1, fc2)
│   └── ...
│
├── Projector (视觉-语言投影层)
│   └── 将视觉特征映射到 LLM 的 embedding 空间
│
└── Language Model (语言模型)
    ├── Embedding Layer
    ├── Transformer Blocks
    │   ├── Self-Attention (q_proj, k_proj, v_proj, o_proj) ← LoRA 作用于此
    │   └── FFN (gate_proj, up_proj, down_proj) ← LoRA 作用于此
    └── LM Head
```

### 2.3 当前配置的训练范围

| 模块 | 是否被 LoRA 微调 |
|------|-----------------|
| Visual Encoder (视觉编码器) | ❌ 不训练 |
| Projector (投影层) | ❌ 不训练 |
| Language Model (语言模型) | ✅ 训练 |

**结论**：当前配置只微调语言模型部分的参数，视觉编码器的参数保持冻结。

---

## 3. 是否需要微调视觉部分？

### 3.1 场景分析

| 场景 | 建议 | 理由 |
|------|------|------|
| 学习新的输出格式/指令遵循 | 只调 LLM | 视觉理解能力已足够，只需调整输出行为 |
| 适配特定 UI 风格/元素 | 考虑调视觉部分 | 可能需要增强对特定视觉特征的理解 |
| 数据集与预训练领域差异大 | 建议调视觉部分 | 需要学习新的视觉概念 |
| 显存有限 | 只调 LLM | 视觉编码器参数量大，加入后显存占用增加 |

### 3.2 只调 LLM 的优点

1. **显存占用更低**：视觉编码器参数量大，不训练可节省大量显存
2. **训练更稳定**：保持预训练的视觉理解能力
3. **收敛更快**：可训练参数更少，优化更高效
4. **泛化性更好**：避免在小数据集上过拟合视觉特征

### 3.3 调整视觉部分的优点

1. **更强的领域适应**：针对特定视觉内容进行优化
2. **更好的细粒度理解**：学习识别特定的 UI 元素、图标等
3. **端到端优化**：整个模型协同优化

---

## 4. 如何微调视觉部分

### 4.1 查看模型层名称

在训练脚本中添加以下代码，打印所有模块名称：

```python
# 在 model 加载后添加
for name, module in model.named_modules():
    print(name)
```

或者只打印包含特定关键词的层：

```python
for name, module in model.named_modules():
    if any(k in name for k in ["visual", "vision", "patch", "proj"]):
        print(name)
```

### 4.2 扩展 target_modules 配置

根据模型实际结构，可以添加视觉编码器的模块。以下是示例配置：

```yaml
lora:
  enabled: true
  r: 16
  alpha: 32
  dropout: 0.05
  target_modules:
    # === 语言模型部分 ===
    - q_proj
    - k_proj
    - v_proj
    - o_proj
    - gate_proj
    - up_proj
    - down_proj
    
    # === 视觉编码器部分（需根据实际模型结构调整）===
    # Qwen-VL 系列常见的视觉层名称
    - visual.attn.qkv
    - visual.attn.proj
    - visual.mlp.fc1
    - visual.mlp.fc2
    
    # 或者使用通配符匹配（如果 PEFT 支持）
    # - "visual.*proj"
    # - "visual.*fc*"
```

### 4.3 注意事项

1. **显存增加**：添加视觉部分后显存占用会显著增加，可能需要：
   - 降低 batch size
   - 启用 4-bit 量化 (`use_4bit: true`)
   - 减小 LoRA rank (`r: 8`)

2. **学习率调整**：视觉和语言部分可能需要不同的学习率
   - 视觉部分通常使用更小的学习率（如 1e-5）
   - 语言部分可以用相对更大的学习率（如 2e-4）

3. **数据量要求**：微调视觉部分需要更多的训练数据，避免过拟合

---

## 5. 推荐配置

### 5.1 仅微调 LLM（默认推荐）

适用于：指令遵循、格式调整、轻量级适配

```yaml
training:
  lora:
    enabled: true
    r: 16
    alpha: 32
    dropout: 0.05
    target_modules:
      - q_proj
      - k_proj
      - v_proj
      - o_proj
      - gate_proj
      - up_proj
      - down_proj
  
  gradient_checkpointing: true
  use_4bit: false
  
  sft:
    learning_rate: 2.0e-4
    per_device_train_batch_size: 1
    gradient_accumulation_steps: 16
```

### 5.2 同时微调视觉和 LLM

适用于：领域差异大、需要学习新视觉概念

```yaml
training:
  lora:
    enabled: true
    r: 8  # 降低 rank 以节省显存
    alpha: 16
    dropout: 0.05
    target_modules:
      # LLM 部分
      - q_proj
      - k_proj
      - v_proj
      - o_proj
      - gate_proj
      - up_proj
      - down_proj
      # 视觉部分（根据实际模型调整）
      - visual.attn.qkv
      - visual.attn.proj
      - visual.mlp.fc1
      - visual.mlp.fc2
  
  gradient_checkpointing: true
  use_4bit: true  # 启用 4-bit 量化
  
  sft:
    learning_rate: 1.0e-4  # 适当降低学习率
    per_device_train_batch_size: 1
    gradient_accumulation_steps: 32  # 增加累积步数
```

---

## 6. 常见问题

### Q1: 如何判断是否需要微调视觉部分？

**方法**：先用只调 LLM 的配置训练一版，评估效果：
- 如果模型能正确理解图像内容，但输出格式/行为不对 → 只调 LLM 足够
- 如果模型对特定视觉元素识别不准确 → 考虑加入视觉部分

### Q2: 添加视觉部分后 OOM 怎么办？

**解决方案**（按优先级）：
1. 启用 4-bit 量化：`use_4bit: true`
2. 减小 LoRA rank：`r: 8` 或 `r: 4`
3. 减小 batch size 并增加 gradient accumulation
4. 使用 DeepSpeed ZeRO 优化

### Q3: 如何验证 LoRA 作用在了哪些层？

在训练开始时，PEFT 会打印可训练参数信息：

```
trainable params: 12,345,678 || all params: 2,000,000,000 || trainable%: 0.62%
```

也可以手动检查：

```python
for name, param in model.named_parameters():
    if param.requires_grad:
        print(f"Trainable: {name}")
```

---

## 7. 参考资料

- [PEFT 官方文档](https://huggingface.co/docs/peft)
- [Qwen-VL 技术报告](https://arxiv.org/abs/2308.12966)
- [LoRA 论文](https://arxiv.org/abs/2106.09685)
