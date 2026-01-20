"""
Trajectory data converter module.
Converts trajectory logs to training data formats.
Reference: trainer/data/process_trajectory_jsonl.py
"""

import os
import json
import base64
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional, Tuple
from PIL import Image

from .formats import (
    TrajectoryStep,
    TrajectoryMetadata,
    OpenAIMessage,
    OpenAIFormatSample,
    PromptResponseSample,
    FullTrajectorySample,
    OutputFormat,
    ImageFormat,
    ProcessingConfig,
    ProcessingStats,
    GUI_AGENT_SYSTEM_PROMPT,
)


def load_image_as_base64(image_path: str, max_size: Optional[Tuple[int, int]] = None) -> str:
    """
    Load image and convert to base64.
    
    Args:
        image_path: Path to image file
        max_size: Optional (width, height) to resize image
        
    Returns:
        Base64 encoded string with data URL prefix
    """
    try:
        with Image.open(image_path) as img:
            if max_size:
                img.thumbnail(max_size, Image.LANCZOS)
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"[Converter] Failed to load image {image_path}: {e}")
        return ""


class TrajectoryConverter:
    """
    Trajectory data converter.
    Converts trajectory logs to various training data formats.
    """
    
    def __init__(self, logs_dir: str = None):
        """
        Initialize converter.
        
        Args:
            logs_dir: Logs directory path
        """
        if logs_dir is None:
            logs_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "logs"
            )
        self.logs_dir = logs_dir
    
    def load_trajectory(self, session_id: str) -> Tuple[List[TrajectoryStep], TrajectoryMetadata]:
        """
        Load trajectory from session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Tuple of (steps list, metadata)
        """
        log_path = os.path.join(self.logs_dir, session_id, "trajectory.jsonl")
        
        if not os.path.exists(log_path):
            return [], TrajectoryMetadata(session_id=session_id)
        
        steps = []
        instruction = ""
        
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    step = TrajectoryStep.from_dict(data)
                    steps.append(step)
                    
                    if not instruction and data.get("instruction"):
                        instruction = data["instruction"]
        
        metadata = TrajectoryMetadata(
            session_id=session_id,
            task_instruction=instruction,
            total_steps=len(steps),
            success=steps[-1].action_type == "terminate" and steps[-1].action.get("status") == "success" if steps else False,
        )
        
        return steps, metadata
    
    def convert_to_openai_format(
        self,
        steps: List[TrajectoryStep],
        config: ProcessingConfig,
        metadata: TrajectoryMetadata = None,
    ) -> List[OpenAIFormatSample]:
        """
        Convert trajectory to OpenAI messages format.
        
        Args:
            steps: Trajectory steps
            config: Processing configuration
            metadata: Optional metadata
            
        Returns:
            List of OpenAI format samples
        """
        samples = []
        system_prompt = config.system_prompt or GUI_AGENT_SYSTEM_PROMPT
        
        for i, step in enumerate(steps):
            if config.skip_failed_steps and not step.success:
                continue
            
            # Build history context
            history_text = ""
            if config.include_history and i > 0:
                start_idx = max(0, i - config.history_window)
                history_steps = steps[start_idx:i]
                history_parts = []
                for h_step in history_steps:
                    history_parts.append(
                        f"Step {h_step.step_index}: {h_step.action_type} - {h_step.message}"
                    )
                history_text = "\n".join(history_parts)
            
            # System message
            system_msg = OpenAIMessage(
                role="system",
                content=[{"type": "text", "text": system_prompt}]
            )
            
            # User message with image and instruction
            user_content = []
            
            # Add image
            if step.screenshot_path and config.image_format != ImageFormat.SKIP:
                if config.image_format == ImageFormat.BASE64:
                    img_url = load_image_as_base64(step.screenshot_path, config.max_image_size)
                    if img_url:
                        user_content.append({
                            "type": "image_url",
                            "image_url": {"url": img_url}
                        })
                else:  # PATH
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": step.screenshot_path}
                    })
            
            # Add instruction and history
            instruction_text = step.instruction or (metadata.task_instruction if metadata else "")
            text_content = f"Task: {instruction_text}"
            if history_text:
                text_content = f"{text_content}\n\nHistory:\n{history_text}"
            
            user_content.append({"type": "text", "text": text_content})
            
            user_msg = OpenAIMessage(role="user", content=user_content)
            
            # Assistant message with thinking and action
            assistant_content = ""
            if step.thinking:
                assistant_content += f"<thinking>\n{step.thinking}\n</thinking>\n"
            assistant_content += f"<tool_call>\n{json.dumps(step.action, ensure_ascii=False)}\n</tool_call>"
            
            assistant_msg = OpenAIMessage(role="assistant", content=assistant_content)
            
            # Create sample
            sample = OpenAIFormatSample(
                messages=[system_msg, user_msg, assistant_msg],
                metadata={
                    "session_id": metadata.session_id if metadata else "",
                    "step_index": step.step_index,
                    "action_type": step.action_type,
                }
            )
            samples.append(sample)
        
        return samples
    
    def convert_to_sft_format(
        self,
        steps: List[TrajectoryStep],
        config: ProcessingConfig,
        metadata: TrajectoryMetadata = None,
    ) -> List[PromptResponseSample]:
        """
        Convert trajectory to SFT (prompt-response) format.
        
        Args:
            steps: Trajectory steps
            config: Processing configuration
            metadata: Optional metadata
            
        Returns:
            List of prompt-response samples
        """
        samples = []
        system_prompt = config.system_prompt or GUI_AGENT_SYSTEM_PROMPT
        
        for i, step in enumerate(steps):
            if config.skip_failed_steps and not step.success:
                continue
            
            # Build prompt
            instruction = step.instruction or (metadata.task_instruction if metadata else "")
            
            history_text = ""
            if config.include_history and i > 0:
                start_idx = max(0, i - config.history_window)
                history_steps = steps[start_idx:i]
                history_parts = []
                for h_step in history_steps:
                    history_parts.append(
                        f"Step {h_step.step_index}: {h_step.action_type} - {h_step.message}"
                    )
                history_text = "\nHistory:\n" + "\n".join(history_parts)
            
            prompt = f"{system_prompt}\n\nTask: {instruction}{history_text}\n\nCurrent screen: [IMAGE]"
            
            # Build response
            response = ""
            if step.thinking:
                response += f"<thinking>\n{step.thinking}\n</thinking>\n"
            response += f"<tool_call>\n{json.dumps(step.action, ensure_ascii=False)}\n</tool_call>"
            
            # Handle image
            image_path = None
            image_base64 = None
            if step.screenshot_path and config.image_format != ImageFormat.SKIP:
                if config.image_format == ImageFormat.BASE64:
                    image_base64 = load_image_as_base64(step.screenshot_path, config.max_image_size)
                else:
                    image_path = step.screenshot_path
            
            sample = PromptResponseSample(
                prompt=prompt,
                response=response,
                image_path=image_path,
                image_base64=image_base64,
                metadata={
                    "session_id": metadata.session_id if metadata else "",
                    "step_index": step.step_index,
                }
            )
            samples.append(sample)
        
        return samples
    
    def convert_to_rl_format(
        self,
        steps: List[TrajectoryStep],
        config: ProcessingConfig,
        metadata: TrajectoryMetadata = None,
    ) -> FullTrajectorySample:
        """
        Convert trajectory to RL (full trajectory) format.
        
        Args:
            steps: Trajectory steps
            config: Processing configuration
            metadata: Optional metadata
            
        Returns:
            Full trajectory sample
        """
        filtered_steps = []
        for step in steps:
            if config.skip_failed_steps and not step.success:
                continue
            filtered_steps.append(step)
        
        # Calculate reward
        reward = None
        if filtered_steps:
            last_step = filtered_steps[-1]
            if last_step.action_type == "terminate":
                reward = 1.0 if last_step.action.get("status") == "success" else -1.0
            elif last_step.action_type == "answer":
                reward = 1.0
        
        instruction = metadata.task_instruction if metadata else ""
        if not instruction and steps:
            instruction = steps[0].instruction
        
        return FullTrajectorySample(
            task_instruction=instruction,
            steps=filtered_steps,
            metadata=metadata,
            reward=reward,
        )
    
    def convert_session(
        self,
        session_id: str,
        config: ProcessingConfig,
    ) -> Tuple[List[Any], ProcessingStats]:
        """
        Convert a single session.
        
        Args:
            session_id: Session ID
            config: Processing configuration
            
        Returns:
            Tuple of (samples list, stats)
        """
        steps, metadata = self.load_trajectory(session_id)
        
        stats = ProcessingStats(
            total_sessions=1,
            total_steps=len(steps),
            successful_steps=sum(1 for s in steps if s.success),
            failed_steps=sum(1 for s in steps if not s.success),
        )
        
        if config.output_format == OutputFormat.OPENAI_MESSAGES:
            samples = self.convert_to_openai_format(steps, config, metadata)
        elif config.output_format == OutputFormat.PROMPT_RESPONSE:
            samples = self.convert_to_sft_format(steps, config, metadata)
        elif config.output_format == OutputFormat.FULL_TRAJECTORY:
            samples = [self.convert_to_rl_format(steps, config, metadata)]
        else:
            samples = []
        
        stats.output_samples = len(samples)
        stats.skipped_steps = stats.total_steps - stats.output_samples if config.output_format != OutputFormat.FULL_TRAJECTORY else 0
        stats.total_images = sum(1 for s in steps if s.screenshot_path)
        
        return samples, stats
    
    def batch_convert(
        self,
        session_ids: List[str],
        config: ProcessingConfig,
        output_path: str = None,
        progress_callback: Callable[[float, str], None] = None,
    ) -> Tuple[str, ProcessingStats]:
        """
        Batch convert multiple sessions.
        
        Args:
            session_ids: List of session IDs
            config: Processing configuration
            output_path: Output file path (optional)
            progress_callback: Progress callback (progress: 0-1, message: str)
            
        Returns:
            Tuple of (output_path, combined_stats)
        """
        all_samples = []
        combined_stats = ProcessingStats()
        
        total = len(session_ids)
        for i, session_id in enumerate(session_ids):
            if progress_callback:
                progress_callback(i / total, f"Processing {session_id}...")
            
            samples, stats = self.convert_session(session_id, config)
            all_samples.extend(samples)
            
            # Combine stats
            combined_stats.total_sessions += stats.total_sessions
            combined_stats.total_steps += stats.total_steps
            combined_stats.successful_steps += stats.successful_steps
            combined_stats.failed_steps += stats.failed_steps
            combined_stats.skipped_steps += stats.skipped_steps
            combined_stats.output_samples += stats.output_samples
            combined_stats.total_images += stats.total_images
        
        # Generate output path if not provided
        if output_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            format_suffix = config.output_format.value
            output_path = os.path.join(self.logs_dir, f"export_{timestamp}_{format_suffix}.jsonl")
        
        # Write output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            for sample in all_samples:
                if hasattr(sample, "to_dict"):
                    f.write(json.dumps(sample.to_dict(), ensure_ascii=False) + "\n")
                else:
                    f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        
        combined_stats.output_file_size = os.path.getsize(output_path)
        
        if progress_callback:
            progress_callback(1.0, "Export complete!")
        
        return output_path, combined_stats
    
    def get_conversion_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a session without converting.
        
        Args:
            session_id: Session ID
            
        Returns:
            Statistics dictionary
        """
        steps, metadata = self.load_trajectory(session_id)
        
        return {
            "session_id": session_id,
            "total_steps": len(steps),
            "successful_steps": sum(1 for s in steps if s.success),
            "failed_steps": sum(1 for s in steps if not s.success),
            "has_images": any(s.screenshot_path for s in steps),
            "instruction": metadata.task_instruction,
        }
