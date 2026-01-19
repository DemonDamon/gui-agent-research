#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SFT Trainer for MAI-UI Models.

This script fine-tunes a pre-trained MAI-UI model using trajectory-based SFT data,
with configuration-driven training and proper prompt/response formatting.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import torch
import yaml
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    TrainingArguments,
    Trainer,
)


def load_config(config_path: str) -> dict:
    """Load YAML configuration file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def merge_args_with_config(args: argparse.Namespace, config: dict) -> dict:
    """Merge CLI arguments with config, CLI takes precedence."""
    merged = config.copy()
    
    # Model config
    if args.model_name_or_path:
        merged["model"]["path"] = args.model_name_or_path
    if args.output_dir:
        merged["training"]["output_dir"] = args.output_dir
    
    # Data config
    if args.data_path:
        merged["data"]["path"] = args.data_path
    
    # Training config
    if args.max_length:
        merged["training"]["max_length"] = args.max_length
    if args.num_train_epochs:
        merged["training"]["num_train_epochs"] = args.num_train_epochs
    if args.per_device_train_batch_size:
        merged["training"]["per_device_train_batch_size"] = args.per_device_train_batch_size
    if args.learning_rate:
        merged["training"]["learning_rate"] = args.learning_rate
    if args.save_steps:
        merged["training"]["save_steps"] = args.save_steps
    
    return merged


def tokenize_function(examples, tokenizer, max_length: int):
    """Tokenize examples with proper prompt/response masking."""
    prompts = examples["prompt"]
    responses = examples["response"]
    
    # Combine prompt and response
    texts = [f"{prompt}{response}" for prompt, response in zip(prompts, responses)]
    
    # Tokenize
    tokenized = tokenizer(
        texts,
        truncation=True,
        padding="max_length",
        max_length=max_length,
        return_tensors=None,
    )
    
    # Create labels: mask prompt tokens with -100, keep response tokens
    labels = []
    for i, text in enumerate(texts):
        prompt_len = len(tokenizer.encode(prompts[i], add_special_tokens=False))
        response_len = len(tokenizer.encode(responses[i], add_special_tokens=False))
        
        label = [-100] * prompt_len + tokenized["input_ids"][i][prompt_len : prompt_len + response_len]
        
        # Pad to max_length
        while len(label) < max_length:
            label.append(-100)
        
        labels.append(label[:max_length])
    
    tokenized["labels"] = labels
    return tokenized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, help="Path to sft_config.yaml")
    parser.add_argument("--model_name_or_path", type=str, help="Pre-trained model name or path")
    parser.add_argument("--data_path", type=str, help="Path to SFT training data (JSONL file)")
    parser.add_argument("--output_dir", type=str, help="Directory to save the fine-tuned model")
    parser.add_argument("--max_length", type=int, help="Maximum sequence length")
    parser.add_argument("--num_train_epochs", type=int, help="Number of training epochs")
    parser.add_argument("--per_device_train_batch_size", type=int, help="Batch size per device")
    parser.add_argument("--learning_rate", type=float, help="Learning rate")
    parser.add_argument("--save_steps", type=int, help="Save checkpoint every X steps")
    args = parser.parse_args()
    
    # Load config
    if args.config:
        config = load_config(args.config)
    else:
        # Default config if no file provided
        config = {
            "model": {"path": "Tongyi-MAI/MAI-UI-2B"},
            "data": {"path": None},
            "training": {
                "output_dir": "./mai-ui-2b-sft",
                "max_length": 2048,
                "num_train_epochs": 3,
                "per_device_train_batch_size": 1,
                "gradient_accumulation_steps": 8,
                "learning_rate": 2.0e-5,
                "logging_steps": 10,
                "save_steps": 500,
                "warmup_steps": 100,
            },
        }
    
    # Merge CLI args
    config = merge_args_with_config(args, config)
    
    # Validate required fields
    model_path = config["model"]["path"]
    data_path = config["data"]["path"]
    if not data_path:
        raise ValueError("Data path must be provided via --data_path or config file")
    
    output_dir = config["training"]["output_dir"]
    max_length = config["training"]["max_length"]
    
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    
    # Load dataset
    dataset = load_dataset("json", data_files=data_path, split="train")
    
    # Tokenize
    def tokenize_fn(examples):
        return tokenize_function(examples, tokenizer, max_length)
    
    tokenized_dataset = dataset.map(tokenize_fn, batched=True, remove_columns=dataset.column_names)
    
    # Set up training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        num_train_epochs=config["training"]["num_train_epochs"],
        per_device_train_batch_size=config["training"]["per_device_train_batch_size"],
        gradient_accumulation_steps=config["training"].get("gradient_accumulation_steps", 1),
        learning_rate=config["training"]["learning_rate"],
        logging_steps=config["training"]["logging_steps"],
        save_steps=config["training"]["save_steps"],
        save_total_limit=2,
        logging_dir=os.path.join(output_dir, "logs"),
        bf16=True,
        warmup_steps=config["training"].get("warmup_steps", 0),
        report_to="none",
    )
    
    # Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    
    # Start training
    print("Starting SFT training...")
    trainer.train()
    
    # Save the final model
    trainer.save_model(output_dir)
    print(f"SFT training completed. Model saved to {output_dir}")


if __name__ == "__main__":
    main()
