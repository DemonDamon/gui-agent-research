"""
Trajectory visualization utility module.
Provides log loading, Chatbot format conversion, action marker drawing, etc.
"""

import os
import json
import base64
from io import BytesIO
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw


def get_logs_dir() -> str:
    """Get the default logs directory path."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "logs")


LOGS_DIR = get_logs_dir()


def long_side_resize(image: Image.Image, long_side: int = 800) -> Image.Image:
    """
    Limit image long side to specified size.
    
    Args:
        image: PIL Image
        long_side: Target long side size
    
    Returns:
        Resized PIL Image
    """
    w, h = image.size
    if max(w, h) <= long_side:
        return image
    
    if w > h:
        new_w = long_side
        new_h = int(h * long_side / w)
    else:
        new_h = long_side
        new_w = int(w * long_side / h)
    
    return image.resize((new_w, new_h), Image.LANCZOS)


def image_to_base64(image: Image.Image) -> str:
    """
    Convert PIL image to base64 Data URL.
    
    Args:
        image: PIL Image
    
    Returns:
        base64 Data URL string
    """
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def get_available_sessions(logs_dir: str = None) -> List[str]:
    """
    Get list of all available session IDs.
    
    Args:
        logs_dir: Logs directory
    
    Returns:
        List of session IDs, sorted by time descending
    """
    if logs_dir is None:
        logs_dir = LOGS_DIR
        
    if not os.path.exists(logs_dir):
        return []
    
    sessions = []
    for name in os.listdir(logs_dir):
        session_dir = os.path.join(logs_dir, name)
        if os.path.isdir(session_dir):
            if os.path.exists(os.path.join(session_dir, "trajectory.jsonl")):
                sessions.append(name)
    
    sessions.sort(reverse=True)
    return sessions


def load_session_logs(session_id: str, logs_dir: str = None) -> List[Dict[str, Any]]:
    """
    Load logs for specified session.
    
    Args:
        session_id: Session ID
        logs_dir: Logs directory
    
    Returns:
        List of log entries
    """
    if logs_dir is None:
        logs_dir = LOGS_DIR
        
    log_path = os.path.join(logs_dir, session_id, "trajectory.jsonl")
    
    if not os.path.exists(log_path):
        return []
    
    logs = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
    except Exception as e:
        print(f"[ERROR] Failed to load logs: {e}")
    
    return logs


def logs_to_chatbot_messages(
    logs: List[Dict[str, Any]],
    task_instruction: str = None,
    model_name: str = None
) -> List[Dict[str, Any]]:
    """
    Convert logs to Gradio Chatbot format message list.

    Gradio Chatbot format:
    [
        {
            "role": "assistant",
            "content": [
                "text content",
                {"path": "path/to/image.png", "alt_text": "description"}
            ]
        }
    ]

    Args:
        logs: List of log entries
        task_instruction: Task instruction (optional)
        model_name: Model name (optional)

    Returns:
        Chatbot messages list
    """
    messages = []
    
    if logs and not task_instruction:
        first_log = logs[0]
        task_instruction = first_log.get("instruction", "") or first_log.get("task", "")
    
    if task_instruction:
        header_content = f"### Task: {task_instruction}"
        if model_name:
            header_content += f"\n\n**Model**: {model_name}"
        messages.append({
            "role": "assistant",
            "content": header_content
        })

    for log in logs:
        step_index = log.get("step_index", 0)
        thinking = log.get("thinking", "")
        action = log.get("action", {})
        action_type = log.get("action_type", "unknown")
        message = log.get("message", "")
        screenshot_path = log.get("screenshot_path", "")

        content_parts = []
        content_parts.append(f"**Step {step_index}**")

        if thinking:
            thinking_display = thinking[:200] + "..." if len(thinking) > 200 else thinking
            content_parts.append(f"\nThinking: {thinking_display}")

        action_text = format_action(action_type, action)
        content_parts.append(f"\nAction: {action_text}")
        content_parts.append(f"\nResult: {message}")

        text_content = "\n".join(content_parts)

        if screenshot_path and os.path.exists(screenshot_path):
            try:
                img = Image.open(screenshot_path)
                img = long_side_resize(img, 800)

                img = draw_action_marker(img, action, action_type)

                marked_path = screenshot_path.replace(".png", "_marked.png")
                img.save(marked_path)

                image_message = {
                    "path": marked_path,
                    "alt_text": f"Step {step_index}: {action_type}"
                }
                content = [text_content, image_message]
            except Exception as e:
                print(f"[WARNING] Failed to load screenshot: {e}")
                content = text_content
        else:
            content = text_content

        messages.append({
            "role": "assistant",
            "content": content
        })

    return messages


def format_action(action_type: str, action: Dict[str, Any]) -> str:
    """
    Format action as readable string.
    
    Args:
        action_type: Action type
        action: Action dictionary
    
    Returns:
        Formatted action description
    """
    if action_type == "click":
        coords = action.get("coordinate", [0, 0])
        return f"Click ({coords[0]:.3f}, {coords[1]:.3f})"
    
    elif action_type == "long_press":
        coords = action.get("coordinate", [0, 0])
        return f"Long Press ({coords[0]:.3f}, {coords[1]:.3f})"
    
    elif action_type == "swipe":
        direction = action.get("direction", "unknown")
        return f"Swipe {direction}"
    
    elif action_type == "type":
        text = action.get("text", "")
        display_text = text[:30] + "..." if len(text) > 30 else text
        return f'Type: "{display_text}"'
    
    elif action_type == "system_button":
        button = action.get("button", "unknown")
        return f"System Button: {button}"
    
    elif action_type == "open":
        app = action.get("text", "unknown")
        return f"Open App: {app}"
    
    elif action_type == "wait":
        return "Wait"
    
    elif action_type == "terminate":
        status = action.get("status", "unknown")
        return f"Terminate ({status})"
    
    elif action_type == "answer":
        text = action.get("text", "")
        display_text = text[:50] + "..." if len(text) > 50 else text
        return f'Answer: "{display_text}"'
    
    elif action_type == "ask_user":
        text = action.get("text", "")
        display_text = text[:50] + "..." if len(text) > 50 else text
        return f'Ask User: "{display_text}"'
    
    elif action_type == "mcp_call":
        name = action.get("name", "unknown")
        return f"MCP Call: {name}"
    
    else:
        return f"{action_type}: {action}"


def draw_action_marker(
    image: Image.Image,
    action: Dict[str, Any],
    action_type: str
) -> Image.Image:
    """
    Draw action marker on screenshot.
    
    Args:
        image: PIL Image
        action: Action dictionary
        action_type: Action type
    
    Returns:
        Marked PIL Image
    """
    if action_type not in ["click", "long_press", "swipe"]:
        return image
    
    img = image.copy()
    draw = ImageDraw.Draw(img)
    img_width, img_height = img.size
    
    coords = action.get("coordinate")
    if not coords:
        return image
    
    x = int(coords[0] * img_width)
    y = int(coords[1] * img_height)
    
    if action_type == "click":
        radius = 15
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            outline="red", width=3
        )
        inner_radius = 5
        draw.ellipse(
            (x - inner_radius, y - inner_radius, x + inner_radius, y + inner_radius),
            fill="red"
        )
        line_length = 25
        draw.line((x - line_length, y, x - radius - 3, y), fill="red", width=2)
        draw.line((x + radius + 3, y, x + line_length, y), fill="red", width=2)
        draw.line((x, y - line_length, x, y - radius - 3), fill="red", width=2)
        draw.line((x, y + radius + 3, x, y + line_length), fill="red", width=2)
    
    elif action_type == "long_press":
        radius = 15
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            outline="blue", width=3
        )
        radius2 = 22
        draw.ellipse(
            (x - radius2, y - radius2, x + radius2, y + radius2),
            outline="blue", width=2
        )
    
    elif action_type == "swipe":
        direction = action.get("direction", "up")
        arrow_length = 40
        
        if direction == "up":
            end_x, end_y = x, y - arrow_length
        elif direction == "down":
            end_x, end_y = x, y + arrow_length
        elif direction == "left":
            end_x, end_y = x - arrow_length, y
        elif direction == "right":
            end_x, end_y = x + arrow_length, y
        else:
            end_x, end_y = x, y - arrow_length
        
        draw.line((x, y, end_x, end_y), fill="green", width=4)
        
        draw.ellipse(
            (end_x - 6, end_y - 6, end_x + 6, end_y + 6),
            fill="green"
        )
        draw.ellipse(
            (x - 4, y - 4, x + 4, y + 4),
            fill="green", outline="white", width=1
        )
    
    return img


def trajectory_to_markdown(logs: List[Dict[str, Any]]) -> str:
    """
    Convert trajectory to Markdown format.
    
    Args:
        logs: List of log entries
    
    Returns:
        Markdown string
    """
    lines = ["# Task Trajectory\n"]
    
    for log in logs:
        step_index = log.get("step_index", 0)
        thinking = log.get("thinking", "")
        action_type = log.get("action_type", "unknown")
        action = log.get("action", {})
        message = log.get("message", "")
        timestamp = log.get("timestamp", "")
        
        lines.append(f"## Step {step_index}")
        lines.append(f"*Time: {timestamp}*\n")
        
        if thinking:
            lines.append(f"**Thinking**: {thinking}\n")
        
        action_text = format_action(action_type, action)
        lines.append(f"**Action**: {action_text}\n")
        lines.append(f"**Result**: {message}\n")
        lines.append("---\n")
    
    return "\n".join(lines)


def export_trajectory_to_pdf(
    session_id: str,
    logs_dir: str = None,
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Export trajectory to PDF file.
    
    Args:
        session_id: Session ID
        logs_dir: Logs directory
        output_path: Output file path, default {logs_dir}/{session_id}/trajectory.pdf
    
    Returns:
        Generated PDF file path, None if failed
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        print("[ERROR] reportlab required: pip install reportlab")
        return None
    
    if logs_dir is None:
        logs_dir = LOGS_DIR
    
    logs = load_session_logs(session_id, logs_dir)
    if not logs:
        print(f"[ERROR] No logs found: {session_id}")
        return None
    
    if output_path is None:
        output_path = os.path.join(logs_dir, session_id, f"trajectory_{session_id}.pdf")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Try to register Chinese font
    font_registered = False
    try:
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                pdfmetrics.registerFont(TTFont("ChineseFont", fp))
                font_registered = True
                break
    except Exception as e:
        print(f"[WARNING] Failed to register Chinese font: {e}")
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    styles = getSampleStyleSheet()
    if font_registered:
        title_style = ParagraphStyle(
            "ChineseTitle",
            parent=styles["Heading1"],
            fontName="ChineseFont",
            fontSize=18,
            spaceAfter=12
        )
        body_style = ParagraphStyle(
            "ChineseBody",
            parent=styles["Normal"],
            fontName="ChineseFont",
            fontSize=10,
            leading=14
        )
    else:
        title_style = styles["Heading1"]
        body_style = styles["Normal"]
    
    story = []
    
    story.append(Paragraph(f"Task Trajectory: {session_id}", title_style))
    story.append(Spacer(1, 10*mm))
    
    for log in logs:
        step_index = log.get("step_index", 0)
        thinking = log.get("thinking", "")
        action_type = log.get("action_type", "unknown")
        action = log.get("action", {})
        message = log.get("message", "")
        timestamp = log.get("timestamp", "")
        screenshot_path = log.get("screenshot_path", "")
        
        story.append(Paragraph(f"<b>Step {step_index}</b> - {timestamp}", body_style))
        story.append(Spacer(1, 2*mm))
        
        if thinking:
            thinking_short = thinking[:200] + "..." if len(thinking) > 200 else thinking
            story.append(Paragraph(f"<i>Thinking:</i> {thinking_short}", body_style))
        
        action_text = format_action(action_type, action)
        story.append(Paragraph(f"<b>Action:</b> {action_text}", body_style))
        
        story.append(Paragraph(f"<b>Result:</b> {message}", body_style))
        
        marked_path = screenshot_path.replace(".png", "_marked.png") if screenshot_path else ""
        img_path = marked_path if os.path.exists(marked_path) else screenshot_path
        
        if img_path and os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path)
                img_w, img_h = pil_img.size
                
                max_width = 160 * mm
                max_height = 200 * mm
                scale = min(max_width / img_w, max_height / img_h, 1.0)
                
                rl_img = RLImage(img_path, width=img_w * scale, height=img_h * scale)
                story.append(Spacer(1, 3*mm))
                story.append(rl_img)
            except Exception as e:
                print(f"[WARNING] Failed to load image: {e}")
        
        story.append(Spacer(1, 8*mm))
        story.append(Paragraph("<hr/>", body_style))
        story.append(Spacer(1, 5*mm))
    
    try:
        doc.build(story)
        print(f"[PDF] Export successful: {output_path}")
        return output_path
    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}")
        return None
