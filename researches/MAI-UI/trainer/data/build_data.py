#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Building Pipeline for MAI-UI

This script implements the self-evolving data pipeline described in the MAI-UI paper,
including three data sources: rejection-sampled trajectories, manually-annotated trajectories,
and automatic agent rollouts.

Author: Damon Li
Date: 2026-01-19
"""

import os
import json
import random
from tqdm import tqdm

class DataPipeline:
    def __init__(self, config):
        self.config = config
        self.rejection_sampled_pool = []
        self.manual_pool = []
        self.rollout_pool = []

    def collect_manual_trajectories(self, manual_data_path):
        """Load manually annotated trajectories."""
        with open(manual_data_path, 'r') as f:
            self.manual_pool = json.load(f)
        print(f"Loaded {len(self.manual_pool)} manually annotated trajectories.")

    def run_automatic_rollouts(self, agent, env, num_episodes):
        """Generate trajectories using an agent in the environment."""
        for _ in tqdm(range(num_episodes), desc="Running Automatic Rollouts"):
            obs = env.reset()
            done = False
            trajectory = []
            while not done:
                action = agent.get_action(obs)
                next_obs, reward, done, info = env.step(action)
                trajectory.append((obs, action, reward, next_obs, done))
                obs = next_obs
            if reward == 1: # Only add successful trajectories
                self.rollout_pool.append(trajectory)
        print(f"Generated {len(self.rollout_pool)} successful trajectories from rollouts.")

    def run_rejection_sampling(self, agent, env, num_episodes):
        """Generate and filter trajectories using rejection sampling."""
        # This is a simplified implementation. A real implementation would
        # involve more sophisticated filtering based on model scores.
        self.run_automatic_rollouts(agent, env, num_episodes)
        self.rejection_sampled_pool = self.rollout_pool
        print(f"Filtered {len(self.rejection_sampled_pool)} trajectories using rejection sampling.")

    def build_sft_dataset(self, output_path):
        """Combine all data sources to build the SFT dataset."""
        sft_dataset = []
        all_trajectories = self.manual_pool + self.rejection_sampled_pool + self.rollout_pool

        for trajectory in all_trajectories:
            # Convert trajectory to SFT format (e.g., prompt-response pairs)
            # This part needs to be implemented based on the specific data format
            pass

        with open(output_path, 'w') as f:
            json.dump(sft_dataset, f, indent=2)
        print(f"SFT dataset built with {len(sft_dataset)} samples.")

if __name__ == "__main__":
    # This is a conceptual example of how to use the DataPipeline
    # You would need to provide your own agent, environment, and data paths

    # config = ...
    # pipeline = DataPipeline(config)
    # pipeline.collect_manual_trajectories("path/to/manual_data.json")
    # pipeline.run_automatic_rollouts(agent, env, num_episodes=100)
    # pipeline.run_rejection_sampling(agent, env, num_episodes=100)
    # pipeline.build_sft_dataset("path/to/sft_data.json")
    pass
