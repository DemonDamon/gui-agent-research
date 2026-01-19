#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SFT Trainer for MAI-UI Models

This script fine-tunes a pre-trained MAI-UI model (e.g., 2B version)
using a dataset of GUI trajectories in a supervised fashion.

Author: Damon Li
Date: 2026-01-19
"""

import os
import argparse
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)

def main(args):
    # 1. Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name_or_path,
        torch_dtype=torch.bfloat16, # Use bfloat16 for efficiency
        device_map="auto",
    )

    # 2. Load and preprocess dataset
    dataset = load_dataset("json", data_files=args.data_path)

    def tokenize_function(examples):
        # This function needs to be adapted based on the actual data format
        # It should combine instruction, history, and screenshot info into a single prompt
        return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=args.max_length)

    tokenized_datasets = dataset.map(tokenize_function, batched=True)

    # 3. Set up training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        overwrite_output_dir=True,
        num_train_epochs=args.num_train_epochs,
        per_device_train_batch_size=args.per_device_train_batch_size,
        save_steps=args.save_steps,
        save_total_limit=2,
        logging_dir='./logs',
        logging_steps=10,
        learning_rate=args.learning_rate,
        bf16=True, # Enable bfloat16 training
    )

    # 4. Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        tokenizer=tokenizer,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )

    # 5. Start training
    print("Starting SFT training...")
    trainer.train()

    # 6. Save the final model
    trainer.save_model(args.output_dir)
    print(f"SFT training completed. Model saved to {args.output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", type=str, default="Tongyi-MAI/MAI-UI-2B", help="Pre-trained model name or path.")
    parser.add_argument("--data_path", type=str, required=True, help="Path to the SFT training data (JSON file).")
    parser.add_argument("--output_dir", type=str, default="./mai-ui-2b-sft", help="Directory to save the fine-tuned model.")
    parser.add_argument("--max_length", type=int, default=2048, help="Maximum sequence length.")
    parser.add_argument("--num_train_epochs", type=int, default=3, help="Number of training epochs.")
    parser.add_argument("--per_device_train_batch_size", type=int, default=1, help="Batch size per device.")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate.")
    parser.add_argument("--save_steps", type=int, default=500, help="Save checkpoint every X updates steps.")

    args = parser.parse_args()
    main(args)
