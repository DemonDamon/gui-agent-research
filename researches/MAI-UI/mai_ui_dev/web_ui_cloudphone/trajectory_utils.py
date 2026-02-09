"""
轨迹工具模块 - 处理任务执行轨迹的保存、加载和可视化
"""

import os
import json
import base64
from io import BytesIO
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw

# 配置日志
import logging
logger = logging.getLogger(__name__)


# ==================== 日志存储 ====================
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)


def get_available_sessions() -> List[str]:
    """获取所有可用的 session ID"""
    sessions = []
    if os.path.exists(LOGS_DIR):
        for item in os.listdir(LOGS_DIR):
            item_path = os.path.join(LOGS_DIR, item)
            if os.path.isdir(item_path) and item.replace('_', '').replace(':', '').replace('-', '').isdigit():
                # 检查是否有轨迹文件
                traj_file = os.path.join(item_path, "trajectory.jsonl")
                if os.path.exists(traj_file):
                    sessions.append(item)
    return sorted(sessions, reverse=True)


def load_session_logs(session_id: str) -> List[Dict[str, Any]]:
    """加载指定 session 的日志"""
    session_dir = os.path.join(LOGS_DIR, session_id)
    traj_file = os.path.join(session_dir, "trajectory.jsonl")

    if not os.path.exists(traj_file):
        return []

    logs = []
    try:
        with open(traj_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
    except Exception as e:
        logger.error(f"加载日志失败: {e}")

    return logs


def save_step_log(session_id: str, step_index: int, screenshot: Image.Image,
                  thinking: str, action: Dict, action_type: str,
                  success: bool, message: str, instruction: str):
    """保存单步日志"""
    session_dir = os.path.join(LOGS_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    # 保存截图
    screenshot_path = os.path.join(session_dir, f"step_{step_index:03d}.png")
    screenshot.save(screenshot_path)

    # 保存轨迹
    log_entry = {
        "step_index": step_index,
        "thinking": thinking,
        "action": action,
        "action_type": action_type,
        "success": success,
        "message": message,
        "screenshot_path": screenshot_path,
        "instruction": instruction
    }

    traj_file = os.path.join(session_dir, "trajectory.jsonl")
    with open(traj_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    logger.debug(f"保存日志: {session_id} - step {step_index}")


# ==================== 图像处理 ====================
def image_to_base64(image: Image.Image, format: str = "JPEG", quality: int = 85) -> str:
    """将 PIL Image 转换为 base64 字符串"""
    buffer = BytesIO()
    # JPEG 不支持 alpha 通道，需要先转换为 RGB
    if format == "JPEG" and image.mode == "RGBA":
        image = image.convert("RGB")
    image.save(buffer, format=format, quality=quality)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def long_side_resize(image: Image.Image, max_size: int = 1024) -> Image.Image:
    """按长边缩放图片"""
    width, height = image.size
    if max(width, height) > max_size:
        ratio = max_size / max(width, height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return image


def draw_action_marker(screenshot: Image.Image, action: Dict[str, Any]) -> Image.Image:
    """在截图上绘制动作标记"""
    img = screenshot.copy()
    draw = ImageDraw.Draw(img)

    action_type = action.get("action", "")

    # 绘制坐标标记
    if action_type in ["click", "long_press", "Tap", "LongPress"]:
        element = action.get("element")
        if element and len(element) >= 2:
            x, y = element[0], element[1]
            # 绘制圆圈
            draw.ellipse([x-20, y-20, x+20, y+20], outline="red", width=3)
            draw.ellipse([x-5, y-5, x+5, y+5], fill="red")

    # 绘制滑动箭头
    elif action_type in ["swipe", "drag", "Swipe"]:
        start = action.get("start")
        end = action.get("end")
        if start and end and len(start) >= 2 and len(end) >= 2:
            draw.line([start[0], start[1], end[0], end[1]], fill="blue", width=5)
            # 起点
            draw.ellipse([start[0]-10, start[1]-10, start[0]+10, start[1]+10], fill="green")

    return img


# ==================== 轨迹可视化 ====================
def logs_to_chatbot_messages(logs: List[Dict[str, Any]], task_instruction: str = None) -> List:
    """
    将日志转换为 Gradio Chatbot 格式的消息

    Gradio 4.0+ 格式: [{"role": "user/assistant", "content": "..."}, ...]
    """
    messages = []

    # 添加任务指令作为第一条消息
    if task_instruction:
        messages.append({
            "role": "user",
            "content": f"📋 任务: {task_instruction}"
        })

    for log in logs:
        step = log.get("step_index", 0)
        thinking = log.get("thinking", "")
        action_type = log.get("action_type", "")
        message = log.get("message", "")
        screenshot_path = log.get("screenshot_path")

        # 构建消息内容
        content = f"**步骤 {step}**\n\n"

        if thinking:
            content += f"🤔 **思考**: {thinking[:200]}...\n\n"

        content += f"⚡ **动作**: {action_type}\n"
        content += f"📝 **说明**: {message}"

        # 加载并添加截图
        if screenshot_path and os.path.exists(screenshot_path):
            screenshot = Image.open(screenshot_path)
            # 在截图上绘制动作标记
            action = log.get("action", {})
            marked_screenshot = draw_action_marker(screenshot, action)
            # 缩放
            marked_screenshot = long_side_resize(marked_screenshot, 640)
            # 转为 base64
            img_b64 = image_to_base64(marked_screenshot)
            content += f"\n\n![screenshot](data:image/jpeg;base64,{img_b64})"

        messages.append({
            "role": "assistant",
            "content": content
        })

    return messages


# ==================== PDF 导出 ====================
def export_trajectory_to_pdf(session_id: str) -> Optional[str]:
    """导出轨迹为 PDF"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet

        session_dir = os.path.join(LOGS_DIR, session_id)
        pdf_path = os.path.join(session_dir, f"trajectory_{session_id}.pdf")

        logs = load_session_logs(session_id)
        if not logs:
            return None

        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # 标题
        title = f"任务轨迹 - {session_id}"
        story.append(Paragraph(f"<b>{title}</b>", styles['Title']))
        story.append(Spacer(1, 0.2 * inch))

        # 获取任务指令
        instruction = logs[0].get("instruction", "未知任务") if logs else "未知任务"
        story.append(Paragraph(f"<b>任务:</b> {instruction}", styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))

        # 每一步
        for log in logs:
            step = log.get("step_index", 0)
            action_type = log.get("action_type", "")
            thinking = log.get("thinking", "")
            screenshot_path = log.get("screenshot_path")

            # 步骤标题
            story.append(Paragraph(f"<b>步骤 {step}</b>", styles['Heading2']))

            # 思考
            if thinking:
                story.append(Paragraph(f"<i>思考:</i> {thinking[:300]}...", styles['Normal']))

            # 动作
            story.append(Paragraph(f"<i>动作:</i> {action_type}", styles['Normal']))

            # 截图
            if screenshot_path and os.path.exists(screenshot_path):
                try:
                    img = RLImage(screenshot_path, width=4 * inch, height=7 * inch)
                    story.append(img)
                except:
                    pass

            story.append(Spacer(1, 0.2 * inch))

        doc.build(story)
        logger.info(f"PDF 导出成功: {pdf_path}")
        return pdf_path

    except ImportError:
        logger.warning("reportlab 未安装，无法导出 PDF")
        return None
    except Exception as e:
        logger.error(f"PDF 导出失败: {e}")
        return None
