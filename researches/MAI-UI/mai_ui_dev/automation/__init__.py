"""
MAI-UI 自动化数据采集 Pipeline

本模块提供批量任务执行、自动打标、数据分析等功能。
"""

__version__ = "1.0.0"

from automation.task_loader import TaskLoader, Task
from automation.task_executor import TaskExecutor, ExecutionResult, ExecutionStatus
from automation.trajectory_judge import TrajectoryJudge, JudgeConfig, JudgmentResult, get_available_sessions
from automation.statistics import DataStatistics, OverallStatistics, SessionStats
from automation.data_filter import DataFilter, FilterCriteria
from automation.report_generator import ReportGenerator
from automation.pipeline import DataCollectionPipeline

__all__ = [
    "TaskLoader",
    "Task",
    "TaskExecutor",
    "ExecutionResult",
    "ExecutionStatus",
    "TrajectoryJudge",
    "JudgeConfig",
    "JudgmentResult",
    "get_available_sessions",
    "DataStatistics",
    "OverallStatistics",
    "SessionStats",
    "DataFilter",
    "FilterCriteria",
    "ReportGenerator",
    "DataCollectionPipeline",
]
