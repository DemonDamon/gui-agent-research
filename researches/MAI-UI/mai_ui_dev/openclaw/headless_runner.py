"""
HeadlessMAIAgent - 无头 MAI-UI Agent 执行器

从 web_ui/agent_runner.py 中剥离 Gradio 依赖，封装为纯 Python 类。
实现 观测(Screenshot) → 推理(vLLM) → 执行(ADB) 循环，
可被 MCP Server 或其他上层调用方直接使用。

关键设计：
- 零 UI 依赖：不引入 gradio 或任何 GUI 框架
- Prompt 严格复用：使用 src/prompt.py 中的原始 System Prompt，确保模型输出格式正确
- 滑动窗口：当对话历史过长时自动截断，保留 System Prompt 和初始指令
- 坐标转换：模型输出归一化坐标 (0-1) → 设备实际像素坐标
"""

import os
import sys
import json
import time
import logging
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

# ---------------------------------------------------------------------------
# 路径设置：确保 src/ 和 web_ui/ 目录可被导入
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")
_WEBUI_DIR = os.path.join(_PROJECT_ROOT, "web_ui")

for _dir in (_SRC_DIR, _WEBUI_DIR):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

# 复用原仓库的核心组件（零修改）
from adb_utils import (
    take_screenshot_file_mode,
    tap_device,
    long_press_device,
    swipe_direction,
    input_text_yadb,
    press_system_button,
    open_app,
    get_adb_devices,
    get_device_resolution,
)
from mai_naivigation_agent import MAIUINaivigationAgent

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logger = logging.getLogger("openclaw.headless")


class HeadlessMAIAgent:
    """
    无头 MAI-UI Agent —— 无 UI 依赖的端到端自动化执行器。

    用法示例::

        agent = HeadlessMAIAgent(
            model_url="http://localhost:8000/v1",
            api_key="empty",
        )
        result = agent.run_task("打开设置，把亮度调低")
        print(result)

    Attributes:
        model_url:  vLLM 推理服务地址（兼容 OpenAI API 格式）。
        api_key:    API Key，vLLM 本地部署通常为 "empty"。
        model_name: 模型名称，默认 "MAI-UI-8B"。
        device_id:  Android 设备 ID，为 None 时自动检测。
    """

    def __init__(
        self,
        model_url: str = "http://localhost:8000/v1",
        api_key: str = "empty",
        model_name: str = "MAI-UI-8B",
        device_id: Optional[str] = None,
        history_n: int = 1,
        max_img_dim: int = 1200,
    ):
        """
        初始化 HeadlessMAIAgent。

        Args:
            model_url:   vLLM 服务地址（须兼容 OpenAI Chat Completion 格式）。
            api_key:     API Key，本地部署填 "empty" 即可。
            model_name:  模型名称，需与 vLLM 加载的模型一致。
            device_id:   ADB 设备 ID，为 None 则自动选择第一个已连接设备。
            history_n:   保留的历史截图轮数，用于多步上下文。
            max_img_dim: 截图送入模型前的最大边长（px），用于控制 Token 消耗。
        """
        self.model_url = model_url
        self.api_key = api_key
        self.model_name = model_name
        self.device_id = device_id
        self.history_n = history_n
        self.max_img_dim = max_img_dim

        # 自动检测 ADB 设备
        if self.device_id is None:
            self._auto_detect_device()

        # 初始化底层 Agent（负责 Prompt 构建、LLM 调用、响应解析）
        self._agent: Optional[MAIUINaivigationAgent] = None

        logger.info(
            "HeadlessMAIAgent 初始化完成 | model=%s | device=%s",
            self.model_name,
            self.device_id,
        )

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def run_task(
        self,
        instruction: str,
        max_steps: int = 15,
        step_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """
        执行一条端到端任务。

        这是外部调用的**主入口**。内部执行观测-推理-执行循环，
        直到模型输出 terminate / answer 或达到 max_steps。

        Args:
            instruction: 自然语言任务指令，如 "打开微信发一条消息"。
            max_steps:   单次任务最大步数，防止无限循环。
            step_delay:  每步执行后等待时间（秒），等待 UI 渲染。

        Returns:
            {
                "status": "success" | "failed" | "max_steps_reached",
                "steps":  int,       # 实际执行步数
                "logs":   List[str], # 每步日志摘要
            }
        """
        logger.info("开始任务: %s (max_steps=%d)", instruction, max_steps)

        # 每次新任务重新初始化 Agent（清空历史）
        self._init_agent()

        logs: List[str] = []
        final_status = "max_steps_reached"

        for step_idx in range(1, max_steps + 1):
            logger.info("── Step %d/%d ──", step_idx, max_steps)

            # 1. 观测：截取当前屏幕
            screenshot = self._get_observation()
            if screenshot is None:
                logs.append(f"Step {step_idx}: 截图失败")
                final_status = "failed"
                break

            # 2. 推理：调用 vLLM 预测下一步动作
            prediction, action = self._predict(instruction, screenshot)
            if action is None or action.get("action") is None:
                logs.append(f"Step {step_idx}: 推理失败")
                final_status = "failed"
                break

            action_type = action.get("action", "unknown")
            logger.info("动作: %s | 详情: %s", action_type, json.dumps(action, ensure_ascii=False))

            # 3. 检查终止条件
            if action_type == "terminate":
                status = action.get("status", "unknown")
                final_status = "success" if status == "success" else "failed"
                logs.append(f"Step {step_idx}: 终止 ({status})")
                logger.info("任务终止: %s", status)
                break

            if action_type == "answer":
                answer_text = action.get("text", "")
                final_status = "success"
                logs.append(f"Step {step_idx}: 回答 - {answer_text}")
                logger.info("任务完成，回答: %s", answer_text)
                break

            # 4. 执行动作
            success, msg = self._execute_action(action, screenshot)
            logs.append(f"Step {step_idx}: [{action_type}] {msg} (ok={success})")

            # 5. 等待 UI 渲染
            time.sleep(step_delay)

        result = {
            "status": final_status,
            "steps": len(logs),
            "logs": logs,
        }
        logger.info("任务结束: %s", json.dumps(result, ensure_ascii=False))
        return result

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _auto_detect_device(self) -> None:
        """自动检测并选择第一个已连接的 ADB 设备。"""
        devices, msg = get_adb_devices()
        if devices:
            self.device_id = devices[0]
            logger.info("自动检测到设备: %s", self.device_id)
        else:
            logger.warning("未检测到 ADB 设备，后续操作可能失败: %s", msg)

    def _init_agent(self) -> None:
        """初始化（或重置）底层 MAIUINaivigationAgent。"""
        self._agent = MAIUINaivigationAgent(
            llm_base_url=self.model_url,
            model_name=self.model_name,
            runtime_conf={
                "history_n": self.history_n,
                "temperature": 0.0,
                "top_k": -1,
                "top_p": 1.0,
                "max_tokens": 2048,
            },
        )
        self._agent.reset()

    def _get_observation(self) -> Optional[Image.Image]:
        """
        截取设备当前屏幕。

        Returns:
            PIL Image 对象；截图失败返回 None。
        """
        try:
            screenshot = take_screenshot_file_mode(self.device_id)
            logger.info("截图成功: %s", screenshot.size)
            return screenshot
        except Exception as e:
            logger.error("截图失败: %s", e)
            return None

    def _predict(
        self,
        instruction: str,
        screenshot: Image.Image,
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        调用 vLLM 进行推理，返回原始预测文本和解析后的动作字典。

        会先将截图缩小到 max_img_dim 以控制 Token 消耗。

        Args:
            instruction: 任务指令。
            screenshot:  当前屏幕截图。

        Returns:
            (prediction_text, action_dict) 或 (None, None)。
        """
        if self._agent is None:
            return None, None

        # 缩小截图以减少 Token 消耗
        pred_img = screenshot.copy()
        if max(pred_img.size) > self.max_img_dim:
            ratio = self.max_img_dim / max(pred_img.size)
            new_size = (int(pred_img.width * ratio), int(pred_img.height * ratio))
            pred_img = pred_img.resize(new_size, Image.LANCZOS)
            logger.info("截图缩放: %s -> %s", screenshot.size, new_size)

        obs = {"screenshot": pred_img}

        try:
            prediction, action = self._agent.predict(instruction, obs)
            return prediction, action
        except Exception as e:
            logger.error("推理失败: %s", e)
            return None, None

    def _execute_action(
        self,
        action: Dict[str, Any],
        screenshot: Image.Image,
    ) -> Tuple[bool, str]:
        """
        执行模型输出的动作。

        坐标转换逻辑：模型输出的归一化坐标 (0.0-1.0) × 截图尺寸 = 实际像素坐标。
        （因为模型看到的就是截图，坐标是相对于截图而言的）

        Args:
            action:     解析后的动作字典，如 {"action":"click","coordinate":[0.5,0.3]}。
            screenshot: 当前截图（用于获取实际尺寸进行坐标映射）。

        Returns:
            (success: bool, message: str)
        """
        action_type = action.get("action", "unknown")
        img_w, img_h = screenshot.size

        try:
            if action_type == "click":
                coords = action.get("coordinate", [0.5, 0.5])
                x, y = int(coords[0] * img_w), int(coords[1] * img_h)
                ok = tap_device(x, y, self.device_id)
                return ok, f"点击 ({x}, {y})"

            elif action_type == "long_press":
                coords = action.get("coordinate", [0.5, 0.5])
                x, y = int(coords[0] * img_w), int(coords[1] * img_h)
                ok = long_press_device(x, y, device_id=self.device_id)
                return ok, f"长按 ({x}, {y})"

            elif action_type == "swipe":
                direction = action.get("direction", "up")
                coords = action.get("coordinate")
                x, y = None, None
                if coords:
                    x, y = int(coords[0] * img_w), int(coords[1] * img_h)
                ok = swipe_direction(direction, x, y, device_id=self.device_id)
                return ok, f"滑动 {direction}"

            elif action_type == "type":
                text = action.get("text", "")
                ok = input_text_yadb(text, self.device_id)
                return ok, f"输入: {text[:30]}"

            elif action_type == "system_button":
                button = action.get("button", "home")
                ok = press_system_button(button, self.device_id)
                return ok, f"按键 {button}"

            elif action_type in ("open", "AWAKE"):
                app_name = action.get("text", "")
                ok, msg = open_app(app_name, self.device_id, prefer_awake=True)
                return ok, f"打开应用: {msg}"

            elif action_type == "wait":
                time.sleep(2)
                return True, "等待 2s"

            elif action_type in ("ask_user", "INFO"):
                text = action.get("text", "")
                # 无头模式下无法交互，记录后继续
                logger.warning("Agent 请求用户输入（无头模式跳过）: %s", text)
                return True, f"询问用户(已跳过): {text}"

            else:
                return False, f"未知动作: {action_type}"

        except Exception as e:
            return False, f"执行失败: {e}"


# ---------------------------------------------------------------------------
# 独立运行测试
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    # 从环境变量或默认值获取配置
    api_url = os.environ.get("API_BASE_URL", "http://192.168.32.119:7777/v1")
    api_key = os.environ.get("API_KEY", "empty")
    model = os.environ.get("MODEL_NAME", "MAI-UI-8B")

    agent = HeadlessMAIAgent(
        model_url=api_url,
        api_key=api_key,
        model_name=model,
    )

    # 简单测试：打开设置
    result = agent.run_task("打开中移移动办公，给谭文辉发消息“你好”。")
    print("\n========== 任务结果 ==========")
    print(json.dumps(result, ensure_ascii=False, indent=2))
