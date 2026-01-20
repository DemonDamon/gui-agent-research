"""
Language switcher component for MAI-UI WebUI.
Provides UI for switching between English and Chinese.
"""

import gradio as gr
from typing import Tuple

from ..i18n import set_language, get_current_language, t


def create_language_switcher() -> Tuple[gr.components.Component, ...]:
    """
    Create language switcher component using buttons.
    
    Returns:
        Tuple of (language_btn_en, language_btn_zh, language_state)
    """
    current_lang = get_current_language()
    
    with gr.Row(elem_classes=["lang-switcher-container"]):
        language_btn_en = gr.Button(
            "EN",
            variant="primary" if current_lang == "en" else "secondary",
            size="sm",
            min_width=70,
            elem_classes=["lang-btn", "lang-btn-en"],
        )
        language_btn_zh = gr.Button(
            "中文",
            variant="primary" if current_lang == "zh" else "secondary",
            size="sm",
            min_width=70,
            elem_classes=["lang-btn", "lang-btn-zh"],
        )
    
    language_state = gr.State(value=current_lang)
    
    return language_btn_en, language_btn_zh, language_state
