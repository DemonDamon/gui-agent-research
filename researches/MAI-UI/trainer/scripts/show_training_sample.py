#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
展示一个完整的conversation训练样本格式

这个脚本会：
1. 加载一个训练样本
2. 展示原始格式
3. 展示转换后的Qwen VL格式
4. 展示最终tokenize后的格式（如果可能）
"""

import json
import sys
from pathlib import Path

# 添加trainer目录到路径
trainer_dir = Path(__file__).parent.parent
sys.path.insert(0, str(trainer_dir))

from sft_trainer import (
    MultiModalDataCollator,
    extract_images_from_messages,
    PreprocessedMultiModalDataset,
)


def load_sample(data_path: str, index: int = 0):
    """加载一个训练样本"""
    with open(data_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == index:
                return json.loads(line.strip())
    return None


def show_sample_structure(sample: dict):
    """展示样本结构"""
    print("=" * 80)
    print("训练样本结构分析")
    print("=" * 80)
    print()
    
    # 1. 原始格式
    print("1. 原始数据格式 (JSONL文件中的格式)")
    print("-" * 80)
    print(json.dumps(sample, indent=2, ensure_ascii=False))
    print()
    
    # 2. 提取关键信息
    print("2. 关键字段解析")
    print("-" * 80)
    messages = sample.get("messages", [])
    metadata = sample.get("metadata", {})
    
    print(f"消息数量: {len(messages)}")
    for i, msg in enumerate(messages):
        role = msg.get("role", "")
        content = msg.get("content", "")
        print(f"\n  消息 {i+1} - 角色: {role}")
        
        if isinstance(content, list):
            print(f"    内容类型: 多模态列表 (包含 {len(content)} 个元素)")
            for j, item in enumerate(content):
                item_type = item.get("type", "")
                if item_type == "text":
                    text = item.get("text", "")
                    preview = text[:100] + "..." if len(text) > 100 else text
                    print(f"      元素 {j+1}: 文本 - {preview}")
                elif item_type == "image_url":
                    url = item.get("image_url", {})
                    if isinstance(url, dict):
                        url_str = url.get("url", "")[:50] + "..." if len(url.get("url", "")) > 50 else url.get("url", "")
                    else:
                        url_str = str(url)[:50] + "..."
                    print(f"      元素 {j+1}: 图片 - {url_str}")
                elif item_type == "image":
                    print(f"      元素 {j+1}: 图片对象 (PIL Image)")
        else:
            preview = str(content)[:100] + "..." if len(str(content)) > 100 else str(content)
            print(f"    内容: {preview}")
    
    print(f"\n元数据:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    print()
    
    # 3. 转换为Qwen VL格式（模拟）
    print("3. 转换为Qwen VL格式 (训练时使用的格式)")
    print("-" * 80)
    
    # 提取图片
    images = extract_images_from_messages(messages)
    print(f"提取到的图片数量: {len(images)}")
    if images:
        for i, img in enumerate(images):
            print(f"  图片 {i+1}: 尺寸 {img.size}, 模式 {img.mode}")
    
    # 转换为Qwen格式
    qwen_messages = []
    image_idx = 0
    
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if isinstance(content, str):
            qwen_messages.append({"role": role, "content": content})
        elif isinstance(content, list):
            qwen_content = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        qwen_content.append({
                            "type": "text",
                            "text": item.get("text", "")
                        })
                    elif item.get("type") == "image_url":
                        if image_idx < len(images):
                            qwen_content.append({
                                "type": "image",
                                "image": images[image_idx]
                            })
                            image_idx += 1
            qwen_messages.append({"role": role, "content": qwen_content})
    
    print("\nQwen VL格式的messages:")
    for i, msg in enumerate(qwen_messages):
        role = msg.get("role", "")
        content = msg.get("content", "")
        print(f"\n  消息 {i+1} - 角色: {role}")
        if isinstance(content, list):
            print(f"    内容: 多模态列表 ({len(content)} 个元素)")
            for j, item in enumerate(content):
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text = item.get("text", "")
                        preview = text[:150] + "..." if len(text) > 150 else text
                        print(f"      元素 {j+1}: 文本")
                        print(f"        {preview}")
                    elif item.get("type") == "image":
                        print(f"      元素 {j+1}: 图片对象")
        else:
            preview = str(content)[:150] + "..." if len(str(content)) > 150 else str(content)
            print(f"    内容: {preview}")
    print()
    
    # 4. 展示训练时的处理流程
    print("4. 训练时的处理流程")
    print("-" * 80)
    print("""
训练时的处理步骤：
1. 加载JSONL文件，每行是一个训练样本
2. PreprocessedMultiModalDataset 预处理：
   - 提取图片（从base64或路径）
   - 解码图片并缓存到内存
   - 限制每个样本的图片数量（默认最多3张）
   
3. MultiModalDataCollator 批处理时：
   - 将 messages 转换为 Qwen VL 格式
   - 使用 processor.apply_chat_template() 转换为文本
   - 使用 processor() 处理文本和图片，生成：
     * input_ids: token化的文本
     * attention_mask: 注意力掩码
     * pixel_values: 图片的像素值
     * image_grid_thw: 图片网格信息
   - 创建 labels（mask prompt部分，只训练response部分）
   
4. 最终输入模型的格式：
   - input_ids: [batch_size, seq_len] - token化的文本序列
   - attention_mask: [batch_size, seq_len] - 注意力掩码
   - labels: [batch_size, seq_len] - 训练标签（-100表示不计算loss）
   - pixel_values: [batch_size, num_images, C, H, W] - 图片像素值
   - image_grid_thw: [batch_size, num_images, 3] - 图片网格信息
""")
    
    print("=" * 80)


def main():
    # 默认数据路径
    default_data_path = trainer_dir.parent / "dataset" / "processed" / "sft_train_final.jsonl"
    
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        data_path = str(default_data_path)
    
    if not Path(data_path).exists():
        print(f"错误: 数据文件不存在: {data_path}")
        print(f"\n使用方法:")
        print(f"  python {sys.argv[0]} <数据文件路径> [样本索引]")
        print(f"\n示例:")
        print(f"  python {sys.argv[0]} {default_data_path} 0")
        return
    
    index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    print(f"加载数据文件: {data_path}")
    print(f"样本索引: {index}")
    print()
    
    sample = load_sample(data_path, index)
    if sample is None:
        print(f"错误: 无法加载索引为 {index} 的样本")
        return
    
    show_sample_structure(sample)


if __name__ == "__main__":
    main()
