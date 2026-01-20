"""
Prompt editor panel component.
Provides prompt template viewing, editing, and management.
"""

import gradio as gr
from typing import Tuple

from config.prompt_config import get_prompt_manager
from ..i18n import t


def create_prompt_editor() -> Tuple[gr.components.Component, ...]:
    """
    Create prompt editor panel.
    
    Returns:
        Tuple of Gradio components
    """
    manager = get_prompt_manager()
    
    with gr.Tab(t("prompt.tab_title")):
        # Template selection
        with gr.Row():
            template_names = manager.get_template_names()
            template_dropdown = gr.Dropdown(
                label=t("prompt.select_template"),
                choices=template_names,
                value=template_names[0] if template_names else None,
                interactive=True,
                scale=3,
            )
            current_label = gr.Textbox(
                label=t("prompt.current"),
                value=manager.get_current_template_name(),
                interactive=False,
                scale=1,
            )
        
        # Template info
        template_desc = gr.Textbox(
            label=t("prompt.description"),
            value="",
            interactive=False,
            lines=1,
        )
        
        # Code editor
        template_editor = gr.Code(
            label=t("prompt.template_content"),
            language="jinja2",
            lines=20,
            value="",
            elem_classes=["mai-code-editor"],
            container=True,
        )
        
        # Control buttons
        with gr.Row():
            save_btn = gr.Button(t("common.save"), variant="primary", size="sm")
            preview_btn = gr.Button(t("prompt.preview"), variant="secondary", size="sm")
            restore_btn = gr.Button(t("prompt.restore_default"), size="sm")
            set_current_btn = gr.Button(t("prompt.set_as_current"), variant="primary", size="sm")
        
        # Variables display
        with gr.Accordion(t("prompt.template_variables"), open=False):
            variables_display = gr.Dataframe(
                headers=[t("prompt.variable"), t("prompt.description"), t("prompt.example")],
                datatype=["str", "str", "str"],
                row_count=5,
                col_count=(3, "fixed"),
                interactive=False,
            )
        
        # Preview output
        with gr.Accordion(t("prompt.preview_output"), open=True):
            preview_vars = gr.Textbox(
                label=t("prompt.preview_variables"),
                placeholder=t("prompt.preview_variables_placeholder"),
                lines=2,
            )
            preview_output = gr.Textbox(
                label=t("prompt.rendered_preview"),
                lines=15,
                interactive=False,
            )
        
        # Status
        editor_status = gr.Textbox(
            label=t("common.status"),
            value=t("prompt.select_template_to_edit"),
            interactive=False,
            lines=1,
        )
    
    # Event handlers
    def load_template(template_name: str):
        """Load template content and info."""
        if not template_name:
            return "", "", [], "", t("prompt.no_template_selected")
        
        template = manager.get_template(template_name)
        if not template:
            return "", "", [], "", t("prompt.template_not_found", template_name=template_name)
        
        content = template.get("template", "")
        description = template.get("description", "")
        
        # Get variables
        variables = template.get("variables", [])
        if isinstance(variables, list):
            var_data = [
                [v.get("name", ""), v.get("description", ""), v.get("example", "")]
                for v in variables
            ]
        else:
            var_data = []
        
        # Auto-detect variables from template
        detected = manager.get_template_variables(template_name)
        for var in detected:
            if not any(v[0] == var for v in var_data):
                var_data.append([var, "", ""])
        
        return content, description, var_data, "", f"Loaded: {template_name}"
    
    def save_template(template_name: str, content: str):
        """Save template content."""
        if not template_name:
            return t("prompt.please_select_template")
        
        success, msg = manager.save_template(template_name, content)
        return msg
    
    def preview_template(template_name: str, vars_json: str):
        """Preview rendered template."""
        if not template_name:
            return "", t("prompt.please_select_template")
        
        import json
        
        try:
            # Handle None or empty string
            if vars_json and vars_json.strip():
                preview_vars = json.loads(vars_json)
            else:
                preview_vars = {}
        except json.JSONDecodeError as e:
            return "", t("prompt.invalid_json", error=str(e))
        
        try:
            rendered = manager.preview_template(template_name, **preview_vars)
            status_msg = t("prompt.preview_success") if rendered else t("prompt.preview_empty")
            return rendered, status_msg
        except Exception as e:
            error_msg = t("prompt.render_error", error=str(e))
            return "", error_msg
    
    def restore_default(template_name: str):
        """Restore template to default."""
        if not template_name:
            return "", t("prompt.please_select_template")
        
        success, msg = manager.restore_default_template(template_name)
        if success:
            template = manager.get_template(template_name)
            content = template.get("template", "") if template else ""
            return content, msg
        return "", msg
    
    def set_as_current(template_name: str):
        """Set template as current active template."""
        if not template_name:
            return "", t("prompt.please_select_template")
        
        success, msg = manager.set_current_template(template_name)
        current = manager.get_current_template_name()
        return current, msg
    
    # Wire up events
    template_dropdown.change(
        fn=load_template,
        inputs=[template_dropdown],
        outputs=[template_editor, template_desc, variables_display, preview_output, editor_status],
    )
    
    save_btn.click(
        fn=save_template,
        inputs=[template_dropdown, template_editor],
        outputs=[editor_status],
    )
    
    preview_btn.click(
        fn=preview_template,
        inputs=[template_dropdown, preview_vars],
        outputs=[preview_output, editor_status],
    )
    
    restore_btn.click(
        fn=restore_default,
        inputs=[template_dropdown],
        outputs=[template_editor, editor_status],
    )
    
    set_current_btn.click(
        fn=set_as_current,
        inputs=[template_dropdown],
        outputs=[current_label, editor_status],
    )
    
    return (
        template_dropdown,
        template_editor,
        template_desc,
        variables_display,
        preview_output,
        editor_status,
        save_btn,
        preview_btn,
        restore_btn,
        set_current_btn,
        current_label,
        preview_vars,
    )
