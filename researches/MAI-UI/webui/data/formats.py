"""
Data format definitions for MAI-UI WebUI.
Reference: trainer/data/data_formats.py

Defines standard data structures for trajectory processing and training data generation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class OutputFormat(Enum):
    """Output format types for training data."""
    PROMPT_RESPONSE = "prompt_response"  # SFT format
    FULL_TRAJECTORY = "full_trajectory"  # RL format
    OPENAI_MESSAGES = "openai_messages"  # OpenAI messages format


class ImageFormat(Enum):
    """Image format types for export."""
    BASE64 = "base64"  # Inline base64 encoding
    PATH = "path"  # File path reference
    SKIP = "skip"  # Skip images


@dataclass
class TrajectoryStep:
    """Single step in a trajectory."""
    step_index: int
    thinking: str = ""
    action: Dict[str, Any] = field(default_factory=dict)
    action_type: str = "unknown"
    success: bool = True
    message: str = ""
    timestamp: str = ""
    screenshot_path: str = ""
    instruction: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_index": self.step_index,
            "thinking": self.thinking,
            "action": self.action,
            "action_type": self.action_type,
            "success": self.success,
            "message": self.message,
            "timestamp": self.timestamp,
            "screenshot_path": self.screenshot_path,
            "instruction": self.instruction,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrajectoryStep":
        """Create from dictionary."""
        return cls(
            step_index=data.get("step_index", 0),
            thinking=data.get("thinking", ""),
            action=data.get("action", {}),
            action_type=data.get("action_type", "unknown"),
            success=data.get("success", True),
            message=data.get("message", ""),
            timestamp=data.get("timestamp", ""),
            screenshot_path=data.get("screenshot_path", ""),
            instruction=data.get("instruction", ""),
        )


@dataclass
class TrajectoryMetadata:
    """Metadata for a trajectory session."""
    session_id: str
    task_instruction: str = ""
    model_name: str = ""
    device_id: str = ""
    total_steps: int = 0
    success: bool = True
    start_time: str = ""
    end_time: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "task_instruction": self.task_instruction,
            "model_name": self.model_name,
            "device_id": self.device_id,
            "total_steps": self.total_steps,
            "success": self.success,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


@dataclass
class OpenAIMessage:
    """Single message in OpenAI format."""
    role: str  # "system", "user", "assistant"
    content: Union[str, List[Dict[str, Any]]]  # Text or multimodal content
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass
class OpenAIFormatSample:
    """Training sample in OpenAI messages format."""
    messages: List[OpenAIMessage]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "messages": [msg.to_dict() for msg in self.messages],
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class PromptResponseSample:
    """Training sample in prompt-response (SFT) format."""
    prompt: str
    response: str
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "prompt": self.prompt,
            "response": self.response,
        }
        if self.image_path:
            result["image_path"] = self.image_path
        if self.image_base64:
            result["image_base64"] = self.image_base64
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class FullTrajectorySample:
    """Training sample containing full trajectory (RL format)."""
    task_instruction: str
    steps: List[TrajectoryStep]
    metadata: Optional[TrajectoryMetadata] = None
    reward: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "task_instruction": self.task_instruction,
            "steps": [step.to_dict() for step in self.steps],
        }
        if self.metadata:
            result["metadata"] = self.metadata.to_dict()
        if self.reward is not None:
            result["reward"] = self.reward
        return result


@dataclass
class ProcessingConfig:
    """Configuration for data processing."""
    output_format: OutputFormat = OutputFormat.OPENAI_MESSAGES
    image_format: ImageFormat = ImageFormat.BASE64
    max_image_size: Optional[tuple] = None  # (width, height)
    include_history: bool = True
    history_window: int = 3
    skip_failed_steps: bool = True
    system_prompt: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "output_format": self.output_format.value,
            "image_format": self.image_format.value,
            "max_image_size": self.max_image_size,
            "include_history": self.include_history,
            "history_window": self.history_window,
            "skip_failed_steps": self.skip_failed_steps,
            "system_prompt": self.system_prompt,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessingConfig":
        """Create from dictionary."""
        return cls(
            output_format=OutputFormat(data.get("output_format", "openai_messages")),
            image_format=ImageFormat(data.get("image_format", "base64")),
            max_image_size=data.get("max_image_size"),
            include_history=data.get("include_history", True),
            history_window=data.get("history_window", 3),
            skip_failed_steps=data.get("skip_failed_steps", True),
            system_prompt=data.get("system_prompt"),
        )


@dataclass
class ProcessingStats:
    """Statistics from data processing."""
    total_sessions: int = 0
    total_steps: int = 0
    successful_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    output_samples: int = 0
    total_images: int = 0
    output_file_size: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_sessions": self.total_sessions,
            "total_steps": self.total_steps,
            "successful_steps": self.successful_steps,
            "failed_steps": self.failed_steps,
            "skipped_steps": self.skipped_steps,
            "output_samples": self.output_samples,
            "total_images": self.total_images,
            "output_file_size": self.output_file_size,
        }
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Sessions: {self.total_sessions}",
            f"Total Steps: {self.total_steps}",
            f"Successful: {self.successful_steps}",
            f"Failed: {self.failed_steps}",
            f"Skipped: {self.skipped_steps}",
            f"Output Samples: {self.output_samples}",
            f"Images: {self.total_images}",
        ]
        if self.output_file_size > 0:
            size_mb = self.output_file_size / (1024 * 1024)
            lines.append(f"File Size: {size_mb:.2f} MB")
        return "\n".join(lines)


# Default system prompt for GUI Agent
GUI_AGENT_SYSTEM_PROMPT = """You are a GUI automation agent that can interact with Android devices through screenshots and actions.

Your task is to complete the user's instruction by analyzing the current screen state and executing appropriate actions.

Available actions:
- click(coordinate): Click at the specified normalized coordinate [x, y] where x, y are in range [0, 1]
- long_press(coordinate): Long press at the specified coordinate
- swipe(direction): Swipe in the specified direction (up, down, left, right)
- type(text): Input text at the current focused field
- system_button(button): Press system button (home, back, menu, enter)
- open(text): Open an application by name
- wait: Wait for the screen to update
- terminate(status): End the task with status (success, fail)
- answer(text): Provide an answer to the user's question
- ask_user(text): Ask the user for clarification or additional information

Think step by step about what action to take based on the current screen state."""


# MAI-UI specific system prompt (from trainer/mobile_world/agents/utils/prompts.py)
MAI_MOBILE_SYS_PROMPT = """You are a helpful assistant that can interact with an Android mobile device.

## Role
You are controlling an Android device to help users complete various tasks. You can see the current screen through screenshots and perform actions like clicking, typing, and swiping.

## Capabilities
1. Analyze screenshots to understand the current UI state
2. Plan and execute actions to complete user tasks
3. Navigate between apps and screens
4. Input text and interact with UI elements
5. Handle errors and unexpected situations

## Guidelines
1. Always analyze the screenshot before taking action
2. Click on visible UI elements to interact with them
3. Use swipe actions to scroll or navigate
4. Type text when needed for input fields
5. Press system buttons (home, back) when appropriate
6. If stuck, try alternative approaches
7. Report completion or ask for help when needed"""
