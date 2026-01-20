"""
Trajectory visualization panel component.
Provides chatbot-style trajectory display and session management.
"""

import gradio as gr
from typing import Tuple, List, Dict, Any

from core.trajectory_utils import (
    get_available_sessions,
    load_session_logs,
    logs_to_chatbot_messages,
    export_trajectory_to_pdf,
    LOGS_DIR,
)
from ..i18n import t


def create_trajectory_panel() -> Tuple[gr.components.Component, ...]:
    """
    Create trajectory visualization panel.
    
    Returns:
        Tuple of Gradio components
    """
    # Chatbot display
    chatbot = gr.Chatbot(
        label=t("trajectory.title"),
        elem_classes=["mai-chatbot"],
        height=550,
    )
    
    # Session controls
    session_dropdown = gr.Dropdown(
        label=t("trajectory.load_session"),
        choices=[],
        value=None,
        interactive=True,
    )
    
    # Export controls
    with gr.Row():
        export_pdf_btn = gr.Button(t("trajectory.export_pdf"), size="sm", elem_classes=["export-control-btn"])
        export_md_btn = gr.Button(t("trajectory.export_markdown"), size="sm", elem_classes=["export-control-btn"])
        clear_btn = gr.Button(t("common.clear"), size="sm", variant="secondary", elem_classes=["export-control-btn"])
        refresh_sessions_btn = gr.Button(t("common.refresh"), size="sm", elem_classes=["refresh-btn", "refresh-btn-green"])
    
    # Export file output
    export_file = gr.File(
        label=t("common.download"),
        visible=False,
    )
    
    # Event handlers
    def refresh_sessions():
        """Refresh available sessions."""
        sessions = get_available_sessions()
        return gr.update(choices=sessions, value=sessions[0] if sessions else None)
    
    def load_session(session_id: str):
        """Load a session's trajectory."""
        if not session_id:
            return []
        
        logs = load_session_logs(session_id)
        if not logs:
            return []
        
        messages = logs_to_chatbot_messages(logs)
        return messages
    
    def export_pdf(session_id: str):
        """Export trajectory to PDF."""
        if not session_id:
            return gr.update(visible=False)
        
        output_path = export_trajectory_to_pdf(session_id)
        if output_path:
            return gr.update(value=output_path, visible=True)
        return gr.update(visible=False)
    
    def export_markdown(session_id: str):
        """Export trajectory to Markdown."""
        if not session_id:
            return gr.update(visible=False)
        
        from core.trajectory_utils import trajectory_to_markdown
        import os
        
        logs = load_session_logs(session_id)
        if not logs:
            return gr.update(visible=False)
        
        md_content = trajectory_to_markdown(logs)
        output_path = os.path.join(LOGS_DIR, session_id, f"trajectory_{session_id}.md")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        return gr.update(value=output_path, visible=True)
    
    def clear_chatbot():
        """Clear chatbot display."""
        return []
    
    # Wire up events
    refresh_sessions_btn.click(
        fn=refresh_sessions,
        outputs=[session_dropdown],
    )
    
    session_dropdown.change(
        fn=load_session,
        inputs=[session_dropdown],
        outputs=[chatbot],
    )
    
    export_pdf_btn.click(
        fn=export_pdf,
        inputs=[session_dropdown],
        outputs=[export_file],
    )
    
    export_md_btn.click(
        fn=export_markdown,
        inputs=[session_dropdown],
        outputs=[export_file],
    )
    
    clear_btn.click(
        fn=clear_chatbot,
        outputs=[chatbot],
    )
    
    return chatbot, session_dropdown, refresh_sessions_btn, export_file, export_pdf_btn, export_md_btn, clear_btn
