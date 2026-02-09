"""
Pipeline主模块

编排任务加载、执行、打标等整个数据采集流程。
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from automation.config.pipeline_config import PipelineConfig, load_config
from automation.task_loader import TaskLoader, Task
from automation.task_executor import TaskExecutor, ExecutorConfig, ExecutionResult, ExecutionStatus
from automation.trajectory_judge import TrajectoryJudge, JudgeConfig, JudgmentResult, get_available_sessions
from automation.utils.checkpoint import CheckpointManager, CheckpointData
from automation.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """Pipeline执行结果"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    results: List[ExecutionResult]
    start_time: str
    end_time: str
    duration: float


class DataCollectionPipeline:
    """
    数据采集Pipeline

    编排任务加载、批量执行、进度保存等完整流程。
    支持断点续传、失败重试等功能。
    """

    def __init__(self, config: PipelineConfig):
        """
        初始化Pipeline

        Args:
            config: Pipeline配置
        """
        self.config = config
        self.checkpoint_manager = CheckpointManager(config.reporting.output_dir)

        # 初始化子组件
        self.task_loader = TaskLoader(
            encoding=config.task_source.encoding
        )

        self.task_executor = None  # 延迟初始化
        self.judge = None  # Judge延迟初始化

        self.results: List[ExecutionResult] = []
        self.judgments: List[JudgmentResult] = []

    def run(self, resume: bool = False) -> PipelineResult:
        """
        运行完整的Pipeline

        Args:
            resume: 是否从检查点恢复

        Returns:
            Pipeline执行结果
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info(f"启动 {self.config.name} v{self.config.version}")
        logger.info("=" * 60)

        try:
            # 阶段1: 加载任务
            logger.info("\n【阶段 1/3】加载任务")
            tasks = self._load_tasks()

            # 阶段2: 恢复进度（如果需要）
            if resume:
                logger.info("\n【阶段 2/3】恢复进度")
                tasks = self._resume_from_checkpoint(tasks)
            else:
                # 清除旧的检查点
                self.checkpoint_manager.delete(self.config.name)

            # 阶段3: 执行任务
            logger.info("\n【阶段 3/3】执行任务")
            results = self._execute_tasks(tasks)

            # 保存结果
            self._save_results(results)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 生成Pipeline结果
            pipeline_result = PipelineResult(
                total_tasks=len(tasks),
                completed_tasks=sum(1 for r in results if r.status == ExecutionStatus.SUCCESS),
                failed_tasks=sum(1 for r in results if r.status != ExecutionStatus.SUCCESS),
                success_rate=sum(1 for r in results if r.status == ExecutionStatus.SUCCESS) / len(tasks) if tasks else 0,
                results=results,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration=duration
            )

            # 打印最终报告
            self._print_final_report(pipeline_result)

            return pipeline_result

        except Exception as e:
            logger.error(f"Pipeline执行出错: {e}", exc_info=True)
            raise

    def _load_tasks(self) -> List[Task]:
        """加载任务"""
        logger.info(f"从 {self.config.task_source.path} 加载任务...")

        tasks = self.task_loader.load_from_file(
            self.config.task_source.path,
            self.config.task_source.type
        )

        # 打印任务数量
        logger.info(f"  - 总任务数: {len(tasks)}")

        return tasks

    def _resume_from_checkpoint(self, tasks: List[Task]) -> List[Task]:
        """从检查点恢复"""
        checkpoint = self.checkpoint_manager.load(self.config.name)

        if checkpoint is None:
            logger.info("  未找到检查点，从头开始")
            return tasks

        logger.info(f"  从第 {checkpoint.current_index} 个任务继续")
        logger.info(f"  已完成: {checkpoint.completed_tasks}")
        logger.info(f"  已失败: {checkpoint.failed_tasks}")

        # 跳过已完成的任务
        if checkpoint.current_index < len(tasks):
            return tasks[checkpoint.current_index:]
        else:
            logger.info("  所有任务已完成")
            return []

    def _execute_tasks(self, tasks: List[Task]) -> List[ExecutionResult]:
        """执行任务"""
        if not tasks:
            logger.warning("没有任务需要执行")
            return []

        # 初始化执行器
        executor_config = ExecutorConfig(
            device_id=self.config.execution.device_id,
            llm_base_url=self.config.execution.llm_base_url,
            model_name=self.config.execution.model_name,
            logs_dir=self.config.execution.logs_dir,
            max_steps=self.config.execution.max_steps_per_task,
            timeout=self.config.execution.timeout_per_task,
            return_to_desktop=self.config.execution.return_to_desktop,
            task_delay=self.config.execution.task_delay,
        )

        self.task_executor = TaskExecutor(executor_config)

        # 设置进度回调
        self.task_executor.on_status_change = self._on_status_change

        # 批量执行
        results = self.task_executor.execute_batch(
            tasks=tasks,
            max_retries=self.config.execution.max_retries
        )

        return results

    def _on_status_change(self, status: str) -> None:
        """状态变化回调"""
        logger.debug(f"状态变化: {status}")

    def _save_results(self, results: List[ExecutionResult]) -> None:
        """保存执行结果"""
        if not self.config.reporting.enabled:
            return

        output_dir = Path(self.config.reporting.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存详细结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = output_dir / f"results_{timestamp}.json"

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in results], f, ensure_ascii=False, indent=2)

        logger.info(f"执行结果已保存: {result_file}")

        # 更新检查点
        checkpoint = CheckpointData(
            pipeline_name=self.config.name,
            total_tasks=len(results),
            completed_tasks=sum(1 for r in results if r.status == ExecutionStatus.SUCCESS),
            failed_tasks=sum(1 for r in results if r.status != ExecutionStatus.SUCCESS),
            current_index=len(results),
            completed_session_ids=[r.session_id for r in results if r.session_id],
            failed_task_indices=[
                i for i, r in enumerate(results)
                if r.status != ExecutionStatus.SUCCESS
            ],
            timestamp=datetime.now().isoformat()
        )

        self.checkpoint_manager.save(checkpoint)

    def _print_final_report(self, result: PipelineResult) -> None:
        """打印最终报告"""
        logger.info("\n" + "=" * 60)
        logger.info("Pipeline执行完成")
        logger.info("=" * 60)
        logger.info(f"  总任务数: {result.total_tasks}")
        logger.info(f"  成功完成: {result.completed_tasks}")
        logger.info(f"  失败/错误: {result.failed_tasks}")
        logger.info(f"  成功率: {result.success_rate * 100:.1f}%")
        logger.info(f"  总耗时: {result.duration:.1f}秒")
        logger.info(f"  平均耗时: {result.duration / result.total_tasks:.1f}秒/任务")
        logger.info("=" * 60)

    def get_results(self) -> List[ExecutionResult]:
        """获取执行结果"""
        return self.results

    # ==================== 打标相关方法 ====================

    def _init_judge(self) -> None:
        """初始化Judge"""
        if not self.config.judge.enabled:
            logger.info("打标功能未启用")
            return

        if self.judge is None:
            judge_config = JudgeConfig(
                enabled=self.config.judge.enabled,
                provider=self.config.judge.provider,
                api_base=self.config.judge.api_base,
                model=self.config.judge.model,
                api_key=self.config.judge.api_key,
                check_last_n_steps=self.config.judge.check_last_n_steps,
                require_termination=self.config.judge.require_termination,
                min_confidence=self.config.judge.min_confidence,
                max_tokens=self.config.judge.max_tokens,
                temperature=self.config.judge.temperature,
                use_vision=False  # 默认不使用视觉模型
            )

            self.judge = TrajectoryJudge(judge_config)
            logger.info("Judge初始化完成")

    def judge_sessions(
        self,
        session_ids: Optional[List[str]] = None,
        logs_dir: str = "data/collected"
    ) -> List[JudgmentResult]:
        """
        对指定的session进行打标

        Args:
            session_ids: Session ID列表，如果为None则处理所有session
            logs_dir: 日志目录

        Returns:
            打标结果列表
        """
        # 初始化Judge
        self._init_judge()

        if not self.config.judge.enabled or self.judge is None:
            logger.warning("打标功能未启用")
            return []

        # 获取要处理的session列表
        if session_ids is None:
            session_ids = get_available_sessions(logs_dir)
            logger.info(f"找到 {len(session_ids)} 个session")

        if not session_ids:
            logger.warning("没有需要打标的session")
            return []

        # 批量打标
        results = self.judge.judge_batch(session_ids, logs_dir)
        self.judgments.extend(results)

        return results

    def judge_results(
        self,
        logs_dir: str = "data/collected"
    ) -> List[JudgmentResult]:
        """
        对最近执行的任务结果进行打标

        Args:
            logs_dir: 日志目录

        Returns:
            打标结果列表
        """
        if not self.results:
            logger.warning("没有执行结果可以打标")
            return []

        # 提取成功的session_id
        session_ids = [
            r.session_id for r in self.results
            if r.session_id and r.status == ExecutionStatus.SUCCESS
        ]

        if not session_ids:
            logger.warning("没有成功完成的session")
            return []

        logger.info(f"对 {len(session_ids)} 个成功完成的session进行打标")

        return self.judge_sessions(session_ids, logs_dir)
