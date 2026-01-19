#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RL Trainer for MAI-UI Models using PPO

This script fine-tunes an SFT model using Reinforcement Learning (PPO)
by interacting with a live Android environment.

Author: Damon Li
Date: 2026-01-19
"""

import os
import argparse
import torch
from trl import PPOConfig, PPOTrainer, AutoModelForCausalLMWithValueHead
from transformers import AutoTokenizer
from android_env.wrappers import GymWrapper

def main(args):
    # 1. PPO Configuration
    ppo_config = PPOConfig(
        p_steps=args.ppo_steps,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        adap_kl_ctrl=True,
        target_kl=0.1,
    )

    # 2. Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(args.sft_model_path)
    model = AutoModelForCausalLMWithValueHead.from_pretrained(
        args.sft_model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    # 3. Initialize PPO Trainer
    ppo_trainer = PPOTrainer(
        config=ppo_config,
        model=model,
        ref_model=None, # Use the same model for reference
        tokenizer=tokenizer,
    )

    # 4. Initialize Android Environment
    # This requires a running Android emulator or device
    env = GymWrapper(
        env=AndroidEnv(
            avd_name=args.avd_name,
            task_path=args.task_path,
        )
    )

    # 5. RL Training Loop
    print("Starting RL training...")
    for epoch in range(args.num_epochs):
        obs = env.reset()
        done = False
        while not done:
            # Get action from the model
            # This part needs a custom generation function to format the prompt
            # and parse the model's output into an action.
            prompt = format_prompt(obs)
            query_tensor = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
            response_tensor = ppo_trainer.generate(query_tensor, **generation_kwargs)
            action = parse_action(tokenizer.decode(response_tensor[0]))

            # Execute action in the environment
            next_obs, reward, done, info = env.step(action)

            # PPO step
            stats = ppo_trainer.step([query_tensor], [response_tensor], [torch.tensor(reward)])
            
            obs = next_obs

        print(f"Epoch {epoch+1} completed.")

    # 6. Save the final model
    ppo_trainer.save_model(args.output_dir)
    print(f"RL training completed. Model saved to {args.output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sft_model_path", type=str, required=True, help="Path to the SFT fine-tuned model.")
    parser.add_argument("--output_dir", type=str, default="./mai-ui-2b-rl", help="Directory to save the RL fine-tuned model.")
    parser.add_argument("--avd_name", type=str, default="pixel_2", help="Name of the Android Virtual Device.")
    parser.add_argument("--task_path", type=str, required=True, help="Path to the AndroidEnv task file.")
    parser.add_argument("--num_epochs", type=int, default=10, help="Number of training epochs.")
    parser.add_argument("--ppo_steps", type=int, default=256, help="Number of PPO steps.")
    parser.add_argument("--batch_size", type=int, default=4, help="PPO batch size.")
    parser.add_argument("--learning_rate", type=float, default=1.41e-5, help="Learning rate.")

    args = parser.parse_args()
    main(args)
