#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Builder for MAI-UI SFT and RL Training

This script provides functionalities to:
1. Collect GUI trajectory data from real devices or emulators.
2. Convert raw trajectory data into a unified format for SFT and RL training.
3. Preprocess and tokenize the data for model consumption.

Author: Damon Li
Date: 2026-01-19
"""

import os
import json
import base64
from PIL import Image
from io import BytesIO

class TrajectoryCollector:
    """Collects GUI interaction trajectories from a device."""

    def __init__(self, device_id):
        self.device_id = device_id
        # Initialize ADB connection
        pass

    def start_collection(self):
        """Starts the data collection process."""
        print("Starting data collection...")
        # Implement logic to record screen, actions, and device state
        pass

    def save_trajectory(self, trajectory, output_path):
        """Saves the collected trajectory to a file."""
        with open(output_path, 'w') as f:
            json.dump(trajectory, f, indent=2)
        print(f"Trajectory saved to {output_path}")

class DataFormatter:
    """Formats raw trajectory data into a structured format for training."""

    def format_sft_data(self, raw_data):
        """Formats data for Supervised Fine-Tuning (SFT)."""
        formatted_data = []
        for entry in raw_data:
            # Implement logic to convert raw log into a structured SFT sample
            # Each sample should contain: instruction, history, screenshot, and ground truth action
            pass
        return formatted_data

    def format_rl_data(self, raw_data):
        """Formats data for Reinforcement Learning (RL)."""
        # RL data format might be similar to SFT but with rewards and terminal states
        pass

    def _encode_image(self, image_path):
        """Encodes an image to a base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

if __name__ == '__main__':
    # Example usage
    collector = TrajectoryCollector(device_id='emulator-5554')
    # collector.start_collection() # This would be an interactive process

    # Example raw data (replace with actual collected data)
    raw_trajectory = [
        {"screenshot": "path/to/screen1.png", "action": {"type": "click", "x": 100, "y": 200}},
        {"screenshot": "path/to/screen2.png", "action": {"type": "swipe", "x1": 100, "y1": 800, "x2": 100, "y2": 200}},
    ]

    formatter = DataFormatter()
    sft_samples = formatter.format_sft_data(raw_trajectory)

    # Save formatted data
    output_dir = 'processed'
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, 'sft_data.json'), 'w') as f:
        json.dump(sft_samples, f, indent=2)

    print("Data building process completed.")
