"""
MAI-UI WebUI Main Application.
Modern web interface for Android GUI automation with AI agent.
"""

import os
import sys
import gradio as gr
from typing import List, Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.styles import get_theme, get_custom_css, get_custom_js, get_header_html
from ui.components.device_panel import create_device_panel
from ui.components.task_panel import create_task_panel
from ui.components.trajectory_panel import create_trajectory_panel
from ui.components.model_config_panel import create_model_config_panel
from ui.components.prompt_editor import create_prompt_editor
from ui.components.data_export_panel import create_data_export_panel
from ui.components.language_switcher import create_language_switcher
from ui.i18n import t, set_language, get_current_language
from core.agent_runner import get_runner, reset_runner
from core.trajectory_utils import logs_to_chatbot_messages, get_available_sessions, LOGS_DIR
from config.model_config import get_model_manager
from config.prompt_config import get_prompt_manager


def create_ui():
    """
    Create the main Gradio UI.
    
    Returns:
        Tuple of (demo, theme, css, head)
    """
    theme = get_theme()
    css = get_custom_css()
    head = get_custom_js()
    
    with gr.Blocks(
        title=t("header.title"),
    ) as demo:
        # Hidden HTML component for triggering JavaScript language change event
        language_trigger = gr.HTML("", visible=False)
        
        # Header
        header_html = gr.HTML(get_header_html())
        
        # Main layout: three columns
        with gr.Row():
            # ========== Left Panel: Control ==========
            with gr.Column(scale=1, min_width=300):
                # Language switcher above Device Management
                language_btn_en, language_btn_zh, language_state = create_language_switcher()
                
                # Device management
                (
                    device_dropdown,
                    device_status,
                    refresh_btn,
                    check_adb_btn,
                    restart_adb_btn,
                    connect_btn,
                    disconnect_btn,
                    ip_input,
                    port_input,
                ) = create_device_panel()
                
                # Model configuration
                (
                    provider_dropdown,
                    model_input,
                    config_status,
                    apply_model_btn,
                    test_model_btn,
                    add_provider_btn,
                    delete_provider_btn,
                    api_base_input,
                    api_key_input,
                    new_provider_id,
                    new_provider_name,
                    new_api_base,
                    new_api_key,
                    new_default_model,
                ) = create_model_config_panel()
                
                # Task control
                (
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
                ) = create_task_panel()
            
            # ========== Middle Panel: Trajectory ==========
            with gr.Column(scale=2, min_width=500):
                chatbot, session_dropdown, refresh_sessions_btn, export_file, export_pdf_btn, export_md_btn, clear_btn = create_trajectory_panel()
            
            # ========== Right Panel: Configuration & Export ==========
            with gr.Column(scale=1, min_width=350):
                with gr.Tabs():
                    # Prompt configuration tab
                    (
                        template_dropdown,
                        template_editor,
                        template_desc,
                        variables_display,
                        preview_output,
                        editor_status,
                        save_prompt_btn,
                        preview_prompt_btn,
                        restore_prompt_btn,
                        set_current_btn,
                        current_label,
                        preview_vars,
                    ) = create_prompt_editor()
                    
                    # Data export tab
                    (
                        export_session_select,
                        format_select,
                        image_format_select,
                        include_history,
                        skip_failed,
                        history_window,
                        export_btn,
                        export_status,
                        download_file,
                        stats_display,
                        refresh_export_btn,
                        convert_trajectory_header,
                    ) = create_data_export_panel()
        
        # ========== Event Handlers ==========
        
        # Task control events
        def start_task(instruction: str, device_id: str):
            """Start new task."""
            if not instruction.strip():
                return [], t("task.enter_instruction"), t("common.ready")
            
            try:
                runner = get_runner()
                runner.device_id = device_id
                session_id = runner.start_task(instruction)
                return [], t("task.task_started", session_id=session_id), t("common.running")
            except Exception as e:
                return [], t("task.start_failed", error=str(e)), t("common.error")
        
        def execute_step():
            """Execute single step."""
            runner = get_runner()
            if not runner.is_running:
                return gr.update(), t("task.no_running_task"), t("common.ready")
            
            result = runner.step()
            if result:
                # Update chatbot with new step
                messages = []
                for r in runner.trajectory:
                    messages.append({
                        "role": "assistant",
                        "content": f"**Step {r.step_index}**\nThinking: {r.thinking[:100]}...\nAction: {r.action_type}\nResult: {r.message}"
                    })
                return messages, t("task.step_completed", step_index=result.step_index), runner.get_status()
            return gr.update(), t("task.step_failed"), runner.get_status()
        
        def auto_run_task(max_steps_val: int, delay_val: float):
            """Auto-run task."""
            runner = get_runner()
            if not runner.is_running:
                return gr.update(), t("task.no_running_task"), t("common.ready")
            
            messages = []
            for result in runner.auto_run(max_steps=int(max_steps_val), step_delay=delay_val):
                messages.append({
                    "role": "assistant",
                    "content": f"**Step {result.step_index}**\nThinking: {result.thinking[:100] if result.thinking else ''}...\nAction: {result.action_type}\nResult: {result.message}"
                })
                yield messages, f"Step {result.step_index}", runner.get_status()
            
            yield messages, t("task.task_completed"), runner.get_status()
        
        def pause_task():
            """Pause task."""
            runner = get_runner()
            status = runner.pause()
            return status, runner.get_status()
        
        def stop_task():
            """Stop task."""
            runner = get_runner()
            runner.stop()
            return t("task.task_stopped"), t("common.ready")
        
        def submit_feedback(feedback: str):
            """Submit user feedback."""
            if not feedback.strip():
                return t("task.enter_feedback")
            
            runner = get_runner()
            if runner.waiting_for_input:
                runner.provide_user_input(feedback)
                return t("task.feedback_submitted")
            elif runner.is_paused:
                runner.resume(feedback)
                return t("task.resumed_with_feedback")
            return t("task.no_pending_feedback")
        
        # Wire up task control events
        start_btn.click(
            fn=start_task,
            inputs=[task_input, device_dropdown],
            outputs=[chatbot, task_status, task_status],
        )
        
        step_btn.click(
            fn=execute_step,
            outputs=[chatbot, task_status, task_status],
        )
        
        auto_run_btn.click(
            fn=auto_run_task,
            inputs=[max_steps, step_delay],
            outputs=[chatbot, task_status, task_status],
        )
        
        pause_btn.click(
            fn=pause_task,
            outputs=[task_status, task_status],
        )
        
        stop_btn.click(
            fn=stop_task,
            outputs=[task_status, task_status],
        )
        
        feedback_btn.click(
            fn=submit_feedback,
            inputs=[feedback_input],
            outputs=[task_status],
        )
        
        # Initialize on load
        def on_load():
            """Initialize on page load."""
            # Refresh devices
            from core.adb_utils import get_adb_devices
            devices, status = get_adb_devices()
            
            # Get available sessions
            sessions = get_available_sessions()
            
            return (
                gr.update(choices=devices, value=devices[0] if devices else None),
                status,
                gr.update(choices=sessions),
            )
        
        demo.load(
            fn=on_load,
            outputs=[device_dropdown, device_status, session_dropdown],
        )
        
        # Language change handler - update all UI components
        def on_language_change_en():
            """Handle language change to English."""
            return on_language_change("en")
        
        def on_language_change_zh():
            """Handle language change to Chinese."""
            return on_language_change("zh")
        
        def on_language_change(lang: str):
            """Handle language change and update UI."""
            set_language(lang)
            
            # Trigger JavaScript event for Accordion/Tab updates
            trigger_html = f"""
            <script>
            (function() {{
                // Set language attribute on document (for CSS selectors)
                document.documentElement.setAttribute('data-lang', '{lang}');
                document.body.setAttribute('data-lang', '{lang}');
                
                // Force update all accordion titles immediately
                const translations = {{
                    'zh': {{
                        'Device Management': '设备管理',
                        'Model Configuration': '模型配置',
                        'Task Control': '任务控制',
                        'Wireless Connection': '无线连接',
                        'API Settings': 'API设置',
                        'Manage Providers': '管理提供商',
                        'Auto-run Settings': '自动运行设置',
                        'User Feedback': '用户反馈',
                        'Template Variables': '模板变量',
                        'Preview Output': '预览输出',
                        'Advanced Options': '高级选项',
                        'Export Statistics': '导出统计',
                        'Prompt Configuration': '提示词配置',
                        'Data Export': '数据导出',
                    }},
                    'en': {{
                        '设备管理': 'Device Management',
                        '模型配置': 'Model Configuration',
                        '任务控制': 'Task Control',
                        '无线连接': 'Wireless Connection',
                        'API设置': 'API Settings',
                        '管理提供商': 'Manage Providers',
                        '自动运行设置': 'Auto-run Settings',
                        '用户反馈': 'User Feedback',
                        '模板变量': 'Template Variables',
                        '预览输出': 'Preview Output',
                        '高级选项': 'Advanced Options',
                        '导出统计': 'Export Statistics',
                        '提示词配置': 'Prompt Configuration',
                        '数据导出': 'Data Export',
                    }}
                }};
                
                const map = translations['{lang}'] || {{}};
                
                function forceUpdateAccordions() {{
                    // Find all possible accordion label elements
                    const allElements = document.querySelectorAll('label, button, [role="button"], span, div, .label-wrap, .wrap');
                    let updated = 0;
                    
                    allElements.forEach(el => {{
                        const text = el.textContent.trim();
                        if (map[text]) {{
                            console.log('[MAI-UI] Force updating:', text, '->', map[text]);
                            el.textContent = map[text];
                            updated++;
                        }}
                    }});
                    
                    // Also update text nodes directly
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null
                    );
                    let textNode;
                    while (textNode = walker.nextNode()) {{
                        const text = textNode.textContent.trim();
                        if (map[text]) {{
                            console.log('[MAI-UI] Force updating text node:', text, '->', map[text]);
                            textNode.textContent = map[text];
                            updated++;
                        }}
                    }}
                    
                    // Update Tab titles
                    const tabButtons = document.querySelectorAll('[role="tab"], button[class*="tab"], .tab-nav button, .tabs button');
                    tabButtons.forEach(btn => {{
                        const text = btn.textContent.trim();
                        if (map[text]) {{
                            console.log('[MAI-UI] Force updating tab:', text, '->', map[text]);
                            btn.textContent = map[text];
                            updated++;
                        }}
                    }});
                    
                    console.log('[MAI-UI] Updated', updated, 'elements');
                    return updated;
                }}
                
                // Update immediately
                forceUpdateAccordions();
                
                // Dispatch event
                window.dispatchEvent(new CustomEvent('languageChanged', {{ detail: {{ lang: '{lang}' }} }}));
                
                // Retry multiple times
                [50, 100, 200, 300, 500, 800, 1000, 1500, 2000, 3000].forEach(delay => {{
                    setTimeout(() => forceUpdateAccordions(), delay);
                }});
            }})();
            </script>
            """
            
            # Update all component labels and values
            return (
                lang,  # language_state
                gr.update(variant="primary" if lang == "en" else "secondary"),  # language_btn_en
                gr.update(variant="primary" if lang == "zh" else "secondary"),  # language_btn_zh
                gr.update(value=trigger_html),  # language_trigger
                gr.update(value=get_header_html()),  # header_html
                gr.update(label=t("device.status"), value=t("device.not_checked")),  # device_status
                gr.update(label=t("device.select_device")),  # device_dropdown
                gr.update(value=t("common.refresh")),  # refresh_btn
                gr.update(value=t("device.check_adb")),  # check_adb_btn
                gr.update(value=t("device.restart_adb")),  # restart_adb_btn
                gr.update(value=t("device.connect")),  # connect_btn
                gr.update(value=t("device.disconnect")),  # disconnect_btn
                gr.update(label=t("device.ip_address")),  # ip_input
                gr.update(label=t("device.port")),  # port_input
                gr.update(label=t("model.provider")),  # provider_dropdown
                gr.update(label=t("model.model_name"), placeholder=t("model.model_name_placeholder")),  # model_input
                gr.update(label=t("model.api_base_url"), placeholder=t("model.api_base_placeholder")),  # api_base_input
                gr.update(label=t("model.api_key"), placeholder=t("common.optional")),  # api_key_input
                gr.update(label=t("model.provider_id"), placeholder=t("model.provider_id_placeholder")),  # new_provider_id
                gr.update(label=t("model.display_name"), placeholder=t("model.display_name_placeholder")),  # new_provider_name
                gr.update(label=t("model.api_base_url"), placeholder="http://..."),  # new_api_base
                gr.update(label=t("model.api_key"), placeholder=t("common.optional")),  # new_api_key
                gr.update(label=t("model.default_model"), placeholder=t("model.default_model_placeholder")),  # new_default_model
                gr.update(label=t("common.status"), value=t("model.select_provider")),  # config_status
                gr.update(value=t("common.apply")),  # apply_model_btn
                gr.update(value=t("model.test_connection")),  # test_model_btn
                gr.update(value=t("model.add_provider")),  # add_provider_btn
                gr.update(value=t("model.delete_selected")),  # delete_provider_btn
                gr.update(label=t("task.instruction"), placeholder=t("task.instruction_placeholder")),  # task_input
                gr.update(label=t("common.status"), value=t("common.ready")),  # task_status
                gr.update(value=t("task.start_task")),  # start_btn
                gr.update(value=t("task.stop")),  # stop_btn
                gr.update(value=t("task.single_step")),  # step_btn
                gr.update(value=t("task.pause_resume")),  # pause_btn
                gr.update(value=t("task.auto_run")),  # auto_run_btn
                gr.update(label=t("task.max_steps")),  # max_steps
                gr.update(label=t("task.step_delay")),  # step_delay
                gr.update(label=t("task.feedback_correction"), placeholder=t("task.feedback_placeholder")),  # feedback_input
                gr.update(value=t("task.submit_feedback")),  # feedback_btn
                gr.update(label=t("trajectory.title")),  # chatbot
                gr.update(label=t("trajectory.load_session")),  # session_dropdown
                gr.update(value=t("common.refresh")),  # refresh_sessions_btn
                gr.update(value=t("trajectory.export_pdf")),  # export_pdf_btn
                gr.update(value=t("trajectory.export_markdown")),  # export_md_btn
                gr.update(value=t("common.clear")),  # clear_btn
                gr.update(label=t("prompt.select_template")),  # template_dropdown
                gr.update(label=t("prompt.description")),  # template_desc
                gr.update(label=t("prompt.template_content")),  # template_editor
                gr.update(label=t("prompt.preview_variables"), placeholder=t("prompt.preview_variables_placeholder")),  # preview_vars
                gr.update(label=t("prompt.rendered_preview")),  # preview_output
                gr.update(value=t("common.save")),  # save_prompt_btn
                gr.update(value=t("prompt.preview")),  # preview_prompt_btn
                gr.update(value=t("prompt.restore_default")),  # restore_prompt_btn
                gr.update(value=t("prompt.set_as_current")),  # set_current_btn
                gr.update(label=t("prompt.current")),  # current_label
                gr.update(label=t("common.status"), value=t("prompt.select_template_to_edit")),  # editor_status
                gr.update(value=f"<h3>{t('export.convert_trajectory')}</h3>"),  # convert_trajectory_header
                gr.update(label=t("export.select_sessions")),  # export_session_select
                gr.update(value=t("export.refresh_sessions")),  # refresh_export_btn
                gr.update(
                    label=t("export.output_format"),
                    choices=[
                        (t("export.format_prompt_response"), "prompt_response"),
                        (t("export.format_full_trajectory"), "full_trajectory"),
                        (t("export.format_openai_messages"), "openai_messages"),
                    ],
                ),  # format_select
                gr.update(
                    label=t("export.image_format"),
                    choices=[
                        (t("export.image_base64"), "base64"),
                        (t("export.image_path"), "path"),
                        (t("export.image_skip"), "skip"),
                    ],
                ),  # image_format_select
                gr.update(label=t("export.include_history")),  # include_history
                gr.update(label=t("export.skip_failed")),  # skip_failed
                gr.update(label=t("export.history_window")),  # history_window
                gr.update(value=t("export.export_training_data")),  # export_btn
                gr.update(label=t("export.export_status"), value=t("export.select_sessions_and_export")),  # export_status
                gr.update(label=t("export.download_exported_data")),  # download_file
            )
        
        language_btn_en.click(
            fn=on_language_change_en,
            outputs=[
                language_state,
                language_btn_en,
                language_btn_zh,
                language_trigger,
                header_html,
                device_status,
                device_dropdown,
                refresh_btn,
                check_adb_btn,
                restart_adb_btn,
                connect_btn,
                disconnect_btn,
                ip_input,
                port_input,
                provider_dropdown,
                model_input,
                api_base_input,
                api_key_input,
                new_provider_id,
                new_provider_name,
                new_api_base,
                new_api_key,
                new_default_model,
                config_status,
                apply_model_btn,
                test_model_btn,
                add_provider_btn,
                delete_provider_btn,
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
                chatbot,
                session_dropdown,
                refresh_sessions_btn,
                export_pdf_btn,
                export_md_btn,
                clear_btn,
                template_dropdown,
                template_desc,
                template_editor,
                preview_vars,
                preview_output,
                save_prompt_btn,
                preview_prompt_btn,
                restore_prompt_btn,
                set_current_btn,
                current_label,
                editor_status,
                convert_trajectory_header,
                export_session_select,
                refresh_export_btn,
                format_select,
                image_format_select,
                include_history,
                skip_failed,
                history_window,
                export_btn,
                export_status,
                download_file,
            ],
        )
        
        language_btn_zh.click(
            fn=on_language_change_zh,
            outputs=[
                language_state,
                language_btn_en,
                language_btn_zh,
                language_trigger,
                header_html,
                device_status,
                device_dropdown,
                refresh_btn,
                check_adb_btn,
                restart_adb_btn,
                connect_btn,
                disconnect_btn,
                ip_input,
                port_input,
                provider_dropdown,
                model_input,
                api_base_input,
                api_key_input,
                new_provider_id,
                new_provider_name,
                new_api_base,
                new_api_key,
                new_default_model,
                config_status,
                apply_model_btn,
                test_model_btn,
                add_provider_btn,
                delete_provider_btn,
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
                chatbot,
                session_dropdown,
                refresh_sessions_btn,
                export_pdf_btn,
                export_md_btn,
                clear_btn,
                template_dropdown,
                template_desc,
                template_editor,
                preview_vars,
                preview_output,
                save_prompt_btn,
                preview_prompt_btn,
                restore_prompt_btn,
                set_current_btn,
                current_label,
                editor_status,
                convert_trajectory_header,
                export_session_select,
                refresh_export_btn,
                format_select,
                image_format_select,
                include_history,
                skip_failed,
                history_window,
                export_btn,
                export_status,
                download_file,
            ],
        )
    
    return demo, theme, css, head


def main():
    """Main entry point."""
    print("=" * 50)
    print("MAI-UI WebUI")
    print("=" * 50)
    
    # Check dependencies
    try:
        import gradio
        print(f"[OK] Gradio version: {gradio.__version__}")
    except ImportError:
        print("[ERROR] Gradio not installed. Run: pip install gradio")
        sys.exit(1)
    
    try:
        from PIL import Image
        print("[OK] Pillow installed")
    except ImportError:
        print("[ERROR] Pillow not installed. Run: pip install Pillow")
        sys.exit(1)
    
    try:
        import yaml
        print("[OK] PyYAML installed")
    except ImportError:
        print("[WARNING] PyYAML not installed. Config may not work properly.")
    
    try:
        import openai
        print("[OK] OpenAI library installed")
    except ImportError:
        print("[WARNING] OpenAI not installed. Agent features may not work.")
    
    # Check ADB
    try:
        from core.adb_utils import check_adb_connection
        connected, msg = check_adb_connection()
        print(f"[{'OK' if connected else 'WARNING'}] ADB: {msg.split(chr(10))[0]}")
    except Exception as e:
        print(f"[WARNING] ADB check failed: {e}")
    
    print("=" * 50)
    
    # Create and launch UI
    demo, theme, css, head = create_ui()
    
    # Get port from environment or use default
    port = int(os.environ.get("MAI_UI_PORT", 7860))
    
    print(f"\nStarting server on port {port}...")
    print(f"Open http://localhost:{port} in your browser\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        inbrowser=True,
        show_error=True,
        allowed_paths=[LOGS_DIR],
        theme=theme,
        css=css,
        head=head,
    )


if __name__ == "__main__":
    main()
