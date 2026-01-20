"""
Task control panel component.
Provides task input, execution control, and status display.
"""

import gradio as gr
from typing import Tuple, Callable, Optional

from ..i18n import t


def create_task_panel(
    on_start: Optional[Callable] = None,
    on_step: Optional[Callable] = None,
    on_pause: Optional[Callable] = None,
    on_stop: Optional[Callable] = None,
    on_auto_run: Optional[Callable] = None,
) -> Tuple[gr.components.Component, ...]:
    """
    Create task control panel.
    
    Args:
        on_start: Callback for starting task
        on_step: Callback for single step execution
        on_pause: Callback for pausing task
        on_stop: Callback for stopping task
        on_auto_run: Callback for auto-run mode
    
    Returns:
        Tuple of Gradio components
    """
    with gr.Accordion(t("task.title"), open=True, elem_classes=["mai-accordion"]):
        # Task input
        task_input = gr.Textbox(
            label=t("task.instruction"),
            placeholder=t("task.instruction_placeholder"),
            lines=3,
            elem_classes=["mai-form-group"],
        )
        
        # Status display
        task_status = gr.Textbox(
            label=t("common.status"),
            value=t("common.ready"),
            interactive=False,
            lines=1,
        )
        
        # Control buttons - Row 1
        with gr.Row():
            start_btn = gr.Button(
                t("task.start_task"),
                variant="primary",
                elem_classes=["mai-btn-primary"],
            )
            stop_btn = gr.Button(
                t("task.stop"),
                variant="stop",
                elem_classes=["mai-btn-danger"],
            )
        
        # Control buttons - Row 2
        with gr.Row():
            step_btn = gr.Button(
                t("task.single_step"),
                variant="secondary",
            )
            pause_btn = gr.Button(
                t("task.pause_resume"),
                variant="secondary",
                elem_classes=["mai-btn-warning"],
            )
        
        # Auto-run settings
        with gr.Accordion(t("task.auto_run_settings"), open=False):
            with gr.Row():
                max_steps = gr.Slider(
                    label=t("task.max_steps"),
                    minimum=1,
                    maximum=100,
                    value=30,
                    step=1,
                )
                step_delay = gr.Slider(
                    label=t("task.step_delay"),
                    minimum=0.5,
                    maximum=5.0,
                    value=1.0,
                    step=0.5,
                )
            
            auto_run_btn = gr.Button(
                t("task.auto_run"),
                variant="primary",
                elem_classes=["mai-btn-success"],
            )
        
        # User feedback input (for ask_user action)
        with gr.Accordion(t("task.user_feedback"), open=False):
            feedback_input = gr.Textbox(
                label=t("task.feedback_correction"),
                placeholder=t("task.feedback_placeholder"),
                lines=2,
            )
            feedback_btn = gr.Button(
                t("task.submit_feedback"),
                variant="secondary",
            )
    
    return (
        task_input,
        task_status,
        start_btn,
        stop_btn,
        step_btn,
        pause_btn,
        auto_run_btn,
        max_steps,
        step_delay,
        feedback_input,
        feedback_btn,
    )
