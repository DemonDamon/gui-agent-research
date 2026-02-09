"""
数据统计模块

对采集和打标的数据进行统计分析。
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from automation.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SessionStats:
    """单个Session的统计信息"""
    session_id: str
    instruction: str
    has_label: bool = False
    success: Optional[bool] = None
    confidence: Optional[float] = None
    quality_score: Optional[int] = None
    steps: int = 0
    duration: Optional[float] = None
    has_termination: bool = False
    termination_status: Optional[str] = None
    timestamp: Optional[str] = None

    def is_labeled(self) -> bool:
        """是否有打标结果"""
        return self.has_label

    def is_success(self) -> Optional[bool]:
        """是否成功（有打标才有值）"""
        return self.success if self.has_label else None

    def get_status_text(self) -> str:
        """获取状态文本"""
        if not self.has_label:
            return "未打标"
        return "成功" if self.success else "失败"


@dataclass
class OverallStatistics:
    """总体统计数据"""
    total_sessions: int = 0
    labeled_sessions: int = 0
    successful_sessions: int = 0
    failed_sessions: int = 0
    unlabeled_sessions: int = 0

    # 质量相关
    avg_confidence: float = 0.0
    avg_quality_score: float = 0.0
    quality_distribution: Dict[str, int] = field(default_factory=dict)

    # 执行相关
    avg_steps: float = 0.0
    avg_duration: float = 0.0

    # 终止相关
    termination_rate: float = 0.0

    # 时间范围
    earliest_time: Optional[str] = None
    latest_time: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_sessions": self.total_sessions,
            "labeled_sessions": self.labeled_sessions,
            "successful_sessions": self.successful_sessions,
            "failed_sessions": self.failed_sessions,
            "unlabeled_sessions": self.unlabeled_sessions,
            "success_rate": self.success_rate,
            "label_rate": self.label_rate,
            "avg_confidence": self.avg_confidence,
            "avg_quality_score": self.avg_quality_score,
            "quality_distribution": self.quality_distribution,
            "avg_steps": self.avg_steps,
            "avg_duration": self.avg_duration,
            "termination_rate": self.termination_rate,
            "earliest_time": self.earliest_time,
            "latest_time": self.latest_time,
        }

    @property
    def success_rate(self) -> float:
        """成功率（基于已打标的数据）"""
        if self.labeled_sessions == 0:
            return 0.0
        return self.successful_sessions / self.labeled_sessions

    @property
    def label_rate(self) -> float:
        """打标率"""
        if self.total_sessions == 0:
            return 0.0
        return self.labeled_sessions / self.total_sessions


class DataStatistics:
    """数据统计分析器"""

    def __init__(
        self,
        collected_dir: str = "data/collected",
        labeled_dir: str = "data/labeled"
    ):
        """
        初始化统计分析器

        Args:
            collected_dir: 采集数据目录
            labeled_dir: 打标数据目录
        """
        self.collected_dir = Path(collected_dir)
        self.labeled_dir = Path(labeled_dir)
        self.session_stats: List[SessionStats] = []

    def analyze(self) -> OverallStatistics:
        """
        分析所有数据

        Returns:
            总体统计数据
        """
        logger.info("开始分析数据...")

        # 1. 扫描所有session
        self._scan_sessions()

        # 2. 计算总体统计
        stats = self._calculate_overall_stats()

        logger.info(f"分析完成: 共 {stats.total_sessions} 个session")
        logger.info(f"  已打标: {stats.labeled_sessions}")
        logger.info(f"  成功: {stats.successful_sessions}")
        logger.info(f"  失败: {stats.failed_sessions}")
        logger.info(f"  成功率: {stats.success_rate * 100:.1f}%")

        return stats

    def _scan_sessions(self) -> None:
        """扫描所有session，收集统计信息"""
        self.session_stats = []

        # 扫描采集目录
        if not self.collected_dir.exists():
            logger.warning(f"采集目录不存在: {self.collected_dir}")
            return

        for session_path in self.collected_dir.iterdir():
            if not session_path.is_dir():
                continue

            session_id = session_path.name
            trajectory_file = session_path / "trajectory.jsonl"

            if not trajectory_file.exists():
                continue

            # 读取轨迹数据
            session_stat = self._parse_session(session_id, trajectory_file)
            if session_stat:
                # 检查是否有打标
                label_file = self.labeled_dir / session_id / "label.json"
                if label_file.exists():
                    self._merge_label(session_stat, label_file)

                self.session_stats.append(session_stat)

    def _parse_session(
        self,
        session_id: str,
        trajectory_file: Path
    ) -> Optional[SessionStats]:
        """解析单个session的轨迹数据"""
        logs = []
        instruction = ""
        timestamps = []

        try:
            with open(trajectory_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        log = json.loads(line)
                        logs.append(log)

                        if not instruction and log.get("instruction"):
                            instruction = log["instruction"]

                        if log.get("timestamp"):
                            timestamps.append(log["timestamp"])

        except Exception as e:
            logger.error(f"解析 {session_id} 失败: {e}")
            return None

        if not logs:
            return None

        # 统计信息
        has_termination = any(
            log.get("action_type") in ["terminate", "answer"]
            for log in logs
        )
        termination_status = None
        for log in logs:
            if log.get("action_type") == "terminate":
                termination_status = log.get("action", {}).get("status")
                break
            elif log.get("action_type") == "answer":
                termination_status = "done"
                break

        # 计算耗时
        duration = None
        if timestamps:
            try:
                start = datetime.fromisoformat(timestamps[0])
                end = datetime.fromisoformat(timestamps[-1])
                duration = (end - start).total_seconds()
            except:
                pass

        return SessionStats(
            session_id=session_id,
            instruction=instruction,
            steps=len(logs),
            duration=duration,
            has_termination=has_termination,
            termination_status=termination_status,
            timestamp=timestamps[0] if timestamps else None
        )

    def _merge_label(
        self,
        session_stat: SessionStats,
        label_file: Path
    ) -> None:
        """合并打标结果"""
        try:
            with open(label_file, 'r', encoding='utf-8') as f:
                label = json.load(f)

            session_stat.has_label = True
            session_stat.success = label.get("success", False)
            session_stat.confidence = label.get("confidence")
            session_stat.quality_score = label.get("quality_score")

        except Exception as e:
            logger.error(f"读取打标 {label_file} 失败: {e}")

    def _calculate_overall_stats(self) -> OverallStatistics:
        """计算总体统计"""
        stats = OverallStatistics()

        if not self.session_stats:
            return stats

        stats.total_sessions = len(self.session_stats)

        # 分类统计
        labeled = [s for s in self.session_stats if s.has_label]
        unlabeled = [s for s in self.session_stats if not s.has_label]
        successful = [s for s in labeled if s.success]
        failed = [s for s in labeled if not s.success]

        stats.labeled_sessions = len(labeled)
        stats.unlabeled_sessions = len(unlabeled)
        stats.successful_sessions = len(successful)
        stats.failed_sessions = len(failed)

        # 质量统计
        if labeled:
            stats.avg_confidence = sum(s.confidence or 0 for s in labeled) / len(labeled)
            stats.avg_quality_score = sum(s.quality_score or 0 for s in labeled) / len(labeled)

            # 质量分布
            for s in labeled:
                if s.quality_score is not None:
                    if s.quality_score >= 9:
                        key = "优秀(9-10)"
                    elif s.quality_score >= 7:
                        key = "良好(7-8)"
                    elif s.quality_score >= 5:
                        key = "中等(5-6)"
                    elif s.quality_score >= 3:
                        key = "较差(3-4)"
                    else:
                        key = "很差(0-2)"
                    stats.quality_distribution[key] = stats.quality_distribution.get(key, 0) + 1

        # 执行统计
        all_steps = [s.steps for s in self.session_stats]
        stats.avg_steps = sum(all_steps) / len(all_steps) if all_steps else 0

        durations = [s.duration for s in self.session_stats if s.duration]
        stats.avg_duration = sum(durations) / len(durations) if durations else 0

        terminated = [s for s in self.session_stats if s.has_termination]
        stats.termination_rate = len(terminated) / len(self.session_stats) if self.session_stats else 0

        # 时间范围
        timestamps = [s.timestamp for s in self.session_stats if s.timestamp]
        if timestamps:
            stats.earliest_time = min(timestamps)
            stats.latest_time = max(timestamps)

        return stats

    def get_session_stats(self) -> List[SessionStats]:
        """获取所有session的统计信息"""
        return self.session_stats

    def get_successful_sessions(self) -> List[str]:
        """获取成功的session ID列表"""
        return [
            s.session_id for s in self.session_stats
            if s.has_label and s.success
        ]

    def get_failed_sessions(self) -> List[str]:
        """获取失败的session ID列表"""
        return [
            s.session_id for s in self.session_stats
            if s.has_label and not s.success
        ]

    def get_unlabeled_sessions(self) -> List[str]:
        """获取未打标的session ID列表"""
        return [
            s.session_id for s in self.session_stats
            if not s.has_label
        ]
