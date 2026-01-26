#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Data Augmentation for GUI Agent Anti-Loop Training.

This script processes trajectory data to:
1. Add action history to each training sample
2. Generate anti-loop samples (detect repeated actions -> change strategy)
3. Generate ask_user samples when search/scroll fails

Supports two output formats:
- OpenAI messages format (with images) - for VLM training
- Prompt/response format (text only) - for text-only training
"""

from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path
from typing import Any


def load_jsonl(file_path: str) -> list[dict]:
    """Load data from JSONL file."""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def load_trajectory(file_path: str) -> list[dict]:
    """Load trajectory data from JSONL file."""
    return load_jsonl(file_path)


def format_action_history(
    trajectory: list[dict], current_step: int, history_window: int = 5
) -> str:
    """Format action history as a readable string.
    
    Args:
        trajectory: Full trajectory list
        current_step: Current step index (1-based)
        history_window: Number of previous steps to include
    
    Returns:
        Formatted action history string (simple format without brackets)
    """
    if current_step <= 1:
        return "No previous actions."
    
    start_idx = max(0, current_step - 1 - history_window)
    end_idx = current_step - 1
    
    history_lines = []
    for i in range(start_idx, end_idx):
        step = trajectory[i]
        action = step.get("action", {})
        action_type = step.get("action_type", action.get("action", "unknown"))
        
        action_str = _format_single_action(action_type, action)
        history_lines.append(f"- Step {step.get('step_index', i+1)}: {action_str}")
    
    return "\n".join(history_lines) if history_lines else "No previous actions."


def format_action_history_bracketed(
    trajectory: list[dict], current_step: int, history_window: int = 5
) -> str:
    """Format action history with brackets (for injection into messages).
    
    Args:
        trajectory: Full trajectory list
        current_step: Current step index (1-based)
        history_window: Number of previous steps to include
    
    Returns:
        Formatted action history string with brackets
    """
    if current_step <= 1:
        return "\n\n[Action History: No previous actions]"
    
    start_idx = max(0, current_step - 1 - history_window)
    end_idx = current_step - 1
    
    history_lines = ["\n\n[Action History:"]
    for i in range(start_idx, end_idx):
        step = trajectory[i]
        action = step.get("action", {})
        action_type = step.get("action_type", action.get("action", "unknown"))
        
        action_str = _format_single_action(action_type, action)
        history_lines.append(f"  - Step {step.get('step_index', i+1)}: {action_str}")
    
    history_lines.append(f"  - Current: Step {current_step}]")
    
    return "\n".join(history_lines)


def _format_single_action(action_type: str, action: dict) -> str:
    """Format a single action into readable string."""
    if action_type == "click":
        coord = action.get("coordinate", [0, 0])
        if isinstance(coord, list) and len(coord) >= 2:
            return f"click at ({coord[0]:.2f}, {coord[1]:.2f})"
        return "click"
    elif action_type == "type":
        text = action.get("text", "")[:30]
        return f'type "{text}"'
    elif action_type == "swipe":
        direction = action.get("direction", "up")
        return f"swipe {direction}"
    elif action_type == "system_button":
        button = action.get("button", "home")
        return f"press {button}"
    elif action_type == "long_press":
        coord = action.get("coordinate", [0, 0])
        if isinstance(coord, list) and len(coord) >= 2:
            return f"long_press at ({coord[0]:.2f}, {coord[1]:.2f})"
        return "long_press"
    elif action_type == "answer":
        return "answer/terminate"
    elif action_type == "ask_user":
        return "ask_user"
    elif action_type == "wait":
        return "wait"
    else:
        return str(action_type)


def detect_repeated_actions(
    trajectory: list[dict], current_step: int, threshold: int = 3
) -> tuple[bool, str, int]:
    """Detect if the same action has been repeated multiple times.
    
    Returns:
        (is_repeated, action_type, repeat_count)
    """
    if current_step < threshold:
        return False, "", 0
    
    recent_actions = []
    for i in range(max(0, current_step - threshold), current_step):
        action = trajectory[i].get("action", {})
        action_type = trajectory[i].get("action_type", action.get("action", ""))
        recent_actions.append(action_type)
    
    if len(set(recent_actions)) == 1 and recent_actions[0]:
        return True, recent_actions[0], len(recent_actions)
    
    return False, "", 0


# =============================================================================
# Response Generation (for anti-loop samples)
# =============================================================================

def generate_anti_loop_response_simple(action_type: str, repeat_count: int) -> str:
    """Generate assistant response content that breaks the loop (simple format)."""
    
    if action_type == "swipe":
        thinking = (
            f"I have performed {repeat_count} swipe operations consecutively, "
            "but still haven't found the target. Continuing to swipe blindly is inefficient. "
            "I should try other strategies: use search, or ask the user for more information."
        )
        action_json = {
            "action": "ask_user",
            "text": "I've scrolled through multiple screens but haven't found the target. "
                    "Could you tell me: 1) Approximately where is it located? "
                    "2) Are there any keywords I can search for?"
        }
    elif action_type == "click":
        thinking = (
            f"I have clicked {repeat_count} times, but it doesn't seem to produce the expected effect. "
            "The element might not be clickable or the page is loading. I should wait."
        )
        action_json = {"action": "wait"}
    else:
        thinking = (
            f"I have performed the same operation ({action_type}) {repeat_count} times "
            "without achieving the expected result. I should change strategy or ask the user."
        )
        action_json = {
            "action": "ask_user",
            "text": "The current operation doesn't seem to work. Should I try a different approach?"
        }
    
    return f"Thought: {thinking}\nAction: {json.dumps(action_json, ensure_ascii=False)}"


def generate_anti_loop_response_xml(
    action_type: str, repeat_count: int, instruction: str = ""
) -> str:
    """Generate a response that breaks the loop (XML format with thinking/tool_call)."""
    
    if action_type == "swipe":
        return f"""<thinking>
I have performed {repeat_count} swipe operations consecutively, but still haven't found the target. This indicates:
1. The target might not be in the current visible area
2. Continuing to swipe blindly is inefficient
3. I should try other strategies

A better strategy is: use search functionality, or ask the user for more information.
</thinking>
<tool_call>
{{"name": "mobile_use", "arguments": {{"action": "ask_user", "text": "I've scrolled through multiple screens but haven't found the target. Could you tell me: 1) Approximately where is the content you're looking for? 2) Are there any keywords I can search for?"}}}}
</tool_call>"""
    
    elif action_type == "click":
        return f"""<thinking>
I have clicked {repeat_count} times, but it doesn't seem to produce the expected effect. Possible reasons:
1. The element is not clickable or is blocked
2. The page is still loading
3. My click position is inaccurate

I should wait, or try clicking a different position.
</thinking>
<tool_call>
{{"name": "mobile_use", "arguments": {{"action": "wait"}}}}
</tool_call>"""
    
    else:
        return f"""<thinking>
I have performed the same operation ({action_type}) {repeat_count} times without achieving the expected result. I should change strategy or ask the user.
</thinking>
<tool_call>
{{"name": "mobile_use", "arguments": {{"action": "ask_user", "text": "The current operation doesn't seem to work. Should I try a different approach?"}}}}
</tool_call>"""


# =============================================================================
# OpenAI Messages Format Processing (with image support)
# =============================================================================

def inject_history_into_messages(
    messages: list[dict],
    history_text: str
) -> list[dict]:
    """Inject action history text into the user message content.
    
    Preserves image_url and other content types.
    """
    new_messages = copy.deepcopy(messages)
    
    for msg in new_messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            
            if isinstance(content, str):
                msg["content"] = content + history_text
            elif isinstance(content, list):
                # Multi-modal content (text + images)
                text_found = False
                for i in range(len(content) - 1, -1, -1):
                    item = content[i]
                    if isinstance(item, dict) and item.get("type") == "text":
                        item["text"] = item.get("text", "") + history_text
                        text_found = True
                        break
                    elif isinstance(item, str):
                        content[i] = item + history_text
                        text_found = True
                        break
                
                if not text_found:
                    content.append({"type": "text", "text": history_text})
            break
    
    return new_messages


def create_anti_loop_sample_messages(
    base_sample: dict,
    history_window: int = 5,
) -> dict | None:
    """Create an anti-loop sample from a base sample (OpenAI messages format).
    
    Modifies user message to include repeated action history,
    and changes assistant response to break the loop.
    """
    if "messages" not in base_sample:
        return None
    
    new_sample = copy.deepcopy(base_sample)
    messages = new_sample["messages"]
    
    # Generate fake repeated action history
    repeat_count = random.randint(3, 6)
    repeat_action = random.choice(["swipe", "click"])
    
    if repeat_action == "swipe":
        fake_history = "\n\n[Action History:"
        for i in range(repeat_count):
            fake_history += f"\n  - Step {i+1}: swipe up"
        fake_history += f"\n  - Current: Step {repeat_count + 1}]"
    else:
        fake_history = "\n\n[Action History:"
        for i in range(repeat_count):
            fake_history += f"\n  - Step {i+1}: click at (0.50, 0.50)"
        fake_history += f"\n  - Current: Step {repeat_count + 1}]"
    
    # Inject history into user message
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                msg["content"] = content + fake_history
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        item["text"] = item.get("text", "") + fake_history
                        break
            break
    
    # Replace assistant response
    for msg in messages:
        if msg.get("role") == "assistant":
            msg["content"] = generate_anti_loop_response_simple(repeat_action, repeat_count)
            break
    
    return new_sample


def create_upload_after_click_samples(
    base_sample: dict,
    variation_idx: int = 0,
) -> dict | None:
    """Create POSITIVE training samples for post-upload actions (OpenAI messages format).
    
    This function creates samples that teach the model to click on the uploaded file
    (not the blue plus button) after a successful upload. Uses contrastive reasoning
    in the thought process to reinforce the correct behavior.
    
    IMPORTANT: This function ONLY generates positive samples (correct actions).
    Negative samples (incorrect actions) are harmful for SFT training because
    the model will learn to output wrong action coordinates.
    
    Args:
        base_sample: Base sample with upload success scenario
        variation_idx: Index for creating different thinking variations (0-4)
    
    Returns:
        Enhanced sample dict or None
    """
    if "messages" not in base_sample:
        return None
    
    new_sample = copy.deepcopy(base_sample)
    messages = new_sample["messages"]
    
    # Find assistant message
    assistant_msg = None
    for msg in messages:
        if msg.get("role") == "assistant":
            assistant_msg = msg
            break
    
    if not assistant_msg:
        return None
    
    # Check if this is an upload success scenario
    assistant_content = assistant_msg.get("content", "")
    if isinstance(assistant_content, str):
        if "upload" not in assistant_content.lower() and "上传" not in assistant_content:
            return None
    elif isinstance(assistant_content, list):
        text_content = " ".join(
            item.get("text", "") for item in assistant_content 
            if isinstance(item, dict) and item.get("type") == "text"
        )
        if "upload" not in text_content.lower() and "上传" not in text_content:
            return None
    
    # Correct: Click on the uploaded file (coordinates in center-upper area)
    correct_coord = [0.4844844844844845, 0.26926926926926925]  # Reference from step_015
    
    # Multiple thinking variations with CONTRASTIVE REASONING
    # Each variation explicitly mentions what NOT to click (the blue plus button)
    thinking_variations = [
        (
            "Thought: The file has been uploaded successfully. "
            "To share it, I need to click on the uploaded file itself (in the file list), "
            "NOT the blue plus button in the bottom right corner. "
            "The plus button is for uploading new files, not for sharing existing ones."
        ),
        (
            "Thought: Upload complete! Now I should click on the file item I just uploaded "
            "to access the share options. I must NOT click the blue plus button at the bottom - "
            "that would start a new upload instead of sharing this file."
        ),
        (
            "Thought: The file upload is finished. To continue with sharing, "
            "I need to select the uploaded file by clicking on it in the file list area. "
            "Important: The blue plus button in the corner is for adding more files, "
            "not for sharing. I should click the file item itself."
        ),
        (
            "Thought: File uploaded successfully. Next step is to click on the file entry "
            "in the list to open sharing options. Note: I should avoid clicking the "
            "prominent blue plus button at the bottom right - it's for new uploads only."
        ),
        (
            "Thought: 文件上传成功。现在我需要点击文件列表中的文件项来分享它，"
            "而不是点击右下角的蓝色加号按钮。蓝色加号是用来上传新文件的，"
            "要分享已上传的文件必须点击文件本身。"
        ),
    ]
    
    thinking = thinking_variations[variation_idx % len(thinking_variations)]
    
    action_json = {
        "action": "click",
        "coordinate": correct_coord
    }
    
    # Update assistant response
    response_text = f"{thinking}\nAction: {json.dumps(action_json, ensure_ascii=False)}"
    
    if isinstance(assistant_content, str):
        assistant_msg["content"] = response_text
    elif isinstance(assistant_content, list):
        # Update text content
        for item in assistant_content:
            if isinstance(item, dict) and item.get("type") == "text":
                item["text"] = response_text
                break
    
    return new_sample


def process_sft_data_with_history(
    input_file: str,
    output_file: str,
    history_window: int = 5,
    generate_anti_loop: bool = True,
    anti_loop_ratio: float = 0.2,
    generate_upload_after_samples: bool = True,
    upload_after_ratio: float = 0.5,  # Increased to 0.5 for aggressive positive augmentation
) -> dict[str, int]:
    """Process SFT data file and add action history (OpenAI messages format).
    
    This function works with the OpenAI messages format and preserves images.
    
    IMPORTANT: For upload-after-click samples, we ONLY generate POSITIVE samples
    with contrastive reasoning. Negative samples (wrong actions) are harmful for SFT
    because the model learns to output the incorrect coordinates.
    
    Args:
        input_file: Path to input SFT JSONL (OpenAI messages format)
        output_file: Path to output enhanced JSONL
        history_window: Number of history steps to include
        generate_anti_loop: Whether to generate anti-loop samples
        anti_loop_ratio: Ratio of anti-loop samples to generate
        generate_upload_after_samples: Whether to generate upload-after-click samples
        upload_after_ratio: Ratio of upload-after samples to generate (default: 0.5)
    
    Returns:
        Statistics dict
    """
    data = load_jsonl(input_file)
    
    enhanced_samples = []
    stats = {
        "original_samples": len(data),
        "enhanced_samples": 0,
        "anti_loop_samples": 0,
        "upload_after_positive_samples": 0,  # Renamed: only positive samples now
    }
    
    # Pass through original samples
    for sample in data:
        enhanced_samples.append(sample)
        stats["enhanced_samples"] += 1
    
    # Generate anti-loop samples
    if generate_anti_loop and data:
        num_anti_loop = int(len(data) * anti_loop_ratio)
        
        for _ in range(num_anti_loop):
            base_sample = random.choice(data)
            anti_loop_sample = create_anti_loop_sample_messages(base_sample, history_window)
            if anti_loop_sample:
                enhanced_samples.append(anti_loop_sample)
                stats["anti_loop_samples"] += 1
    
    # Generate upload-after-click samples (ONLY POSITIVE samples with contrastive reasoning)
    if generate_upload_after_samples and data:
        num_upload_after = int(len(data) * upload_after_ratio)
        
        # Find upload-related samples
        upload_samples = [
            s for s in data 
            if "messages" in s and any(
                "upload" in str(msg.get("content", "")).lower() or 
                "上传" in str(msg.get("content", ""))
                for msg in s.get("messages", [])
            )
        ]
        
        if upload_samples:
            variation_idx = 0
            for _ in range(num_upload_after):
                base_sample = random.choice(upload_samples)
                
                # Create POSITIVE sample with contrastive reasoning (click correct file)
                # Use different thinking variations for diversity
                positive_sample = create_upload_after_click_samples(
                    base_sample, 
                    variation_idx=variation_idx
                )
                if positive_sample:
                    enhanced_samples.append(positive_sample)
                    stats["upload_after_positive_samples"] += 1
                    variation_idx += 1  # Rotate through thinking variations
    
    # Shuffle
    random.shuffle(enhanced_samples)
    
    # Write output
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in enhanced_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    stats["total_output"] = len(enhanced_samples)
    return stats


# =============================================================================
# Prompt/Response Format Processing (text only)
# =============================================================================

def create_training_sample_prompt_response(
    trajectory: list[dict],
    current_step: int,
    history_window: int = 5,
) -> dict:
    """Create a training sample with action history (prompt/response format)."""
    
    step = trajectory[current_step]
    instruction = step.get("instruction", "")
    thinking = step.get("thinking", "")
    action = step.get("action", {})
    action_type = step.get("action_type", action.get("action", ""))
    
    # Format action history
    history = format_action_history(trajectory, current_step + 1, history_window)
    
    # Build prompt
    prompt = f"""Task: {instruction}

Action History:
{history}

Current step: {current_step + 1}

Based on the current screenshot and action history, what should you do next?"""
    
    # Build action JSON
    if action_type == "click":
        coord = action.get("coordinate", [0, 0])
        action_json = {"action": "click", "coordinate": coord}
    elif action_type == "type":
        action_json = {"action": "type", "text": action.get("text", "")}
    elif action_type == "swipe":
        action_json = {"action": "swipe", "direction": action.get("direction", "up")}
        if "coordinate" in action:
            action_json["coordinate"] = action["coordinate"]
    elif action_type == "system_button":
        action_json = {"action": "system_button", "button": action.get("button", "home")}
    elif action_type == "long_press":
        action_json = {"action": "long_press", "coordinate": action.get("coordinate", [0, 0])}
    elif action_type in ("answer", "ask_user"):
        action_json = {"action": action_type, "text": action.get("text", "")}
    else:
        action_json = action
    
    response = f"""<thinking>
{thinking}
</thinking>
<tool_call>
{{"name": "mobile_use", "arguments": {json.dumps(action_json, ensure_ascii=False)}}}
</tool_call>"""
    
    return {"prompt": prompt, "response": response}


def generate_anti_loop_sample_prompt_response(
    trajectory: list[dict],
    insert_at_step: int,
    repeat_action: str,
    repeat_count: int,
    history_window: int = 5,
) -> dict | None:
    """Generate a synthetic anti-loop training sample (prompt/response format)."""
    if insert_at_step >= len(trajectory):
        return None
    
    step = trajectory[insert_at_step]
    instruction = step.get("instruction", "")
    
    # Create fake history
    fake_history_lines = []
    for i in range(repeat_count):
        step_num = insert_at_step - repeat_count + i + 1
        if step_num > 0:
            if repeat_action == "swipe":
                fake_history_lines.append(f"- Step {step_num}: swipe up")
            elif repeat_action == "click":
                fake_history_lines.append(f"- Step {step_num}: click at (0.50, 0.50)")
    
    history = "\n".join(fake_history_lines)
    
    prompt = f"""Task: {instruction}

Action History:
{history}

Current step: {insert_at_step + 1}

Based on the current screenshot and action history, what should you do next?"""
    
    response = generate_anti_loop_response_xml(repeat_action, repeat_count, instruction)
    
    return {"prompt": prompt, "response": response}


def process_trajectory_file(
    input_file: str,
    output_file: str,
    history_window: int = 5,
    generate_anti_loop: bool = True,
    anti_loop_ratio: float = 0.2,
) -> dict[str, int]:
    """Process a trajectory file and output augmented training data (prompt/response format).
    
    Args:
        input_file: Path to input trajectory JSONL
        output_file: Path to output training JSONL
        history_window: Number of history steps to include
        generate_anti_loop: Whether to generate anti-loop samples
        anti_loop_ratio: Ratio of anti-loop samples to normal samples
    
    Returns:
        Statistics dict
    """
    trajectory = load_trajectory(input_file)
    
    samples = []
    stats = {
        "normal_samples": 0,
        "anti_loop_samples": 0,
        "total_steps": len(trajectory),
    }
    
    # Generate normal samples
    for i in range(len(trajectory)):
        sample = create_training_sample_prompt_response(trajectory, i, history_window)
        samples.append(sample)
        stats["normal_samples"] += 1
    
    # Generate anti-loop samples
    if generate_anti_loop and len(trajectory) > 3:
        num_anti_loop = int(len(trajectory) * anti_loop_ratio)
        
        for _ in range(num_anti_loop):
            insert_step = random.randint(3, len(trajectory) - 1)
            repeat_count = random.randint(3, 6)
            repeat_action = random.choice(["swipe", "click"])
            
            sample = generate_anti_loop_sample_prompt_response(
                trajectory, insert_step, repeat_action, repeat_count, history_window
            )
            if sample:
                samples.append(sample)
                stats["anti_loop_samples"] += 1
    
    # Shuffle
    random.shuffle(samples)
    
    # Write output
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    return stats


def process_trajectory_to_sft(
    trajectory_file: str,
    output_file: str,
    system_prompt: str,
    history_window: int = 5,
    image_base_dir: str | None = None,
) -> dict[str, int]:
    """Convert raw trajectory data to SFT format with images and history.
    
    Args:
        trajectory_file: Path to trajectory.jsonl
        output_file: Output SFT JSONL path
        system_prompt: System prompt to use
        history_window: Number of history steps
        image_base_dir: Base directory for resolving image paths
    
    Returns:
        Statistics
    """
    trajectory = load_trajectory(trajectory_file)
    
    if not trajectory:
        return {"samples": 0}
    
    samples = []
    traj_dir = Path(trajectory_file).parent
    
    for i, step in enumerate(trajectory):
        history_text = format_action_history_bracketed(trajectory, i + 1, history_window)
        
        instruction = step.get("instruction", "")
        screenshot_path = step.get("screenshot_path", "")
        thinking = step.get("thinking", "")
        action = step.get("action", {})
        
        # Resolve screenshot path
        if screenshot_path and not Path(screenshot_path).is_absolute():
            if image_base_dir:
                full_path = Path(image_base_dir) / screenshot_path
            else:
                full_path = traj_dir / Path(screenshot_path).name
            screenshot_path = str(full_path)
        
        # Build messages
        user_content = [
            {"type": "text", "text": f"Task: {instruction}{history_text}\n\nCurrent screenshot:"},
        ]
        
        if screenshot_path and Path(screenshot_path).exists():
            user_content.append({
                "type": "image_url",
                "image_url": {"url": screenshot_path}
            })
        
        assistant_content = f"Thought: {thinking}\nAction: {json.dumps(action, ensure_ascii=False)}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ]
        
        samples.append({"messages": messages})
    
    # Write output
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    
    return {"samples": len(samples)}


# =============================================================================
# Main Entry Point
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Augment GUI Agent training data with action history and anti-loop samples"
    )
    parser.add_argument(
        "--input", "-i", type=str, required=True,
        help="Input JSONL file (SFT messages format or trajectory format)"
    )
    parser.add_argument(
        "--output", "-o", type=str, required=True,
        help="Output JSONL file"
    )
    parser.add_argument(
        "--format", type=str, choices=["messages", "prompt_response", "auto"],
        default="auto",
        help="Output format: messages (OpenAI), prompt_response (text-only), auto (detect)"
    )
    parser.add_argument(
        "--history-window", type=int, default=5,
        help="Number of history steps to include (default: 5)"
    )
    parser.add_argument(
        "--anti-loop-ratio", type=float, default=0.2,
        help="Ratio of anti-loop samples to generate (default: 0.2)"
    )
    parser.add_argument(
        "--no-anti-loop", action="store_true",
        help="Disable anti-loop sample generation"
    )
    parser.add_argument(
        "--upload-after-ratio", type=float, default=0.5,
        help="Ratio of upload-after-click positive samples to generate (default: 0.5)"
    )
    parser.add_argument(
        "--no-upload-after", action="store_true",
        help="Disable upload-after-click sample generation"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: {args.input} does not exist")
        return
    
    # Detect format
    output_format = args.format
    if output_format == "auto":
        # Check first line of input
        with open(args.input, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line:
                sample = json.loads(first_line)
                if "messages" in sample:
                    output_format = "messages"
                else:
                    output_format = "prompt_response"
            else:
                output_format = "messages"
    
    if input_path.is_file():
        if output_format == "messages":
            stats = process_sft_data_with_history(
                args.input,
                args.output,
                args.history_window,
                not args.no_anti_loop,
                args.anti_loop_ratio,
                not args.no_upload_after,
                args.upload_after_ratio,
            )
            print(f"Processed (messages format): {args.input}")
            print(f"  Original samples: {stats['original_samples']}")
            print(f"  Enhanced samples: {stats['enhanced_samples']}")
            print(f"  Anti-loop samples: {stats['anti_loop_samples']}")
            print(f"  Upload-after positive samples (with contrastive reasoning): {stats.get('upload_after_positive_samples', 0)}")
            print(f"  Total output: {stats['total_output']}")
        else:
            stats = process_trajectory_file(
                args.input,
                args.output,
                args.history_window,
                not args.no_anti_loop,
                args.anti_loop_ratio,
            )
            print(f"Processed (prompt_response format): {args.input}")
            print(f"  Normal samples: {stats['normal_samples']}")
            print(f"  Anti-loop samples: {stats['anti_loop_samples']}")
            print(f"  Total: {stats['normal_samples'] + stats['anti_loop_samples']}")
    
    elif input_path.is_dir():
        # Process directory with multiple trajectories
        all_samples = []
        total_stats = {"normal_samples": 0, "anti_loop_samples": 0}
        
        for traj_file in input_path.glob("**/trajectory.jsonl"):
            trajectory = load_trajectory(str(traj_file))
            
            for i in range(len(trajectory)):
                sample = create_training_sample_prompt_response(
                    trajectory, i, args.history_window
                )
                all_samples.append(sample)
                total_stats["normal_samples"] += 1
            
            if not args.no_anti_loop and len(trajectory) > 3:
                num_anti_loop = int(len(trajectory) * args.anti_loop_ratio)
                for _ in range(num_anti_loop):
                    insert_step = random.randint(3, len(trajectory) - 1)
                    repeat_count = random.randint(3, 6)
                    repeat_action = random.choice(["swipe", "click"])
                    
                    sample = generate_anti_loop_sample_prompt_response(
                        trajectory, insert_step, repeat_action,
                        repeat_count, args.history_window
                    )
                    if sample:
                        all_samples.append(sample)
                        total_stats["anti_loop_samples"] += 1
        
        random.shuffle(all_samples)
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(args.output, "w", encoding="utf-8") as f:
            for sample in all_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        
        print(f"Processed directory: {args.input}")
        print(f"  Normal samples: {total_stats['normal_samples']}")
        print(f"  Anti-loop samples: {total_stats['anti_loop_samples']}")
        print(f"  Total: {total_stats['normal_samples'] + total_stats['anti_loop_samples']}")
    
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
