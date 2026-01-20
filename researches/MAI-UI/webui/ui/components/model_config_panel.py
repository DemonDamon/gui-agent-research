"""
Model configuration panel component.
Provides model provider management and switching.
"""

import gradio as gr
from typing import Tuple

from config.model_config import get_model_manager
from ..i18n import t


def create_model_config_panel() -> Tuple[gr.components.Component, ...]:
    """
    Create model configuration panel.
    
    Returns:
        Tuple of Gradio components
    """
    manager = get_model_manager()
    
    with gr.Accordion(t("model.title"), open=True, elem_classes=["mai-accordion"]):
        # Provider selection
        providers = manager.get_provider_display_names()
        provider_choices = [(v, k) for k, v in providers.items()]
        
        provider_dropdown = gr.Dropdown(
            label=t("model.provider"),
            choices=provider_choices,
            value=list(providers.keys())[0] if providers else None,
            interactive=True,
        )
        
        # Model name
        model_input = gr.Textbox(
            label=t("model.model_name"),
            placeholder=t("model.model_name_placeholder"),
            value="",
        )
        
        # API settings
        with gr.Accordion(t("model.api_settings"), open=False):
            api_base_input = gr.Textbox(
                label=t("model.api_base_url"),
                placeholder=t("model.api_base_placeholder"),
            )
            api_key_input = gr.Textbox(
                label=t("model.api_key"),
                placeholder=t("common.optional"),
                type="password",
            )
        
        # Control buttons
        with gr.Row():
            apply_btn = gr.Button(t("common.apply"), variant="primary", size="sm")
            test_btn = gr.Button(t("model.test_connection"), variant="secondary", size="sm")
        
        # Status display
        config_status = gr.Textbox(
            label=t("common.status"),
            value=t("model.select_provider"),
            interactive=False,
            lines=2,
        )
        
        # Provider management
        with gr.Accordion(t("model.manage_providers"), open=False):
            with gr.Row():
                new_provider_id = gr.Textbox(
                    label=t("model.provider_id"),
                    placeholder=t("model.provider_id_placeholder"),
                    scale=1,
                )
                new_provider_name = gr.Textbox(
                    label=t("model.display_name"),
                    placeholder=t("model.display_name_placeholder"),
                    scale=1,
                )
            
            with gr.Row():
                new_api_base = gr.Textbox(
                    label=t("model.api_base_url"),
                    placeholder="http://...",
                    scale=2,
                )
                new_api_key = gr.Textbox(
                    label=t("model.api_key"),
                    placeholder=t("common.optional"),
                    type="password",
                    scale=1,
                )
            
            new_default_model = gr.Textbox(
                label=t("model.default_model"),
                placeholder=t("model.default_model_placeholder"),
            )
            
            with gr.Row():
                add_provider_btn = gr.Button(t("model.add_provider"), size="sm")
                delete_provider_btn = gr.Button(t("model.delete_selected"), variant="stop", size="sm")
    
    # Event handlers
    def load_provider_config(provider_id: str):
        """Load configuration for selected provider."""
        if not provider_id:
            return "", "", "", t("model.select_provider")
        
        config = manager.get_provider_config(provider_id)
        if not config:
            return "", "", "", t("model.provider_not_found", provider_id=provider_id)
        
        return (
            config.get("default_model", ""),
            config.get("api_base", ""),
            config.get("api_key", ""),
            t("model.loaded", display_name=config.get("display_name", provider_id)),
        )
    
    def apply_config(provider_id: str, model_name: str, api_base: str, api_key: str):
        """Apply model configuration."""
        if not provider_id:
            return t("model.please_select_provider")
        
        # Update provider config if changed
        config = manager.get_provider_config(provider_id)
        if config:
            updates = {}
            if api_base and api_base != config.get("api_base"):
                updates["api_base"] = api_base
            if api_key != config.get("api_key"):
                updates["api_key"] = api_key
            if model_name and model_name != config.get("default_model"):
                updates["default_model"] = model_name
            
            if updates:
                manager.update_model_provider(provider_id, updates)
        
        # Switch to provider
        success, msg = manager.switch_model(provider_id, model_name)
        return msg
    
    def test_connection(provider_id: str):
        """Test connection to model provider."""
        if not provider_id:
            return t("model.please_select_provider")
        
        success, msg = manager.test_connection(provider_id)
        return msg
    
    def add_new_provider(
        provider_id: str,
        display_name: str,
        api_base: str,
        api_key: str,
        default_model: str,
    ):
        """Add a new provider."""
        if not provider_id or not display_name or not api_base:
            return gr.update(), t("model.fill_required_fields")
        
        config = {
            "display_name": display_name,
            "api_base": api_base,
            "api_key": api_key,
            "default_model": default_model,
        }
        
        success, msg = manager.add_model_provider(provider_id, config)
        
        if success:
            # Refresh dropdown
            providers = manager.get_provider_display_names()
            provider_choices = [(v, k) for k, v in providers.items()]
            return gr.update(choices=provider_choices), msg
        
        return gr.update(), msg
    
    def delete_provider(provider_id: str):
        """Delete selected provider."""
        if not provider_id:
            return gr.update(), t("model.select_provider_to_delete")
        
        success, msg = manager.remove_model_provider(provider_id)
        
        if success:
            providers = manager.get_provider_display_names()
            provider_choices = [(v, k) for k, v in providers.items()]
            value = list(providers.keys())[0] if providers else None
            return gr.update(choices=provider_choices, value=value), msg
        
        return gr.update(), msg
    
    # Wire up events
    provider_dropdown.change(
        fn=load_provider_config,
        inputs=[provider_dropdown],
        outputs=[model_input, api_base_input, api_key_input, config_status],
    )
    
    apply_btn.click(
        fn=apply_config,
        inputs=[provider_dropdown, model_input, api_base_input, api_key_input],
        outputs=[config_status],
    )
    
    test_btn.click(
        fn=test_connection,
        inputs=[provider_dropdown],
        outputs=[config_status],
    )
    
    add_provider_btn.click(
        fn=add_new_provider,
        inputs=[new_provider_id, new_provider_name, new_api_base, new_api_key, new_default_model],
        outputs=[provider_dropdown, config_status],
    )
    
    delete_provider_btn.click(
        fn=delete_provider,
        inputs=[provider_dropdown],
        outputs=[provider_dropdown, config_status],
    )
    
    return (
        provider_dropdown,
        model_input,
        config_status,
        apply_btn,
        test_btn,
        add_provider_btn,
        delete_provider_btn,
        api_base_input,
        api_key_input,
        new_provider_id,
        new_provider_name,
        new_api_base,
        new_api_key,
        new_default_model,
    )
