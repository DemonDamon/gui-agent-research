"""
Configuration module for MAI-UI WebUI.
"""

from .model_config import ModelManager, get_model_manager
from .prompt_config import PromptManager, get_prompt_manager

__all__ = [
    "ModelManager",
    "PromptManager",
    "get_model_manager",
    "get_prompt_manager",
]
