"""
UI Components for MAI-UI WebUI.
"""

from .device_panel import create_device_panel
from .task_panel import create_task_panel
from .trajectory_panel import create_trajectory_panel
from .model_config_panel import create_model_config_panel
from .prompt_editor import create_prompt_editor
from .data_export_panel import create_data_export_panel
from .language_switcher import create_language_switcher

__all__ = [
    "create_device_panel",
    "create_task_panel",
    "create_trajectory_panel",
    "create_model_config_panel",
    "create_prompt_editor",
    "create_data_export_panel",
    "create_language_switcher",
]
