"""
API Adapter - 云手机动作映射层
将 MAI-UI 的原始 action space 映射为云手机 API 要求的格式

设计原则：
1. 保持 MAI-UI 原始提示词不变，让模型输出训练时学过的格式
2. 在此层做动作映射，减少模型幻觉
3. 集中管理映射逻辑，易于维护
"""

import re
import json
import logging
from typing import Dict, Any, Tuple

# 配置日志
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - [API_ADAPTER] - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class CloudPhoneActionMapper:
    """
    云手机动作映射器

    映射规则：
    MAI-UI 原始格式 → 云手机 API 格式
    """

    # 动作映射表
    ACTION_MAP = {
        # 基础动作
        "click": "Tap",
        "long_press": "LongPress",
        "double_click": "DoubleTap",
        "double_tap": "DoubleTap",
        "type": "Type",
        "swipe": "Swipe",
        "drag": "Swipe",

        # 应用启动
        "open": "Launch",
        "awake": "Launch",

        # 系统按键
        "home": "Home",
        "back": "Back",
        "enter": "Enter",

        # 等待
        "wait": "Wait",

        # 终止
        "terminate": "finish",
    }

    @staticmethod
    def parse_llm_output(llm_output: str) -> Tuple[str, Dict[str, Any]]:
        """
        解析 LLM 输出，提取思考过程和动作

        Args:
            llm_output: LLM 原始输出文本

        Returns:
            (thinking, action_dict)
        """
        thinking = ""
        action = {"action": "wait"}  # 默认动作

        # 1. 提取思考过程
        thought_match = re.search(r'<thinking>(.*?)</thinking>', llm_output, re.DOTALL)
        if thought_match:
            thinking = thought_match.group(1).strip()
            logger.debug(f"提取思考过程: {thinking[:100]}...")

        # 2. 提取工具调用 JSON (MAI-UI 使用 < > 标签)
        tool_match = re.search(r'<\s*(.*?)\s*>', llm_output, re.DOTALL)

        if tool_match:
            try:
                json_str = tool_match.group(1).strip()
                logger.info(f"解析工具调用 JSON: {json_str}")
                tool_data = json.loads(json_str)

                if tool_data.get("name") == "mobile_use":
                    action = tool_data.get("arguments", {})
                    logger.info(f"提取动作: {action}")
                else:
                    logger.warning(f"未知工具名称: {tool_data.get('name')}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析失败: {e}")

        return thinking, action

    @classmethod
    def map_action(cls, action: Dict[str, Any], screenshot_size: tuple = (1080, 1920)) -> Dict[str, Any]:
        """
        将 MAI-UI 动作映射为云手机 API 格式

        Args:
            action: MAI-UI 原始动作
            screenshot_size: 截图尺寸 (width, height)

        Returns:
            云手机 API 格式的动作
        """
        action_type = action.get("action", "wait")
        img_width, img_height = screenshot_size

        logger.info(f"开始映射动作: {action_type}")

        # 特殊处理：终止动作
        if action_type == "terminate":
            status = action.get("status", "unknown")
            return {
                "_metadata": "finish",
                "message": f"任务{'成功' if status == 'success' else '失败'}"
            }

        # 特殊处理：answer 动作
        if action_type == "answer":
            text = action.get("text", "")
            return {
                "_metadata": "finish",
                "message": text
            }

        # 特殊处理：system_button 动作（需要进一步解析 button 参数）
        if action_type == "system_button":
            button = action.get("button", "").lower()
            # system_button 的 button 参数映射到对应的按键动作
            button_map = {
                "home": "Home",
                "back": "Back",
                "enter": "Enter",
                "menu": "Menu",
            }
            mapped_button = button_map.get(button, button.capitalize())
            logger.info(f"system_button 映射: {button} → {mapped_button}")
            return {
                "_metadata": "do",
                "action": mapped_button
            }

        # 获取映射后的动作名称
        mapped_action = cls.ACTION_MAP.get(action_type.lower(), action_type)
        logger.debug(f"动作映射: {action_type} → {mapped_action}")

        # 根据动作类型构造云手机 API 格式
        result = {"_metadata": "do", "action": mapped_action}

        # ===== 坐标类动作 =====
        if action_type in ["click", "long_press", "double_click", "double_tap"]:
            coords = action.get("coordinate", [0.5, 0.5])
            if len(coords) >= 2:
                # 相对坐标转绝对坐标
                x = int(coords[0] * img_width)
                y = int(coords[1] * img_height)
                result["element"] = [x, y]
                logger.info(f"坐标转换: {coords} → ({x}, {y})")
            else:
                logger.warning(f"缺少坐标参数: {action}")
                result["element"] = [img_width // 2, img_height // 2]

        # ===== 滑动/拖拽类动作 =====
        elif action_type in ["swipe", "drag"]:
            start = action.get("start")
            end = action.get("end")

            if start and end and len(start) >= 2 and len(end) >= 2:
                x1 = int(start[0] * img_width)
                y1 = int(start[1] * img_height)
                x2 = int(end[0] * img_width)
                y2 = int(end[1] * img_height)
                result["start"] = [x1, y1]
                result["end"] = [x2, y2]
                logger.info(f"滑动: ({x1}, {y1}) → ({x2}, {y2})")
            else:
                # 尝试使用 direction 参数
                direction = action.get("direction", "up")
                result = cls._map_swipe_by_direction(direction, img_width, img_height, action)
                logger.info(f"方向滑动: {direction}")

        # ===== 文本输入 =====
        elif action_type == "type":
            result["text"] = action.get("text", "")

        # ===== 应用启动 =====
        elif action_type in ["open", "awake"]:
            result["app"] = action.get("text", "")

        # ===== 等待 =====
        elif action_type == "wait":
            result["duration"] = action.get("duration", 1)

        logger.info(f"映射结果: {result}")
        return result

    @classmethod
    def _map_swipe_by_direction(cls, direction: str, width: int, height: int, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据方向映射滑动动作

        Args:
            direction: 滑动方向 (up/down/left/right)
            width: 屏幕宽度
            height: 屏幕高度
            action: 原始动作（可能包含 center 坐标）

        Returns:
            云手机 API 格式的滑动动作
        """
        cx, cy = width // 2, height // 2
        distance = min(width, height) // 3

        direction = direction.lower()
        if direction == "up":
            start, end = [cx, cy + distance], [cx, cy - distance]
        elif direction == "down":
            start, end = [cx, cy - distance], [cx, cy + distance]
        elif direction == "left":
            start, end = [cx + distance, cy], [cx - distance, cy]
        elif direction == "right":
            start, end = [cx - distance, cy], [cx + distance, cy]
        else:
            logger.warning(f"未知滑动方向: {direction}，默认向上")
            start, end = [cx, cy + distance], [cx, cy - distance]

        return {
            "_metadata": "do",
            "action": "Swipe",
            "start": start,
            "end": end
        }

    @classmethod
    def convert(cls, llm_output: str, screenshot_size: tuple = (1080, 1920)) -> Tuple[str, Dict[str, Any], str]:
        """
        完整转换流程：LLM 输出 → 思考过程 + 云手机动作 + 摘要

        Args:
            llm_output: LLM 原始输出
            screenshot_size: 截图尺寸

        Returns:
            (thinking, cloud_phone_action, summary)
        """
        # 解析 LLM 输出
        thinking, action = cls.parse_llm_output(llm_output)

        # 映射动作
        cloud_action = cls.map_action(action, screenshot_size)

        # 生成摘要
        action_type = action.get("action", "unknown")
        summary = cls._generate_summary(action, cloud_action)

        return thinking, cloud_action, summary

    @staticmethod
    def _generate_summary(original_action: Dict, mapped_action: Dict) -> str:
        """生成动作摘要"""
        action_type = original_action.get("action", "")

        if action_type == "click":
            return f"点击 {mapped_action.get('element', [])}"
        elif action_type == "long_press":
            return f"长按 {mapped_action.get('element', [])}"
        elif action_type == "swipe":
            return f"滑动 {mapped_action.get('start', [])} → {mapped_action.get('end', [])}"
        elif action_type == "type":
            text = original_action.get('text', '')[:20]
            return f"输入: {text}"
        elif action_type in ["open", "awake"]:
            return f"启动应用: {original_action.get('text', '')}"
        elif action_type == "home":
            return "按下 Home 键"
        elif action_type == "back":
            return "按下返回键"
        elif action_type == "wait":
            return f"等待 {mapped_action.get('duration', 1)} 秒"
        elif action_type == "terminate":
            return f"任务结束: {original_action.get('status', '')}"
        else:
            return f"执行动作: {action_type}"


# 便捷函数
def map_mai_to_cloudphone(llm_output: str, screenshot_size: tuple = (1080, 1920)) -> Tuple[str, Dict[str, Any], str]:
    """
    将 MAI-UI LLM 输出映射为云手机 API 格式

    Args:
        llm_output: LLM 原始输出
        screenshot_size: 截图尺寸 (width, height)

    Returns:
        (thinking, cloud_phone_action, summary)
    """
    return CloudPhoneActionMapper.convert(llm_output, screenshot_size)
