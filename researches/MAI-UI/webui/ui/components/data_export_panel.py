"""
Data export panel component.
Provides one-click training data conversion and export.
"""

import gradio as gr
from typing import Tuple, List

from core.trajectory_utils import get_available_sessions, LOGS_DIR
from data.formats import OutputFormat, ImageFormat
from ..i18n import t


def create_data_export_panel() -> Tuple[gr.components.Component, ...]:
    """
    Create data export panel.
    
    Returns:
        Tuple of Gradio components
    """
    with gr.Tab(t("export.tab_title")):
        convert_trajectory_header = gr.HTML(f"<h3>{t('export.convert_trajectory')}</h3>")
        
        # Session selection
        sessions = get_available_sessions()
        session_select = gr.Dropdown(
            label=t("export.select_sessions"),
            choices=sessions,
            value=[],
            multiselect=True,
            interactive=True,
        )
        
        refresh_btn = gr.Button(t("export.refresh_sessions"), size="sm", elem_classes=["refresh-btn"])
        
        # Format selection
        with gr.Row():
            format_select = gr.Radio(
                label=t("export.output_format"),
                choices=[
                    (t("export.format_prompt_response"), "prompt_response"),
                    (t("export.format_full_trajectory"), "full_trajectory"),
                    (t("export.format_openai_messages"), "openai_messages"),
                ],
                value="openai_messages",
                interactive=True,
            )
            image_format_select = gr.Radio(
                label=t("export.image_format"),
                choices=[
                    (t("export.image_base64"), "base64"),
                    (t("export.image_path"), "path"),
                    (t("export.image_skip"), "skip"),
                ],
                value="base64",
                interactive=True,
            )
        
        # Advanced options
        with gr.Accordion(t("export.advanced_options"), open=False):
            with gr.Row():
                include_history = gr.Checkbox(
                    label=t("export.include_history"),
                    value=True,
                )
                skip_failed = gr.Checkbox(
                    label=t("export.skip_failed"),
                    value=True,
                )
            
            with gr.Row():
                history_window = gr.Slider(
                    label=t("export.history_window"),
                    minimum=1,
                    maximum=10,
                    value=3,
                    step=1,
                )
                max_image_size = gr.Textbox(
                    label=t("export.max_image_size"),
                    placeholder=t("export.max_image_size_placeholder"),
                    value="",
                )
            
            system_prompt = gr.Textbox(
                label=t("export.custom_system_prompt"),
                placeholder=t("export.custom_system_prompt_placeholder"),
                lines=3,
            )
        
        # Export button
        export_btn = gr.Button(
            t("export.export_training_data"),
            variant="primary",
            elem_classes=["mai-btn-primary"],
        )
        
        # Progress and status
        progress_bar = gr.Progress()
        
        export_status = gr.Textbox(
            label=t("export.export_status"),
            value=t("export.select_sessions_and_export"),
            interactive=False,
            lines=5,
        )
        
        # Download file
        download_file = gr.File(
            label=t("export.download_exported_data"),
            visible=False,
        )
        
        # Statistics display
        with gr.Accordion(t("export.export_statistics"), open=False):
            stats_display = gr.Markdown("")
    
    # Event handlers
    def refresh_sessions():
        """Refresh session list."""
        sessions = get_available_sessions()
        return gr.update(choices=sessions)
    
    def export_data(
        session_ids: List[str],
        output_format: str,
        image_format: str,
        include_hist: bool,
        skip_fail: bool,
        hist_window: int,
        max_img_size: str,
        sys_prompt: str,
        progress=gr.Progress(),
    ):
        """Export training data."""
        if not session_ids:
            return (
                t("export.select_at_least_one"),
                gr.update(visible=False),
                "",
            )
        
        try:
            from data.converter import TrajectoryConverter
            from data.formats import ProcessingConfig, OutputFormat as OF, ImageFormat as IF
            
            # Parse max image size
            max_size = None
            if max_img_size.strip():
                try:
                    parts = max_img_size.lower().split("x")
                    if len(parts) == 2:
                        max_size = (int(parts[0]), int(parts[1]))
                except ValueError:
                    pass
            
            # Create config
            config = ProcessingConfig(
                output_format=OF(output_format),
                image_format=IF(image_format),
                max_image_size=max_size,
                include_history=include_hist,
                history_window=int(hist_window),
                skip_failed_steps=skip_fail,
                system_prompt=sys_prompt if sys_prompt.strip() else None,
            )
            
            # Create converter and process
            converter = TrajectoryConverter(logs_dir=LOGS_DIR)
            
            progress(0, desc="Starting export...")
            
            output_path, stats = converter.batch_convert(
                session_ids=session_ids,
                config=config,
                progress_callback=lambda p, msg: progress(p, desc=msg),
            )
            
            progress(1.0, desc="Export complete!")
            
            # Format statistics
            stats_md = f"""
**{t('export.export_statistics')}**
- {t('export.stats_sessions')}: {stats.total_sessions}
- {t('export.stats_total_steps')}: {stats.total_steps}
- {t('export.stats_successful_steps')}: {stats.successful_steps}
- {t('export.stats_failed_steps')}: {stats.failed_steps}
- {t('export.stats_skipped_steps')}: {stats.skipped_steps}
- {t('export.stats_output_samples')}: {stats.output_samples}
- {t('export.stats_images_processed')}: {stats.total_images}
- {t('export.stats_file_size')}: {stats.output_file_size / 1024:.2f} KB
"""
            
            return (
                t("export.export_successful", output_path=output_path),
                gr.update(value=output_path, visible=True),
                stats_md,
            )
            
        except ImportError as e:
            return (
                t("export.missing_dependency", error=str(e)),
                gr.update(visible=False),
                "",
            )
        except Exception as e:
            return (
                t("export.export_failed", error=str(e)),
                gr.update(visible=False),
                "",
            )
    
    # Wire up events
    refresh_btn.click(
        fn=refresh_sessions,
        outputs=[session_select],
    )
    
    export_btn.click(
        fn=export_data,
        inputs=[
            session_select,
            format_select,
            image_format_select,
            include_history,
            skip_failed,
            history_window,
            max_image_size,
            system_prompt,
        ],
        outputs=[export_status, download_file, stats_display],
    )
    
    return (
        session_select,
        format_select,
        image_format_select,
        include_history,
        skip_failed,
        history_window,
        export_btn,
        export_status,
        download_file,
        stats_display,
        refresh_btn,
        convert_trajectory_header,
    )
