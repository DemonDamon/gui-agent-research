"""
任务执行器模块

负责管理和执行单个或批量任务，复用现有的AgentRunner逻辑。
"""

import os
import sys
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional

# 添加必要路径
project_root = Path(__file__).parent.parent.parent
web_ui_dir = project_root / "web_ui"
src_dir = project_root / "src"

if str(web_ui_dir) not in sys.path:
    sys.path.insert(0, str(web_ui_dir))
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from automation.task_loader import Task
from automation.utils.logger import get_logger

logger = get_logger(__name__)


class ExecutionStatus(Enum):
    """任务执行状态"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    SUCCESS = "success"      # 成功完成
    FAILED = "failed"        # 执行失败
    TIMEOUT = "timeout"      # 超时
    ERROR = "error"          # 错误


@dataclass
class ExecutionResult:
    """
    单个任务执行结果

    包含任务执行的所有相关信息
    """
    task_id: str
    task_instruction: str
    status: ExecutionStatus
    session_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: float = 0.0
    steps: int = 0
    error_message: str = ""
    retry_count: int = 0

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_instruction": self.task_instruction,
            "status": self.status.value,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "steps": self.steps,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }


@dataclass
class ExecutorConfig:
    """执行器配置"""
    device_id: Optional[str] = None
    llm_base_url: str = "http://192.168.127.10:5022/v1"
    model_name: str = "MAI-UI-2B"
    logs_dir: str = "data/collected"
    max_steps: int = 50
    timeout: int = 300
    return_to_desktop: bool = True
    task_delay: float = 2.0


class TaskExecutor:
    """
    任务执行器

    管理AgentRunner的生命周期，执行任务并收集结果。
    支持进度保存、失败重试等功能。
    """

    def __init__(self, config: ExecutorConfig):
        """
        初始化任务执行器

        Args:
            config: 执行器配置
        """
        self.config = config
        self._runner = None
        self._lock = threading.Lock()

        # 确保日志目录存在
        Path(config.logs_dir).mkdir(parents=True, exist_ok=True)

        # 状态回调
        self.on_step_complete: Optional[Callable] = None
        self.on_status_change: Optional[Callable] = None

    def _init_runner(self) -> None:
        """初始化AgentRunner"""
        try:
            from agent_runner import AgentRunner

            self._runner = AgentRunner(
                llm_base_url=self.config.llm_base_url,
                model_name=self.config.model_name,
                device_id=self.config.device_id,
                logs_dir=self.config.logs_dir,
                return_to_desktop_on_start=self.config.return_to_desktop,
            )

            # 设置回调
            if self.on_step_complete:
                self._runner.on_step_complete = self.on_step_complete
            if self.on_status_change:
                self._runner.on_status_change = self.on_status_change

            logger.info("AgentRunner初始化成功")

        except ImportError as e:
            logger.error(f"无法导入AgentRunner: {e}")
            raise
        except Exception as e:
            logger.error(f"初始化AgentRunner失败: {e}")
            raise

    def execute_task(
        self,
        task: Task,
        retry_count: int = 0
    ) -> ExecutionResult:
        """
        执行单个任务

        Args:
            task: 要执行的任务
            retry_count: 当前重试次数

        Returns:
            执行结果
        """
        start_time = datetime.now()
        start_time_str = start_time.isoformat()

        logger.info(f"开始执行任务 [{task.id}]: {task.instruction[:50]}...")
        if retry_count > 0:
            logger.info(f"  (第 {retry_count + 1} 次尝试)")

        with self._lock:
            # 初始化runner
            if self._runner is None:
                self._init_runner()

            runner = self._runner

        result = ExecutionResult(
            task_id=task.id,
            task_instruction=task.instruction,
            status=ExecutionStatus.PENDING,
            start_time=start_time_str,
            retry_count=retry_count
        )

        try:
            # 启动任务
            session_id = runner.start_task(task.instruction)
            result.session_id = session_id
            result.status = ExecutionStatus.RUNNING
            logger.info(f"  Session ID: {session_id}")

            # 执行任务（带超时检测）
            step_count = 0
            start = time.time()

            for step_result in runner.auto_run(
                max_steps=self.config.max_steps,
                step_delay=1.0
            ):
                step_count += 1
                result.steps = step_count

                # 检查超时
                elapsed = time.time() - start
                if elapsed > self.config.timeout:
                    logger.warning(f"  任务超时 ({elapsed:.1f}s > {self.config.timeout}s)")
                    runner.stop()
                    result.status = ExecutionStatus.TIMEOUT
                    result.error_message = f"执行超时 ({elapsed:.1f}秒)"
                    break

                # 检查任务状态
                if step_result.action_type == "terminate":
                    status = step_result.action.get("status", "unknown")
                    if status == "done":
                        result.status = ExecutionStatus.SUCCESS
                        logger.info(f"  任务成功完成 (共{step_count}步)")
                    else:
                        result.status = ExecutionStatus.FAILED
                        result.error_message = f"任务终止状态: {status}"
                        logger.warning(f"  任务未成功完成: {status}")
                    break
                elif step_result.action_type == "answer":
                    result.status = ExecutionStatus.SUCCESS
                    logger.info(f"  任务完成并返回答案 (共{step_count}步)")
                    break

            # 等待任务完全结束
            while runner.is_running:
                time.sleep(0.1)
                elapsed = time.time() - start
                if elapsed > self.config.timeout + 10:
                    runner.stop()
                    break

            # 如果还没有设置状态（正常结束）
            if result.status == ExecutionStatus.RUNNING:
                result.status = ExecutionStatus.SUCCESS

        except Exception as e:
            logger.error(f"  执行出错: {e}")
            result.status = ExecutionStatus.ERROR
            result.error_message = str(e)

            # 停止runner
            if runner:
                runner.stop()

        finally:
            # 计算耗时
            end_time = datetime.now()
            result.end_time = end_time.isoformat()
            result.duration = (end_time - start_time).total_seconds()

            logger.info(
                f"  任务结束 [{result.status.value}] "
                f"(耗时: {result.duration:.1f}s, 步数: {result.steps})"
            )

            # 任务间延迟
            if result.status == ExecutionStatus.SUCCESS and self.config.task_delay > 0:
                logger.debug(f"  等待 {self.config.task_delay}s 后执行下一个任务")
                time.sleep(self.config.task_delay)

        return result

    def execute_batch(
        self,
        tasks: List[Task],
        max_retries: int = 2
    ) -> List[ExecutionResult]:
        """
        批量执行任务

        Args:
            tasks: 任务列表
            max_retries: 最大重试次数

        Returns:
            执行结果列表
        """
        results = []
        total = len(tasks)

        logger.info(f"开始批量执行 {total} 个任务")
        logger.info(f"  - 设备ID: {self.config.device_id or '自动检测'}")
        logger.info(f"  - 最大步数: {self.config.max_steps}")
        logger.info(f"  - 超时时间: {self.config.timeout}s")
        logger.info(f"  - 最大重试: {max_retries}")

        for idx, task in enumerate(tasks, 1):
            logger.info(f"[{idx}/{total}] 开始执行: {task.instruction[:50]}...")

            result = self.execute_task(task)

            # 失败重试
            retry = 0
            while (
                result.status in [ExecutionStatus.FAILED, ExecutionStatus.ERROR, ExecutionStatus.TIMEOUT]
                and retry < max_retries
            ):
                retry += 1
                logger.info(f"  任务失败，进行第 {retry} 次重试...")
                time.sleep(2)  # 重试前等待

                result = self.execute_task(task, retry_count=retry)

            results.append(result)

            # 显示进度
            success_count = sum(1 for r in results if r.status == ExecutionStatus.SUCCESS)
            logger.info(
                f"  当前进度: 成功 {success_count}/{idx} "
                f"({success_count/idx*100:.1f}%)"
            )

        # 汇总统计
        success_count = sum(1 for r in results if r.status == ExecutionStatus.SUCCESS)
        failed_count = sum(1 for r in results if r.status == ExecutionStatus.FAILED)
        error_count = sum(1 for r in results if r.status == ExecutionStatus.ERROR)
        timeout_count = sum(1 for r in results if r.status == ExecutionStatus.TIMEOUT)

        logger.info("\n" + "=" * 50)
        logger.info("批量执行完成")
        logger.info(f"  总任务数: {total}")
        logger.info(f"  成功: {success_count}")
        logger.info(f"  失败: {failed_count}")
        logger.info(f"  错误: {error_count}")
        logger.info(f"  超时: {timeout_count}")
        logger.info(f"  成功率: {success_count/total*100:.1f}%")
        logger.info("=" * 50)

        return results

    def get_runner(self):
        """获取底层的AgentRunner实例"""
        return self._runner

    def reset(self) -> None:
        """重置执行器"""
        with self._lock:
            if self._runner:
                self._runner.stop()
            self._runner = None
            logger.info("执行器已重置")
