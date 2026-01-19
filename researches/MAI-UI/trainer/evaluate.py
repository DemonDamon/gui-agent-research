#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Evaluation script for MAI-UI Models

This script evaluates a trained MAI-UI model on a given benchmark task set.
It includes the Zoom-In strategy for improved grounding accuracy.

Author: Damon Li
Date: 2026-01-19
"""

import argparse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from android_env.wrappers import GymWrapper
from PIL import Image

def predict_with_zoom_in(model, tokenizer, image, instruction):
    """
    Predicts coordinates using the two-pass Zoom-In strategy.
    """
    # First pass: Coarse prediction
    prompt_1 = f"Instruction: {instruction}\n<image>" # Placeholder
    inputs_1 = tokenizer(prompt_1, return_tensors="pt").to(model.device)
    outputs_1 = model.generate(**inputs_1)
    coarse_coords = parse_coordinates(tokenizer.decode(outputs_1[0]))

    # Crop image based on coarse coordinates
    width, height = image.size
    crop_box = (
        max(0, coarse_coords[0] - width / 4),
        max(0, coarse_coords[1] - height / 4),
        min(width, coarse_coords[0] + width / 4),
        min(height, coarse_coords[1] + height / 4),
    )
    zoomed_image = image.crop(crop_box).resize((width, height))

    # Second pass: Refined prediction
    prompt_2 = f"Instruction: {instruction}\n<image>" # Placeholder with zoomed_image
    inputs_2 = tokenizer(prompt_2, return_tensors="pt").to(model.device)
    outputs_2 = model.generate(**inputs_2)
    refined_coords_local = parse_coordinates(tokenizer.decode(outputs_2[0]))

    # Convert local coordinates back to original image space
    refined_coords_global = (
        crop_box[0] + refined_coords_local[0] * (crop_box[2] - crop_box[0]) / width,
        crop_box[1] + refined_coords_local[1] * (crop_box[3] - crop_box[1]) / height,
    )

    return refined_coords_global

def main(args):
    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    model = AutoModelForCausalLM.from_pretrained(args.model_path)
    env = GymWrapper(AndroidEnv(avd_name=args.avd_name, task_path=args.task_path))

    obs = env.reset()
    done = False
    while not done:
        screenshot = Image.fromarray(obs["pixels"])
        instruction = obs["instruction"]

        # Model decides action type
        action_type = "ui_action" # Placeholder

        if action_type == "ui_action":
            if args.use_zoom_in:
                coords = predict_with_zoom_in(model, tokenizer, screenshot, instruction)
                action = {"action_type": "CLICK", "touch_position": coords}
            else:
                # Standard prediction
                pass
        elif action_type == "mcp_call":
            # Logic to generate and execute MCP tool call
            pass
        elif action_type == "ask_user":
            # Logic to ask the user for more information
            pass

        next_obs, reward, done, info = env.step(action)
        obs = next_obs

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--avd_name", type=str, default="pixel_2")
    parser.add_argument("--task_path", type=str, required=True)
    parser.add_argument("--use_zoom_in", action="store_true")
    args = parser.parse_args()
    main(args)
