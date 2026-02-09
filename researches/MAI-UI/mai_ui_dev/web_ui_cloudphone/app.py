"""
MAI-UI Cloud Phone Web UI
云手机专用 Web 控制台

设计原则：
- 独立文件夹，不修改原有代码
- 使用 api_adapter 做动作映射
- 简洁清晰的 UI
"""

import gradio as gr
import os
import sys
import time
import yaml
from typing import Optional

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入本地模块
from agent_runner import AgentRunner, get_runner, reset_runner
from adb_utils import (
    get_adb_devices, check_adb_connection, restart_adb,
    get_available_apps
)
from trajectory_utils import (
    get_available_sessions, load_session_logs, logs_to_chatbot_messages,
    export_trajectory_to_pdf
)

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [WEB_UI] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 全局状态 ====================
runner: Optional[AgentRunner] = None


# ==================== 配置加载 ====================
def load_config():
    """加载模型配置"""
    config_path = os.path.join(os.path.dirname(current_dir), "model_config.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"加载配置失败: {e}")
        return {}


# ==================== UI 组件 ====================
def create_ui():
    """创建 Gradio UI"""

    # 加载配置
    config = load_config()
    provider_choices = []
    for key, val in config.items():
        if key != "mcp_tools" and isinstance(val, dict):
            provider_choices.append((val.get("display_name", key), key))
    provider_choices.append(("自定义", "custom"))

    default_prov = provider_choices[0][1] if provider_choices else "custom"
    default_cfg = config.get(default_prov, {})

    # 自定义 CSS
    custom_css = """
    .trajectory-chatbot img {
        max-width: 400px !important;
        max-height: 700px !important;
        width: auto !important;
        height: auto !important;
        object-fit: contain;
        border-radius: 8px;
        cursor: pointer;
    }
    .trajectory-chatbot .message {
        max-width: 100% !important;
    }
    #log-output textarea {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 12px;
    }
    """

    # 创建界面
    with gr.Blocks(
        title="MAI-UI Cloud Phone Console",
        css=custom_css,
        theme=gr.themes.Soft()
    ) as demo:

        gr.Markdown("## 📱 MAI-UI 云手机控制台")
        gr.Markdown("*使用 api_adapter 进行动作映射，保持原始提示词不变*")

        with gr.Row():
            # 左栏：控制面板
            with gr.Column(scale=1, min_width=350):

                # 设备管理
                with gr.Group():
                    gr.Markdown("### 📱 设备管理")
                    device_status = gr.Textbox(
                        label="设备状态",
                        value="❓ 未检查",
                        interactive=False,
                        lines=3
                    )
                    with gr.Row():
                        check_btn = gr.Button("检查", size="sm")
                        refresh_btn = gr.Button("刷新", size="sm")
                        restart_btn = gr.Button("重启ADB", size="sm")

                # 任务控制
                with gr.Group():
                    gr.Markdown("### 🎯 任务控制")

                    with gr.Row():
                        session_dropdown = gr.Dropdown(
                            label="历史会话",
                            choices=[],
                            value=None,
                            scale=4,
                            allow_custom_value=True
                        )
                        refresh_session_btn = gr.Button("🔄", size="sm")

                    task_status = gr.Textbox(
                        label="任务状态",
                        value="⚪ 就绪",
                        interactive=False
                    )

                    auto_reply_chk = gr.Checkbox(
                        label="🤖 自动回复",
                        value=False
                    )

                    return_home_chk = gr.Checkbox(
                        label="🏠 执行前返回桌面",
                        value=True,
                        info="每次新任务开始时先返回桌面"
                    )

                    user_input = gr.Textbox(
                        label="任务指令",
                        placeholder="输入任务指令...",
                        lines=4
                    )

                    with gr.Row():
                        submit_btn = gr.Button("▶ 执行", variant="primary", scale=2)
                        step_btn = gr.Button("⏭ 单步", scale=1)
                        stop_btn = gr.Button("⏹ 停止", variant="stop", scale=1)

                # 模型配置
                with gr.Accordion("⚙️ 模型配置", open=False):
                    provider_dd = gr.Dropdown(
                        label="提供商",
                        choices=provider_choices,
                        value=default_prov
                    )

                    base_url = gr.Textbox(
                        label="Base URL",
                        value=default_cfg.get("api_base", "http://localhost:8000/v1")
                    )

                    model_name = gr.Textbox(
                        label="模型名称",
                        value=default_cfg.get("default_model", "MAI-UI-8B")
                    )

                    with gr.Row():
                        check_model_btn = gr.Button("🔍 测试", size="sm")
                        model_status = gr.Textbox(label="状态", interactive=False)

                    with gr.Row():
                        device_dd = gr.Dropdown(label="设备", choices=[], scale=3)
                        refresh_dev_btn = gr.Button("🔄", scale=1)

                    max_steps = gr.Slider(
                        label="最大步数",
                        minimum=10,
                        maximum=100,
                        value=50,
                        step=10
                    )

                # 实用工具
                with gr.Accordion("🛠 工具", open=False):
                    apps_btn = gr.Button("📲 应用列表", size="sm")
                    apps_output = gr.Textbox(label="已安装应用", lines=3)

            # 右栏：可视化
            with gr.Column(scale=2, min_width=600):
                with gr.Row():
                    # 轨迹显示
                    with gr.Column(scale=1):
                        gr.Markdown("### 📊 任务轨迹")
                        trajectory_output = gr.Chatbot(
                            label="轨迹回放",
                            height=700,
                            show_label=False,
                            elem_classes=["trajectory-chatbot"]
                        )
                        with gr.Row():
                            export_btn = gr.Button("📄 导出PDF", size="sm")
                            export_file = gr.File(label="下载", visible=False)

                    # 日志输出
                    with gr.Column(scale=1):
                        gr.Markdown("### 📋 执行日志")
                        log_output = gr.Textbox(
                            label="日志",
                            value="",
                            lines=28,
                            max_lines=30,
                            interactive=False,
                            elem_id="log-output"
                        )
                        with gr.Row():
                            clear_log_btn = gr.Button("🗑 清空", size="sm")
                            copy_log_btn = gr.Button("📋 复制", size="sm")

        # ==================== 事件绑定 ====================

        # 设备管理
        check_btn.click(
            lambda: check_adb_connection()[1],
            outputs=device_status
        )

        refresh_btn.click(
            lambda: get_adb_devices()[1],
            outputs=device_status
        )

        restart_btn.click(
            lambda: restart_adb()[1],
            outputs=device_status
        )

        # 应用列表
        apps_btn.click(
            lambda: get_available_apps(),
            outputs=apps_output
        )

        # 刷新设备列表
        def refresh_devices():
            devices, _ = get_adb_devices()
            valid = [d for d in devices if d and not d.startswith("错误")]
            return gr.Dropdown(choices=valid, value=valid[0] if valid else None)

        refresh_dev_btn.click(refresh_devices, outputs=device_dd)
        demo.load(refresh_devices, outputs=device_dd)

        # 刷新会话列表
        def refresh_sessions():
            sessions = get_available_sessions()
            return gr.Dropdown(choices=sessions, value=sessions[0] if sessions else None)

        refresh_session_btn.click(refresh_sessions, outputs=session_dropdown)
        demo.load(refresh_sessions, outputs=session_dropdown)

        # 加载轨迹
        def load_trajectory(session_id):
            if not session_id:
                return []
            logs = load_session_logs(session_id)
            task_instruction = logs[0].get("instruction") if logs else None
            return logs_to_chatbot_messages(logs, task_instruction)

        session_dropdown.change(load_trajectory, inputs=[session_dropdown], outputs=[trajectory_output])

        # PDF 导出
        def export_pdf(session_id):
            if not session_id:
                return gr.update(value=None, visible=False)
            pdf_path = export_trajectory_to_pdf(session_id)
            if pdf_path:
                return gr.update(value=pdf_path, visible=True)
            return gr.update(value=None, visible=False)

        export_btn.click(export_pdf, inputs=[session_dropdown], outputs=[export_file])

        # Provider 变更
        def on_provider_change(provider):
            if provider == "custom":
                return "", "", "MAI-UI-8B"
            cfg = config.get(provider, {})
            return (
                cfg.get("api_base", ""),
                "",
                cfg.get("default_model", "MAI-UI-8B")
            )

        provider_dd.change(on_provider_change, inputs=[provider_dd], outputs=[base_url, model_name])

        # 模型测试
        def check_model(base_url, model):
            import requests
            try:
                response = requests.post(
                    f"{base_url.rstrip('/')}/chat/completions",
                    json={"model": model, "messages": [{"role": "user", "content": "test"}], "max_tokens": 1},
                    timeout=10
                )
                if response.status_code == 200:
                    return f"✅ 连接成功\n{base_url}\n{model}"
                else:
                    return f"❌ 连接失败: {response.status_code}"
            except Exception as e:
                return f"❌ 连接错误: {str(e)[:50]}"

        check_model_btn.click(
            check_model,
            inputs=[base_url, model_name],
            outputs=[model_status]
        )

        # 清空日志
        clear_log_btn.click(lambda: "", outputs=log_output)

        # 复制日志
        copy_log_btn.click(
            fn=None,
            inputs=[],
            outputs=[],
            js="""() => {
                let el = document.querySelector('#log-output textarea');
                if (el && el.value) {
                    navigator.clipboard.writeText(el.value);
                    alert('已复制到剪贴板');
                }
            }"""
        )

        # ==================== 核心任务执行 ====================
        def start_task(instruction, base_url, model, device, auto_reply, return_home, max_steps):
            """启动任务"""
            global runner

            if not instruction.strip():
                return "⚠️ 请输入任务指令", [], ""

            try:
                runner = reset_runner(
                    llm_base_url=base_url,
                    model_name=model,
                    device_id=device if device else None,
                    return_to_desktop_on_start=return_home
                )
                runner.auto_reply_enabled = auto_reply

                # 设置回调
                def on_step(result):
                    logs = load_session_logs(runner.session_id)
                    return logs_to_chatbot_messages(logs, instruction)

                def on_status(status):
                    return status

                runner.on_step_complete = lambda r: None  # 简化处理
                runner.on_status_change = lambda s: None  # 简化处理

                session_id = runner.start_task(instruction)
                log_text = f"[{session_id}] 任务已启动: {instruction}\n"

                yield "🟢 运行中", [], log_text

                # 执行
                for result in runner.auto_run(max_steps=int(max_steps), step_delay=1.0):
                    if runner.should_stop or not runner.is_running:
                        log_text += "\n⏹ 任务已停止"
                        trajectory = logs_to_chatbot_messages(load_session_logs(session_id))
                        yield "⏹ 已停止", trajectory, log_text
                        return

                    log_text += f"\n步骤 {result.step_index}: {result.action_type} - {result.message}"
                    trajectory = logs_to_chatbot_messages(load_session_logs(session_id))

                    if result.action_type == "terminate":
                        log_text += f"\n✅ 任务完成: {result.action.get('status', '')}"
                        yield runner.get_status(), trajectory, log_text
                        return

                    yield runner.get_status(), trajectory, log_text

                # 最终状态
                trajectory = logs_to_chatbot_messages(load_session_logs(session_id))
                yield runner.get_status(), trajectory, log_text

            except Exception as e:
                logger.error(f"任务执行出错: {e}", exc_info=True)
                yield f"🔴 错误: {e}", [], str(e)

        submit_btn.click(
            start_task,
            inputs=[user_input, base_url, model_name, device_dd, auto_reply_chk, return_home_chk, max_steps],
            outputs=[task_status, trajectory_output, log_output]
        )

        # 单步执行
        def step_task(instruction, base_url, model, device, auto_reply, return_home, current_logs):
            global runner

            if runner is None or not runner.is_running:
                if not instruction.strip():
                    return "⚠️ 请输入任务指令", [], ""

                runner = reset_runner(
                    llm_base_url=base_url,
                    model_name=model,
                    device_id=device if device else None,
                    return_to_desktop_on_start=return_home
                )
                runner.auto_reply_enabled = auto_reply
                runner.start_task(instruction)

            result = runner.step()
            if result:
                log_text = current_logs + f"\n步骤 {result.step_index}: {result.action_type} - {result.message}"
                trajectory = logs_to_chatbot_messages(load_session_logs(runner.session_id))
                return runner.get_status(), trajectory, log_text

            return runner.get_status() if runner else "⚪ 就绪", [], current_logs

        step_btn.click(
            step_task,
            inputs=[user_input, base_url, model_name, device_dd, auto_reply_chk, return_home_chk, log_output],
            outputs=[task_status, trajectory_output, log_output]
        )

        # 停止任务
        def stop_task():
            global runner
            if runner:
                runner.stop()
                runner.clear_pause_state()
                return "⏹ 已停止"
            return "⚪ 就绪"

        stop_btn.click(stop_task, outputs=task_status)

        # 定时刷新
        def poll_sessions():
            """轮询刷新会话列表，并确保当前选中值在列表中"""
            sessions = get_available_sessions()
            current_session = runner.session_id if runner and runner.is_running else None
            # 确保当前 session 在列表中，如果没有则选择第一个
            if current_session and current_session in sessions:
                return gr.Dropdown(choices=sessions, value=current_session)
            elif sessions:
                return gr.Dropdown(choices=sessions, value=sessions[0])
            else:
                return gr.Dropdown(choices=[], value=None)

        gr.Timer(value=2.0).tick(
            fn=poll_sessions,
            outputs=[session_dropdown]
        )

    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=8867,
        share=False,
        inbrowser=True
    )
