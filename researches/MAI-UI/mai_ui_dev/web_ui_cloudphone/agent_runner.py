"""
Agent 运行器 - 云手机版本
整合 MAI-UI Agent 与 ADB 操作，实现自动化任务执行

设计原则：
1. 使用原始 prompt.py，让模型输出训练时学过的格式
2. 在 api_adapter 层做动作映射到云手机格式
3. 通过 adb_utils 执行实际的 ADB 命令
"""

import os
import sys
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Generator, Callable
from datetime import datetime
from PIL import Image

# 添加 src 目录到路径
src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 导入本地模块
from adb_utils import (
    take_screenshot,
    tap_device, long_press_device, double_tap_device,
    swipe_device, input_text_yadb,
    press_home, press_back, press_enter, wait_device,
    get_device_resolution, launch_app
)
from api_adapter import CloudPhoneActionMapper
from trajectory_utils import save_step_log

# 配置日志
import logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - [AGENT_RUNNER] - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ==================== Agent 导入 ====================
try:
    from mai_naivigation_agent import MAIUINaivigationAgent
    HAS_AGENT = True
except ImportError:
    HAS_AGENT = False
    logger.warning("MAI-UI Agent 未找到，将使用模拟模式")


@dataclass
class StepResult:
    """单步执行结果"""
    step_index: int
    screenshot: Image.Image
    thinking: str
    action: Dict[str, Any]
    action_type: str
    success: bool
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "thinking": self.thinking,
            "action": self.action,
            "action_type": self.action_type,
            "success": self.success,
            "message": self.message,
            "timestamp": self.timestamp
        }


class AgentRunner:
    """
    Agent 运行器 - 云手机版本

    执行流程：
    1. 截图
    2. 调用 LLM 预测（使用原始 prompt.py）
    3. 使用 api_adapter 映射动作
    4. 执行 ADB 命令
    5. 保存日志
    """

    def __init__(
        self,
        llm_base_url: str = "http://localhost:8000/v1",
        model_name: str = "MAI-UI-8B",
        device_id: Optional[str] = None,
        logs_dir: str = None,
        return_to_desktop_on_start: bool = True
    ):
        self.llm_base_url = llm_base_url
        self.model_name = model_name
        self.device_id = device_id

        # 日志目录
        if logs_dir is None:
            logs_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "logs"
            )
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)

        self.return_to_desktop_on_start = return_to_desktop_on_start
        self.auto_reply_enabled = False

        # 状态
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        self.waiting_for_input = False
        self.user_input: Optional[str] = None
        self.pending_user_feedback: Optional[str] = None
        self.paused_session_id: Optional[str] = None

        # 当前任务
        self.current_instruction: Optional[str] = None
        self.session_id: Optional[str] = None
        self.step_count = 0
        self.trajectory: List[StepResult] = []
        self.task_start_time: Optional[float] = None

        # Agent 实例
        self.agent: Optional['MAIUINaivigationAgent'] = None

        # 回调
        self.on_step_complete: Optional[Callable[[StepResult], None]] = None
        self.on_status_change: Optional[Callable[[str], None]] = None

        # 线程锁
        self._lock = threading.Lock()

    def _init_agent(self):
        """初始化 Agent（使用原始提示词）"""
        if not HAS_AGENT:
            logger.warning("Agent 不可用")
            return

        # 使用原始 prompt.py（不使用 cloudphone 版本）
        logger.info("使用原始 prompt.py - 让模型输出训练时学过的格式")

        self.agent = MAIUINaivigationAgent(
            llm_base_url=self.llm_base_url,
            model_name=self.model_name,
            runtime_conf={
                "history_n": 3,
                "temperature": 0.0,
                "top_k": -1,
                "top_p": 1.0,
                "max_tokens": 2048,
            }
        )
        logger.info(f"Agent 初始化完成: {self.model_name}")

    def start_task(self, instruction: str) -> str:
        """开始新任务"""
        with self._lock:
            if self.is_running:
                raise RuntimeError("已有任务正在运行")

            # 生成 Session ID
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_instruction = instruction
            self.step_count = 0
            self.trajectory = []
            self.task_start_time = time.time()
            self.is_running = True
            self.is_paused = False
            self.should_stop = False
            self.waiting_for_input = False

            # 初始化 Agent
            self._init_agent()
            if self.agent:
                self.agent.reset()

            # 返回桌面
            if self.return_to_desktop_on_start:
                self._notify_status("🏠 正在返回桌面...")
                try:
                    success = press_home(self.device_id)
                    if success:
                        time.sleep(0.5)
                        logger.info("已返回桌面")
                    else:
                        logger.warning("返回桌面失败")
                except Exception as e:
                    logger.error(f"返回桌面出错: {e}")

            self._notify_status("🟢 任务已开始")
            logger.info(f"任务开始: {instruction}")

            return self.session_id

    def step(self) -> Optional[StepResult]:
        """执行单步"""
        if not self.is_running:
            return None

        if self.is_paused:
            return None

        if self.should_stop:
            self._finish_task("stopped")
            return None

        try:
            # 1. 截图
            logger.info(f"步骤 {self.step_count + 1}: 截图中...")
            self.step_count += 1
            screenshot = take_screenshot(self.device_id)
            img_width, img_height = screenshot.size
            logger.info(f"截图成功: {screenshot.size}")

            # 2. 调用 Agent 预测
            if self.agent:
                logger.info(f"调用 LLM 预测: {self.current_instruction[:50]}...")

                # 缩小截图以减少 Token 消耗
                pred_screenshot = screenshot.copy()
                max_dim = 1024
                if max(pred_screenshot.size) > max_dim:
                    ratio = max_dim / max(pred_screenshot.size)
                    new_size = (int(pred_screenshot.width * ratio), int(pred_screenshot.height * ratio))
                    pred_screenshot = pred_screenshot.resize(new_size, Image.Resampling.LANCZOS)

                obs = {"screenshot": pred_screenshot}

                # 处理用户反馈
                if self.pending_user_feedback or self.user_input:
                    feedback = self.pending_user_feedback or self.user_input
                    obs["user_feedback"] = f"【用户输入】{feedback}"
                    logger.info(f"用户反馈: {feedback}")
                    self.pending_user_feedback = None
                    self.user_input = None

                # 获取 LLM 预测（原始格式）
                prediction, action = self.agent.predict(self.current_instruction, obs)
                logger.info(f"LLM 输出: {prediction[:150]}...")

                # 解析思考过程
                thinking = ""
                if "<thinking>" in prediction:
                    thinking = prediction.split("<thinking>")[1].split("</thinking>")[0].strip()
            else:
                action = {"action": "terminate", "status": "fail"}
                thinking = "Agent 未初始化"
                prediction = ""

            action_type = action.get("action", "unknown")

            # 检查暂停/停止状态
            if self.is_paused:
                logger.info("检测到暂停状态，放弃执行")
                return None

            if self.should_stop:
                logger.info("检测到停止状态")
                self._finish_task("stopped")
                return None

            # 3. 使用 api_adapter 映射动作
            logger.info(f"原始动作: {action}")
            cloud_action = CloudPhoneActionMapper.map_action(action, (img_width, img_height))
            logger.info(f"映射后动作: {cloud_action}")

            # 4. 执行动作
            logger.info(f"执行动作: {cloud_action.get('action')}")
            success, message = self._execute_cloud_action(cloud_action, screenshot)
            logger.info(f"执行结果: {'成功' if success else '失败'} - {message}")

            # 5. 创建结果
            result = StepResult(
                step_index=self.step_count,
                screenshot=screenshot,
                thinking=thinking,
                action=cloud_action,  # 保存映射后的动作
                action_type=action_type,
                success=success,
                message=message
            )

            self.trajectory.append(result)

            # 6. 保存日志
            save_step_log(
                self.session_id,
                self.step_count,
                screenshot,
                thinking,
                cloud_action,
                action_type,
                success,
                message,
                self.current_instruction
            )

            # 7. 回调
            if self.on_step_complete:
                self.on_step_complete(result)

            # 8. 检查终止条件
            if action_type == "terminate":
                status = action.get("status", "unknown")
                self._finish_task(status)
            elif action_type in ["answer", "ask_user", "INFO"]:
                if self.auto_reply_enabled:
                    self._handle_auto_reply(screenshot, action.get("text", ""))
                else:
                    self._wait_for_user_input(action.get("text", ""))

            return result

        except Exception as e:
            logger.error(f"步骤执行出错: {e}", exc_info=True)
            result = StepResult(
                step_index=self.step_count,
                screenshot=screenshot if 'screenshot' in locals() else Image.new('RGB', (100, 100)),
                thinking="",
                action={"action": "error"},
                action_type="error",
                success=False,
                message=f"执行出错: {str(e)}"
            )
            self.trajectory.append(result)
            self._notify_status(f"🔴 执行出错: {e}")
            return result

    def _execute_cloud_action(self, action: Dict[str, Any], screenshot: Image.Image) -> tuple:
        """
        执行云手机动作

        Args:
            action: 云手机格式的动作（已通过 api_adapter 映射）
            screenshot: 当前截图

        Returns:
            (success, message)
        """
        action_type = action.get("action", "")
        img_width, img_height = screenshot.size

        try:
            # Tap - 点击
            if action_type == "Tap":
                element = action.get("element", [])
                if len(element) >= 2:
                    x, y = element[0], element[1]
                    return tap_device(x, y, self.device_id), f"点击 ({x}, {y})"
                return False, "Tap 缺少坐标"

            # LongPress - 长按
            elif action_type == "LongPress":
                element = action.get("element", [])
                if len(element) >= 2:
                    x, y = element[0], element[1]
                    duration = action.get("duration", 1000)
                    return long_press_device(x, y, duration, self.device_id), f"长按 ({x}, {y}) {duration}ms"
                return False, "LongPress 缺少坐标"

            # DoubleTap - 双击
            elif action_type == "DoubleTap":
                element = action.get("element", [])
                if len(element) >= 2:
                    x, y = element[0], element[1]
                    return double_tap_device(x, y, self.device_id), f"双击 ({x}, {y})"
                return False, "DoubleTap 缺少坐标"

            # Swipe - 滑动
            elif action_type == "Swipe":
                start = action.get("start", [])
                end = action.get("end", [])
                if len(start) >= 2 and len(end) >= 2:
                    x1, y1 = start[0], start[1]
                    x2, y2 = end[0], end[1]
                    return swipe_device(x1, y1, x2, y2, device_id=self.device_id), f"滑动 ({x1},{y1})→({x2},{y2})"
                return False, "Swipe 缺少坐标"

            # Type - 输入文本
            elif action_type == "Type":
                text = action.get("text", "")
                logger.info(f"准备输入文本: {text}")

                # 云手机环境：先点击输入框确保焦点，再输入
                # 添加延迟确保焦点获得
                time.sleep(0.3)

                success = input_text_yadb(text, self.device_id)

                # 输入后再等待一下
                if success:
                    time.sleep(0.2)
                    logger.info(f"文本输入成功: {text[:30]}...")
                else:
                    logger.warning(f"文本输入失败: {text[:30]}...")

                return success, f"输入: {text[:30]}..."

            # Launch - 启动应用
            elif action_type == "Launch":
                app_name = action.get("app", "")
                return launch_app(app_name, self.device_id)

            # Home - Home 键
            elif action_type == "Home":
                return press_home(self.device_id), "按下 Home 键"

            # Back - 返回键
            elif action_type == "Back":
                return press_back(self.device_id), "按下返回键"

            # Enter - 回车键
            elif action_type == "Enter":
                return press_enter(self.device_id), "按下回车键"

            # Wait - 等待
            elif action_type == "Wait":
                duration = action.get("duration", 1)
                return wait_device(duration, self.device_id), f"等待 {duration} 秒"

            else:
                return False, f"未知动作: {action_type}"

        except Exception as e:
            logger.error(f"动作执行失败: {e}", exc_info=True)
            return False, f"执行失败: {str(e)}"

    def _wait_for_user_input(self, prompt: str):
        """等待用户输入"""
        self.waiting_for_input = True
        self.is_paused = True
        self._notify_status(f"🟡 等待用户输入: {prompt}")

    def provide_user_input(self, text: str):
        """提供用户输入"""
        with self._lock:
            if self.waiting_for_input:
                self.user_input = text
                self.waiting_for_input = False
                self.is_paused = False
                self._notify_status("🟢 已收到用户输入，继续执行")

    def _handle_auto_reply(self, screenshot: Image.Image, question: str):
        """生成自动回复"""
        self._notify_status(f"🤖 正在生成自动回复: {question}")
        # 简化处理：直接跳过
        logger.info(f"自动回复功能暂未实现，问题: {question}")

    def auto_run(self, max_steps: int = 50, step_delay: float = 1.0) -> Generator[StepResult, None, None]:
        """自动执行直到终止"""
        for _ in range(max_steps):
            if self.should_stop or not self.is_running:
                break

            if self.is_paused:
                logger.info("检测到暂停，退出")
                return

            result = self.step()
            if result:
                yield result

                if result.action_type == "terminate":
                    break
            else:
                if self.is_paused or self.should_stop:
                    return

            # 延迟
            delay_elapsed = 0.0
            while delay_elapsed < step_delay:
                if self.should_stop or self.is_paused:
                    break
                time.sleep(0.1)
                delay_elapsed += 0.1

    def pause(self) -> str:
        """暂停任务"""
        with self._lock:
            if self.is_running:
                self.is_paused = True
                self.paused_session_id = self.session_id
                status = f"⏸ 已暂停 (Session: {self.session_id[:8] if self.session_id else 'unknown'}...)"
                self._notify_status(status)
                return status
            return "⚪ 没有运行中的任务"

    def resume(self, injection: str = None):
        """恢复任务"""
        with self._lock:
            if self.is_running and self.is_paused:
                if injection:
                    self.pending_user_feedback = injection
                    logger.info(f"用户注入指令: {injection}")
                self.is_paused = False
                self.paused_session_id = None
                self._notify_status("▶ 任务已恢复")

    def stop(self):
        """停止任务"""
        with self._lock:
            self.should_stop = True
            self.is_running = False
            self.is_paused = False
            self.paused_session_id = None
            self._notify_status("⏹ 任务已停止")

    def clear_pause_state(self):
        """清除暂停状态"""
        with self._lock:
            self.is_paused = False
            self.paused_session_id = None

    def _finish_task(self, status: str):
        """结束任务"""
        with self._lock:
            if self.task_start_time:
                elapsed = time.time() - self.task_start_time
                logger.info(f"任务完成: 耗时 {elapsed:.2f}秒, 步数 {self.step_count}")
            self.is_running = False
            self.is_paused = False
            self._notify_status(f"⚪ 任务已完成: {status}")

    def _notify_status(self, status: str):
        """通知状态变化"""
        if self.on_status_change:
            self.on_status_change(status)
        logger.info(status)

    def get_status(self) -> str:
        """获取当前状态"""
        if self.waiting_for_input:
            return "🟡 等待输入"
        elif self.is_paused:
            return "⏸ 已暂停"
        elif self.is_running:
            return "🟢 运行中"
        else:
            return "⚪ 就绪"


# ==================== 全局单例 ====================
_runner: Optional[AgentRunner] = None


def get_runner() -> AgentRunner:
    """获取全局 AgentRunner 实例"""
    global _runner
    if _runner is None:
        _runner = AgentRunner()
    return _runner


def reset_runner(**kwargs) -> AgentRunner:
    """重置全局 AgentRunner"""
    global _runner
    _runner = AgentRunner(**kwargs)
    return _runner
