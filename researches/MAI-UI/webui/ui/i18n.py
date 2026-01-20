"""
Internationalization (i18n) module for MAI-UI WebUI.
Provides translation support for English and Chinese.
"""

from typing import Dict, Any

# Current language state (default: English)
_current_language = "en"

# Translation dictionary
TRANSLATIONS: Dict[str, Dict[str, Any]] = {
    "en": {
        "common": {
            "refresh": "Refresh",
            "status": "Status",
            "ready": "Ready",
            "running": "Running",
            "paused": "Paused",
            "stopped": "Stopped",
            "error": "Error",
            "apply": "Apply",
            "save": "Save",
            "clear": "Clear",
            "download": "Download",
            "select": "Select",
            "optional": "(optional)",
        },
        "header": {
            "title": "MAI-UI WebUI",
            "subtitle": "Android GUI Automation with AI Agent",
        },
        "device": {
            "title": "Device Management",
            "status": "Device Status",
            "not_checked": "Not checked",
            "select_device": "Select Device",
            "wireless_connection": "Wireless Connection",
            "ip_address": "IP Address",
            "port": "Port",
            "connect": "Connect",
            "disconnect": "Disconnect",
            "check_adb": "Check ADB",
            "restart_adb": "Restart ADB",
            "selected_device": "Selected device: {device_id}",
            "no_device_selected": "No device selected",
            "enter_ip": "Please enter IP address",
        },
        "task": {
            "title": "Task Control",
            "instruction": "Task Instruction",
            "instruction_placeholder": "Enter task instruction, e.g., 'Open WeChat and send a message to Zhang San'",
            "start_task": "Start Task",
            "stop": "Stop",
            "single_step": "Single Step",
            "pause_resume": "Pause/Resume",
            "auto_run_settings": "Auto-run Settings",
            "max_steps": "Max Steps",
            "step_delay": "Step Delay (s)",
            "auto_run": "Auto Run",
            "user_feedback": "User Feedback",
            "feedback_correction": "Feedback / Correction",
            "feedback_placeholder": "Enter feedback when agent asks for clarification",
            "submit_feedback": "Submit Feedback",
            "enter_instruction": "Please enter task instruction",
            "task_started": "Task started: {session_id}",
            "start_failed": "Start failed: {error}",
            "no_running_task": "No running task",
            "step_completed": "Step {step_index} completed",
            "step_failed": "Step failed or paused",
            "task_completed": "Task completed",
            "task_stopped": "Task stopped",
            "enter_feedback": "Please enter feedback",
            "feedback_submitted": "Feedback submitted",
            "resumed_with_feedback": "Resumed with feedback",
            "no_pending_feedback": "No pending feedback request",
        },
        "trajectory": {
            "title": "Task Trajectory",
            "load_session": "Load Session",
            "export_pdf": "Export PDF",
            "export_markdown": "Export Markdown",
        },
        "model": {
            "title": "Model Configuration",
            "provider": "Model Provider",
            "model_name": "Model Name",
            "model_name_placeholder": "e.g., MAI-UI-8B",
            "api_settings": "API Settings",
            "api_base_url": "API Base URL",
            "api_base_placeholder": "http://localhost:8000/v1",
            "api_key": "API Key",
            "test_connection": "Test Connection",
            "select_provider": "Select a provider",
            "loaded": "Loaded: {display_name}",
            "provider_not_found": "Provider not found: {provider_id}",
            "please_select_provider": "Please select a provider",
            "manage_providers": "Manage Providers",
            "provider_id": "Provider ID",
            "provider_id_placeholder": "e.g., my_custom_api",
            "display_name": "Display Name",
            "display_name_placeholder": "e.g., My Custom API",
            "default_model": "Default Model",
            "default_model_placeholder": "e.g., model-name",
            "add_provider": "Add Provider",
            "delete_selected": "Delete Selected",
            "fill_required_fields": "Please fill in required fields (ID, Name, API Base)",
            "select_provider_to_delete": "Please select a provider to delete",
        },
        "prompt": {
            "tab_title": "Prompt Configuration",
            "select_template": "Select Template",
            "current": "Current",
            "description": "Description",
            "template_content": "Template Content",
            "preview": "Preview",
            "restore_default": "Restore Default",
            "set_as_current": "Set as Current",
            "template_variables": "Template Variables",
            "variable": "Variable",
            "example": "Example",
            "preview_output": "Preview Output",
            "preview_variables": "Preview Variables (JSON)",
            "preview_variables_placeholder": '{"tools": "[]", "goal": "Open Settings"}',
            "rendered_preview": "Rendered Preview",
            "select_template_to_edit": "Select a template to edit",
            "no_template_selected": "No template selected",
            "template_not_found": "Template not found: {template_name}",
            "please_select_template": "Please select a template",
            "invalid_json": "Invalid JSON: {error}",
            "render_error": "Render error: {error}",
            "preview_success": "Preview generated successfully. Check the Preview Output section below.",
            "preview_empty": "Preview is empty. Check template content.",
        },
        "export": {
            "tab_title": "Data Export",
            "convert_trajectory": "Convert trajectory data to training format",
            "select_sessions": "Select Sessions",
            "refresh_sessions": "Refresh Sessions",
            "output_format": "Output Format",
            "format_prompt_response": "SFT (Prompt-Response)",
            "format_full_trajectory": "RL (Full Trajectory)",
            "format_openai_messages": "OpenAI Messages",
            "image_format": "Image Format",
            "image_base64": "Base64 (inline)",
            "image_path": "Path (reference)",
            "image_skip": "Skip images",
            "advanced_options": "Advanced Options",
            "include_history": "Include history steps",
            "skip_failed": "Skip failed steps",
            "history_window": "History window size",
            "max_image_size": "Max image size (WxH)",
            "max_image_size_placeholder": "1024x1024 (optional)",
            "custom_system_prompt": "Custom system prompt (optional)",
            "custom_system_prompt_placeholder": "Leave empty to use default",
            "export_training_data": "Export Training Data",
            "export_status": "Export Status",
            "select_sessions_and_export": "Select sessions and click Export",
            "download_exported_data": "Download Exported Data",
            "export_statistics": "Export Statistics",
            "select_at_least_one": "Please select at least one session",
            "export_successful": "Export successful!\nOutput: {output_path}",
            "missing_dependency": "Missing dependency: {error}\nPlease ensure data converter is properly set up.",
            "export_failed": "Export failed: {error}",
            "stats_sessions": "Sessions",
            "stats_total_steps": "Total Steps",
            "stats_successful_steps": "Successful Steps",
            "stats_failed_steps": "Failed Steps",
            "stats_skipped_steps": "Skipped Steps",
            "stats_output_samples": "Output Samples",
            "stats_images_processed": "Images Processed",
            "stats_file_size": "File Size",
        },
    },
    "zh": {
        "common": {
            "refresh": "刷新",
            "status": "状态",
            "ready": "就绪",
            "running": "运行中",
            "paused": "已暂停",
            "stopped": "已停止",
            "error": "错误",
            "apply": "应用",
            "save": "保存",
            "clear": "清空",
            "download": "下载",
            "select": "选择",
            "optional": "（可选）",
        },
        "header": {
            "title": "MAI-UI WebUI",
            "subtitle": "基于AI智能体的Android GUI自动化",
        },
        "device": {
            "title": "设备管理",
            "status": "设备状态",
            "not_checked": "未检查",
            "select_device": "选择设备",
            "wireless_connection": "无线连接",
            "ip_address": "IP地址",
            "port": "端口",
            "connect": "连接",
            "disconnect": "断开",
            "check_adb": "检查ADB",
            "restart_adb": "重启ADB",
            "selected_device": "已选择设备: {device_id}",
            "no_device_selected": "未选择设备",
            "enter_ip": "请输入IP地址",
        },
        "task": {
            "title": "任务控制",
            "instruction": "任务指令",
            "instruction_placeholder": "输入任务指令，例如：'打开微信并给张三发消息'",
            "start_task": "开始任务",
            "stop": "停止",
            "single_step": "单步执行",
            "pause_resume": "暂停/继续",
            "auto_run_settings": "自动运行设置",
            "max_steps": "最大步数",
            "step_delay": "步延迟（秒）",
            "auto_run": "自动运行",
            "user_feedback": "用户反馈",
            "feedback_correction": "反馈/纠正",
            "feedback_placeholder": "当智能体请求澄清时输入反馈",
            "submit_feedback": "提交反馈",
            "enter_instruction": "请输入任务指令",
            "task_started": "任务已开始: {session_id}",
            "start_failed": "启动失败: {error}",
            "no_running_task": "没有运行中的任务",
            "step_completed": "步骤 {step_index} 已完成",
            "step_failed": "步骤失败或已暂停",
            "task_completed": "任务已完成",
            "task_stopped": "任务已停止",
            "enter_feedback": "请输入反馈",
            "feedback_submitted": "反馈已提交",
            "resumed_with_feedback": "已恢复并附带反馈",
            "no_pending_feedback": "没有待处理的反馈请求",
        },
        "trajectory": {
            "title": "任务轨迹",
            "load_session": "加载会话",
            "export_pdf": "导出PDF",
            "export_markdown": "导出Markdown",
        },
        "model": {
            "title": "模型配置",
            "provider": "模型提供商",
            "model_name": "模型名称",
            "model_name_placeholder": "例如：MAI-UI-8B",
            "api_settings": "API设置",
            "api_base_url": "API基础URL",
            "api_base_placeholder": "http://localhost:8000/v1",
            "api_key": "API密钥",
            "test_connection": "测试连接",
            "select_provider": "选择一个提供商",
            "loaded": "已加载: {display_name}",
            "provider_not_found": "未找到提供商: {provider_id}",
            "please_select_provider": "请选择一个提供商",
            "manage_providers": "管理提供商",
            "provider_id": "提供商ID",
            "provider_id_placeholder": "例如：my_custom_api",
            "display_name": "显示名称",
            "display_name_placeholder": "例如：我的自定义API",
            "default_model": "默认模型",
            "default_model_placeholder": "例如：model-name",
            "add_provider": "添加提供商",
            "delete_selected": "删除选中",
            "fill_required_fields": "请填写必填字段（ID、名称、API基础URL）",
            "select_provider_to_delete": "请选择要删除的提供商",
        },
        "prompt": {
            "tab_title": "提示词配置",
            "select_template": "选择模板",
            "current": "当前",
            "description": "描述",
            "template_content": "模板内容",
            "preview": "预览",
            "restore_default": "恢复默认",
            "set_as_current": "设为当前",
            "template_variables": "模板变量",
            "variable": "变量",
            "example": "示例",
            "preview_output": "预览输出",
            "preview_variables": "预览变量（JSON）",
            "preview_variables_placeholder": '{"tools": "[]", "goal": "打开设置"}',
            "rendered_preview": "渲染预览",
            "select_template_to_edit": "选择一个模板进行编辑",
            "no_template_selected": "未选择模板",
            "template_not_found": "未找到模板: {template_name}",
            "please_select_template": "请选择一个模板",
            "invalid_json": "无效的JSON: {error}",
            "render_error": "渲染错误: {error}",
            "preview_success": "预览生成成功。请查看下方的预览输出部分。",
            "preview_empty": "预览为空。请检查模板内容。",
        },
        "export": {
            "tab_title": "数据导出",
            "convert_trajectory": "将轨迹数据转换为训练格式",
            "select_sessions": "选择会话",
            "refresh_sessions": "刷新会话",
            "output_format": "输出格式",
            "format_prompt_response": "SFT（提示-响应）",
            "format_full_trajectory": "RL（完整轨迹）",
            "format_openai_messages": "OpenAI消息",
            "image_format": "图片格式",
            "image_base64": "Base64（内联）",
            "image_path": "路径（引用）",
            "image_skip": "跳过图片",
            "advanced_options": "高级选项",
            "include_history": "包含历史步骤",
            "skip_failed": "跳过失败步骤",
            "history_window": "历史窗口大小",
            "max_image_size": "最大图片尺寸（宽x高）",
            "max_image_size_placeholder": "1024x1024（可选）",
            "custom_system_prompt": "自定义系统提示词（可选）",
            "custom_system_prompt_placeholder": "留空以使用默认值",
            "export_training_data": "导出训练数据",
            "export_status": "导出状态",
            "select_sessions_and_export": "选择会话并点击导出",
            "download_exported_data": "下载导出数据",
            "export_statistics": "导出统计",
            "select_at_least_one": "请至少选择一个会话",
            "export_successful": "导出成功！\n输出: {output_path}",
            "missing_dependency": "缺少依赖: {error}\n请确保数据转换器已正确设置。",
            "export_failed": "导出失败: {error}",
            "stats_sessions": "会话数",
            "stats_total_steps": "总步数",
            "stats_successful_steps": "成功步数",
            "stats_failed_steps": "失败步数",
            "stats_skipped_steps": "跳过步数",
            "stats_output_samples": "输出样本数",
            "stats_images_processed": "处理的图片数",
            "stats_file_size": "文件大小",
        },
    },
}


def get_current_language() -> str:
    """Get current language code."""
    return _current_language


def set_language(lang: str) -> None:
    """Set current language."""
    global _current_language
    if lang in TRANSLATIONS:
        _current_language = lang
    else:
        raise ValueError(f"Unsupported language: {lang}")


def t(key: str, **kwargs) -> str:
    """
    Translate a key to current language.
    
    Args:
        key: Translation key in dot notation (e.g., "device.title")
        **kwargs: Format arguments for the translation string
    
    Returns:
        Translated string
    """
    keys = key.split(".")
    current_dict = TRANSLATIONS.get(_current_language, TRANSLATIONS["en"])
    
    for k in keys:
        if isinstance(current_dict, dict):
            current_dict = current_dict.get(k)
        else:
            return key  # Key not found, return key itself
    
    if current_dict is None:
        return key
    
    # Format string if kwargs provided
    if kwargs and isinstance(current_dict, str):
        try:
            return current_dict.format(**kwargs)
        except (KeyError, ValueError):
            return current_dict
    
    return current_dict if isinstance(current_dict, str) else key
