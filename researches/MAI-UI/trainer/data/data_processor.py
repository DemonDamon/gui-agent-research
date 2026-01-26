#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Processor for MAI-UI Training with Qwen3-VL Format.

This module converts trajectory.jsonl to Qwen3-VL compatible training format:
- Each step becomes a separate training sample
- Images are referenced via image_url format (path-based, not base64)
- First step: image + instruction + assistant output
- Subsequent steps: image + instruction + history chain + assistant output

Usage:
    python data_processor.py --trajectory trajectory.jsonl --output sft_train.jsonl
    python data_processor.py --trajectory_dir dataset/ --output sft_train.jsonl

Author: Damon Li
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Generator


# =============================================================================
# System Prompt (imported or fallback)
# =============================================================================

# Try to import official MAI-UI prompt from multiple sources
USE_OFFICIAL_PROMPT = False
MAI_MOBILE_SYS_PROMPT_ASK_USER_MCP = None

# Priority 1: Import from trainer/prompts/maiui_official_prompts.py
prompts_file = Path(__file__).parent.parent / "prompts" / "maiui_official_prompts.py"
if prompts_file.exists():
    try:
        prompts_dir = prompts_file.parent
        if str(prompts_dir) not in sys.path:
            sys.path.insert(0, str(prompts_dir))
        from maiui_official_prompts import MAI_MOBILE_SYS_PROMPT_ASK_USER_MCP  # type: ignore[import]  # pyright: ignore
        USE_OFFICIAL_PROMPT = True
    except ImportError:
        pass

# Priority 2: Import from mobile_world
if not USE_OFFICIAL_PROMPT:
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from mobile_world.agents.utils.prompts import MAI_MOBILE_SYS_PROMPT_ASK_USER_MCP
        USE_OFFICIAL_PROMPT = True
    except ImportError:
        pass

# Get system prompt
if USE_OFFICIAL_PROMPT and MAI_MOBILE_SYS_PROMPT_ASK_USER_MCP is not None:
    GUI_AGENT_SYSTEM_PROMPT = MAI_MOBILE_SYS_PROMPT_ASK_USER_MCP.render(tools="")
else:
    # Fallback prompt
    GUI_AGENT_SYSTEM_PROMPT = """You are a GUI agent. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task. 

## Output Format
For each function call, return the thinking process in <thinking> </thinking> tags, and a json object with function name and arguments within <tool_call></tool_call> XML tags:
```
<thinking>
...
</thinking>
<tool_call>
{"name": "mobile_use", "arguments": <args-json-object>}
</tool_call>
```

## Action Space

{"action": "click", "coordinate": [x, y]}
{"action": "long_press", "coordinate": [x, y]}
{"action": "type", "text": ""}
{"action": "swipe", "direction": "up or down or left or right", "coordinate": [x, y]} # "coordinate" is optional. Use the "coordinate" if you want to swipe a specific UI element.
{"action": "open", "text": "app_name"}
{"action": "drag", "start_coordinate": [x1, y1], "end_coordinate": [x2, y2]}
{"action": "system_button", "button": "button_name"} # Options: back, home, menu, enter 
{"action": "wait"}
{"action": "terminate", "status": "success or fail"} 
{"action": "answer", "text": "xxx"} # Use escape characters \\', \\", and \\n in text part to ensure we can parse the text in normal python string format.
{"action": "AWAKE", "text": "app_name"} # Open an app directly by its name.
{"action": "INFO", "text": "xxx"} # Ask user for more info.
{"action": "ask_user", "text": "xxx"} # you can ask user for more information to complete the task.
{"action": "double_click", "coordinate": [x, y]}

## Behavior Rules
1. Track your previous action. If it was a swipe, do NOT swipe in the same direction more than 5 times consecutively.
2. If you swipe in the same direction 2-3 times but the screen content doesn't change significantly (likely reached the boundary), try swiping in the **opposite direction**.
3. Different apps may require different swipe directions to view history or more content. Adjust flexibly based on actual screen feedback.
4. Strictly follow the user's instructions. If you have had a conversation with the user, prioritize the **latest instruction**.

## Note
- **IMPORTANT: When the user asks to open an app (by name like "微信", "高德地图", "淘宝", etc.), ALWAYS use the `open` action with the app name first!** This is the fastest way to launch apps.
- Example: If user says "打开微信", use `{"action": "open", "text": "微信"}` instead of navigating manually.
- Write a small plan and finally summarize your next action (with its target element) in one sentence in <thinking></thinking> part."""


# =============================================================================
# Data Loading Functions
# =============================================================================

def load_trajectory(trajectory_file: str) -> list[dict]:
    """Load trajectory data from JSONL file.
    
    Args:
        trajectory_file: Path to trajectory.jsonl file.
        
    Returns:
        List of step dictionaries.
    """
    steps = []
    with open(trajectory_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                step = json.loads(line)
                steps.append(step)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line {line_num}: {e}")
    return steps


# =============================================================================
# Image Path Resolution
# =============================================================================

def resolve_image_path(
    screenshot_path: str,
    trajectory_dir: Path,
    image_base_dir: Path | None = None,
) -> str | None:
    """Resolve screenshot path to absolute or relative path.
    
    Args:
        screenshot_path: Original screenshot path from trajectory.
        trajectory_dir: Directory containing the trajectory.jsonl file.
        image_base_dir: Optional base directory for images.
        
    Returns:
        Resolved path string, or None if file doesn't exist.
    """
    if not screenshot_path:
        return None
    
    path = Path(screenshot_path)
    
    # If already absolute, check existence
    if path.is_absolute():
        if path.exists():
            return str(path)
        return None
    
    # Try relative to image_base_dir
    if image_base_dir:
        full_path = image_base_dir / path
        if full_path.exists():
            return str(full_path)
        # Try just the filename
        full_path = image_base_dir / path.name
        if full_path.exists():
            return str(full_path)
    
    # Try relative to trajectory directory
    full_path = trajectory_dir / path
    if full_path.exists():
        return str(full_path)
    
    # Try just the filename relative to trajectory directory
    full_path = trajectory_dir / path.name
    if full_path.exists():
        return str(full_path)
    
    # Return original path (may not exist)
    return screenshot_path


def get_image_filename(screenshot_path: str) -> str | None:
    """Extract just the filename from screenshot path.
    
    Args:
        screenshot_path: Original screenshot path from trajectory.
        
    Returns:
        Just the filename (e.g., "step_001.png"), or None if empty.
    """
    if not screenshot_path:
        return None
    return Path(screenshot_path).name


# =============================================================================
# History Formatting
# =============================================================================

def format_history_chain(
    steps: list[dict],
    current_index: int,
    max_history: int | None = None,
) -> str:
    """Format previous steps as history chain text.
    
    Args:
        steps: List of all steps.
        current_index: Current step index (0-based).
        max_history: Maximum number of history steps to include. None = all.
        
    Returns:
        Formatted history text, or empty string if no history.
    """
    if current_index <= 0:
        return ""
    
    # Get history steps (all steps before current)
    history_steps = steps[:current_index]
    
    # Limit history if specified
    if max_history is not None and len(history_steps) > max_history:
        history_steps = history_steps[-max_history:]
    
    if not history_steps:
        return ""
    
    history_lines = ["\nPrevious actions:"]
    for step in history_steps:
        thinking = step.get("thinking", "")
        action = step.get("action", {})
        
        if thinking:
            history_lines.append(f"- {thinking}")
        if action:
            action_json = json.dumps(action, ensure_ascii=False)
            history_lines.append(f"  Action: {action_json}")
    
    return "\n".join(history_lines)


# =============================================================================
# Sample Building Functions
# =============================================================================

def build_user_content(
    image_path: str | None,
    instruction: str,
    history_text: str,
) -> list[dict]:
    """Build user message content for Qwen3-VL format.
    
    Args:
        image_path: Path to screenshot image.
        instruction: Task instruction.
        history_text: Formatted history chain text.
        
    Returns:
        List of content items.
    """
    content = []
    
    # Add image first (if exists)
    if image_path:
        content.append({
            "type": "image_url",
            "image_url": image_path
        })
    
    # Build text content
    text = instruction
    if history_text:
        text += history_text
    
    content.append({
        "type": "text",
        "text": text
    })
    
    return content


def build_assistant_content(thinking: str, action: dict) -> list[dict]:
    """Build assistant message content.
    
    Args:
        thinking: The thinking process text.
        action: The action dictionary.
        
    Returns:
        List of content items.
    """
    # Format response as "Thought: ... Action: {...}"
    action_json = json.dumps(action, ensure_ascii=False)
    response_text = f"{thinking}\nAction: {action_json}"
    
    return [{"type": "text", "text": response_text}]


def build_training_sample(
    step: dict,
    step_index: int,
    all_steps: list[dict],
    trajectory_dir: Path,
    system_prompt: str,
    image_base_dir: Path | None = None,
    max_history: int | None = None,
) -> dict | None:
    """Build a single training sample for a step.
    
    Args:
        step: Current step data.
        step_index: Index of current step (0-based).
        all_steps: List of all steps in trajectory.
        trajectory_dir: Directory containing trajectory file.
        system_prompt: System prompt text.
        image_base_dir: Optional base directory for images.
        max_history: Maximum history steps to include.
        
    Returns:
        Training sample dict, or None if image is missing.
    """
    # Extract step data
    instruction = step.get("instruction", "")
    thinking = step.get("thinking", "")
    action = step.get("action", {})
    screenshot_path = step.get("screenshot_path", "")
    
    # Use just the filename for image path (since output will be in same dir)
    image_filename = get_image_filename(screenshot_path)
    
    # Verify image exists (use full path for validation)
    full_image_path = resolve_image_path(
        screenshot_path,
        trajectory_dir,
        image_base_dir,
    )
    
    # Format history chain (empty for first step)
    history_text = format_history_chain(all_steps, step_index, max_history)
    
    # Build user content (use filename for image_url)
    user_content = build_user_content(image_filename, instruction, history_text)
    
    # Build assistant content
    assistant_content = build_assistant_content(thinking, action)
    
    # Build messages
    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": system_prompt}]
        },
        {
            "role": "user",
            "content": user_content
        },
        {
            "role": "assistant",
            "content": assistant_content
        }
    ]
    
    # Build metadata (use full path for validation reference, but filename in messages)
    metadata = {
        "source": str(trajectory_dir),
        "step_index": step.get("step_index", step_index + 1),
        "action_type": step.get("action_type", action.get("action", "unknown")),
        "success": step.get("success", True),
        "timestamp": step.get("timestamp"),
        "screenshot_path": image_filename,  # Store filename only
    }
    
    return {
        "messages": messages,
        "metadata": metadata
    }


# =============================================================================
# Main Processing Functions
# =============================================================================

def process_trajectory_to_qwen3vl_format(
    trajectory_file: str,
    output_file: str | None = None,
    system_prompt: str | None = None,
    image_base_dir: str | None = None,
    max_history: int | None = None,
    skip_missing_images: bool = True,
) -> dict[str, int]:
    """Convert trajectory.jsonl to Qwen3-VL training format.
    
    Args:
        trajectory_file: Path to trajectory.jsonl file.
        output_file: Output JSONL file path.
        system_prompt: System prompt (uses default if None).
        image_base_dir: Base directory for resolving image paths.
        max_history: Maximum history steps to include (None = all).
        skip_missing_images: Whether to skip steps with missing images.
        
    Returns:
        Statistics dictionary with counts.
    """
    # Use default system prompt if not provided
    if system_prompt is None:
        system_prompt = GUI_AGENT_SYSTEM_PROMPT
    
    # Load trajectory
    steps = load_trajectory(trajectory_file)
    
    if not steps:
        return {"total_steps": 0, "processed": 0, "skipped": 0}
    
    # Get directories
    trajectory_path = Path(trajectory_file)
    trajectory_dir = trajectory_path.parent
    image_base = Path(image_base_dir) if image_base_dir else None
    
    # Set default output file if not provided
    if output_file is None:
        output_file = str(trajectory_dir / "sft_train.jsonl")
    
    # Process each step
    samples = []
    stats = {
        "total_steps": len(steps),
        "processed": 0,
        "skipped": 0,
        "action_types": {},
    }
    
    for i, step in enumerate(steps):
        screenshot_path = step.get("screenshot_path", "")
        
        # Verify image exists (use full path for validation)
        full_image_path = resolve_image_path(
            screenshot_path,
            trajectory_dir,
            image_base,
        )
        
        if skip_missing_images and screenshot_path and not full_image_path:
            stats["skipped"] += 1
            continue
        
        sample = build_training_sample(
            step=step,
            step_index=i,
            all_steps=steps,
            trajectory_dir=trajectory_dir,
            system_prompt=system_prompt,
            image_base_dir=image_base,
            max_history=max_history,
        )
        
        if sample:
            
            samples.append(sample)
            stats["processed"] += 1
            
            # Track action types
            action_type = sample["metadata"].get("action_type", "unknown")
            stats["action_types"][action_type] = stats["action_types"].get(action_type, 0) + 1
        else:
            stats["skipped"] += 1
    
    # Write output
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    return stats


def process_trajectory_directory(
    trajectory_dir: str,
    output_file: str | None = None,
    system_prompt: str | None = None,
    max_history: int | None = None,
    skip_missing_images: bool = True,
) -> dict[str, Any]:
    """Process all trajectory.jsonl files in a directory.
    
    Args:
        trajectory_dir: Directory containing trajectory folders.
        output_file: Output JSONL file path (default: each trajectory's directory).
        system_prompt: System prompt (uses default if None).
        max_history: Maximum history steps to include.
        skip_missing_images: Whether to skip steps with missing images.
        
    Returns:
        Combined statistics dictionary.
    """
    if system_prompt is None:
        system_prompt = GUI_AGENT_SYSTEM_PROMPT
    
    trajectory_path = Path(trajectory_dir)
    
    # Find all trajectory.jsonl files
    trajectory_files = list(trajectory_path.rglob("trajectory.jsonl"))
    
    if not trajectory_files:
        print(f"No trajectory.jsonl files found in {trajectory_dir}")
        return {"total_trajectories": 0, "total_samples": 0}
    
    print(f"Found {len(trajectory_files)} trajectory files")
    
    # Process all trajectories
    all_samples = []
    total_stats = {
        "total_trajectories": len(trajectory_files),
        "total_steps": 0,
        "processed": 0,
        "skipped": 0,
        "action_types": {},
    }
    
    for traj_file in trajectory_files:
        print(f"Processing: {traj_file}")
        
        # Load and process trajectory
        steps = load_trajectory(str(traj_file))
        if not steps:
            continue
        
        traj_dir = traj_file.parent
        
        # Determine output file for this trajectory
        if output_file is None:
            # Output to each trajectory's directory
            traj_output_file = str(traj_dir / "sft_train.jsonl")
        else:
            # Use provided output file (combine all trajectories)
            traj_output_file = output_file
        
        traj_samples = []
        
        for i, step in enumerate(steps):
            screenshot_path = step.get("screenshot_path", "")
            
            # Verify image exists (use full path for validation)
            full_image_path = resolve_image_path(
                screenshot_path,
                traj_dir,
                None,
            )
            
            if skip_missing_images and screenshot_path and not full_image_path:
                total_stats["skipped"] += 1
                continue
            
            sample = build_training_sample(
                step=step,
                step_index=i,
                all_steps=steps,
                trajectory_dir=traj_dir,
                system_prompt=system_prompt,
                image_base_dir=None,
                max_history=max_history,
            )
            
            if sample:
                traj_samples.append(sample)
                all_samples.append(sample)
                total_stats["processed"] += 1
                
                action_type = sample["metadata"].get("action_type", "unknown")
                total_stats["action_types"][action_type] = (
                    total_stats["action_types"].get(action_type, 0) + 1
                )
            else:
                total_stats["skipped"] += 1
        
        total_stats["total_steps"] += len(steps)
        
        # Write output for this trajectory (if output_file is None, write to each dir)
        if output_file is None:
            output_path = Path(traj_output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(traj_output_file, "w", encoding="utf-8") as f:
                for sample in traj_samples:
                    f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            print(f"  Saved {len(traj_samples)} samples to: {traj_output_file}")
    
    # Write combined output if output_file was provided
    if output_file is not None:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            for sample in all_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        print(f"\nTotal samples: {len(all_samples)}")
        print(f"Saved to: {output_file}")
    
    return total_stats


# =============================================================================
# CLI Entry Point
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert trajectory.jsonl to Qwen3-VL training format"
    )
    parser.add_argument(
        "--trajectory", "-t",
        type=str,
        help="Path to single trajectory.jsonl file"
    )
    parser.add_argument(
        "--trajectory_dir", "-d",
        type=str,
        help="Directory containing trajectory folders"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output JSONL file path (default: same dir as trajectory)"
    )
    parser.add_argument(
        "--max_history",
        type=int,
        default=None,
        help="Maximum number of history steps (default: all)"
    )
    parser.add_argument(
        "--image_base_dir",
        type=str,
        default=None,
        help="Base directory for resolving image paths"
    )
    parser.add_argument(
        "--no_skip_missing",
        action="store_true",
        help="Don't skip steps with missing images"
    )
    
    args = parser.parse_args()
    
    if not args.trajectory and not args.trajectory_dir:
        parser.error("Either --trajectory or --trajectory_dir is required")
    
    skip_missing = not args.no_skip_missing
    
    if args.trajectory:
        # Process single trajectory
        # Determine output file path
        if args.output is None:
            trajectory_path = Path(args.trajectory)
            output_path = trajectory_path.parent / "sft_train.jsonl"
        else:
            output_path = Path(args.output)
        
        stats = process_trajectory_to_qwen3vl_format(
            trajectory_file=args.trajectory,
            output_file=str(output_path) if args.output is None else args.output,
            image_base_dir=args.image_base_dir,
            max_history=args.max_history,
            skip_missing_images=skip_missing,
        )
        print(f"Processed: {stats['processed']}, Skipped: {stats['skipped']}")
        print(f"Action types: {stats['action_types']}")
        print(f"Saved to: {output_path}")
    else:
        # Process directory
        stats = process_trajectory_directory(
            trajectory_dir=args.trajectory_dir,
            output_file=args.output,
            max_history=args.max_history,
            skip_missing_images=skip_missing,
        )
        print(f"\nFinal stats: {stats}")


if __name__ == "__main__":
    main()
