#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Evaluation Script for MAI-UI Models

This script evaluates a fine-tuned MAI-UI model on a specified benchmark,
 such as a subset of AndroidWorld or a custom task set.

Author: Damon Li
Date: 2026-01-19
"""

import argparse
from tqdm import tqdm
from android_env.wrappers import GymWrapper
from transformers import AutoModelForCausalLM, AutoTokenizer

def run_evaluation(args):
    # 1. Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    model = AutoModelForCausalLM.from_pretrained(args.model_path, device_map="auto")

    # 2. Initialize environment
    env = GymWrapper(
        env=AndroidEnv(
            avd_name=args.avd_name,
            task_path=args.task_path,
        )
    )

    # 3. Evaluation loop
    success_count = 0
    for i in tqdm(range(env.num_tasks), desc="Evaluating Tasks"):
        obs = env.reset()
        done = False
        while not done:
            # This part needs a custom generation function similar to the RL trainer
            prompt = format_prompt(obs)
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            outputs = model.generate(**inputs, max_new_tokens=100)
            action_str = tokenizer.decode(outputs[0], skip_special_tokens=True)
            action = parse_action(action_str)

            next_obs, reward, done, info = env.step(action)
            obs = next_obs

        if reward == 1: # Assuming reward of 1 indicates success
            success_count += 1

    # 4. Report results
    success_rate = (success_count / env.num_tasks) * 100
    print(f"\nEvaluation completed.")
    print(f"Tasks: {env.num_tasks}")
    print(f"Successes: {success_count}")
    print(f"Success Rate: {success_rate:.2f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True, help="Path to the fine-tuned model.")
    parser.add_argument("--avd_name", type=str, default="pixel_2", help="Name of the Android Virtual Device.")
    parser.add_argument("--task_path", type=str, required=True, help="Path to the evaluation task file (benchmark).")

    args = parser.parse_args()
    run_evaluation(args)
