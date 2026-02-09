"""
数据筛选模块

根据条件筛选session，导出可用的数据列表。
"""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from automation.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FilterCriteria:
    """筛选条件"""
    has_label: Optional[bool] = None         # 是否有打标
    success: Optional[bool] = None           # 是否成功
    min_confidence: Optional[float] = None  # 最低置信度
    min_quality: Optional[int] = None       # 最低质量分
    max_steps: Optional[int] = None         # 最大步数
    min_steps: Optional[int] = None         # 最小步数
    has_termination: Optional[bool] = None  # 是否正常终止


class DataFilter:
    """数据筛选器"""

    def __init__(
        self,
        collected_dir: str = "data/collected",
        labeled_dir: str = "data/labeled"
    ):
        """
        初始化筛选器

        Args:
            collected_dir: 采集数据目录
            labeled_dir: 打标数据目录
        """
        self.collected_dir = Path(collected_dir)
        self.labeled_dir = Path(labeled_dir)

    def filter(
        self,
        session_stats: List,
        criteria: FilterCriteria
    ) -> List:
        """
        根据条件筛选session

        Args:
            session_stats: Session统计列表
            criteria: 筛选条件

        Returns:
            符合条件的session列表
        """
        results = []

        for stat in session_stats:
            if self._match_criteria(stat, criteria):
                results.append(stat)

        logger.info(f"筛选结果: {len(results)} / {len(session_stats)} 个session符合条件")
        return results

    def _match_criteria(self, stat, criteria: FilterCriteria) -> bool:
        """判断是否匹配筛选条件"""
        # has_label
        if criteria.has_label is not None:
            if stat.has_label != criteria.has_label:
                return False

        # success (只在有打标时判断)
        if criteria.success is not None:
            if not stat.has_label:
                return False
            if stat.success != criteria.success:
                return False

        # min_confidence
        if criteria.min_confidence is not None:
            if stat.confidence is None or stat.confidence < criteria.min_confidence:
                return False

        # min_quality
        if criteria.min_quality is not None:
            if stat.quality_score is None or stat.quality_score < criteria.min_quality:
                return False

        # max_steps
        if criteria.max_steps is not None:
            if stat.steps > criteria.max_steps:
                return False

        # min_steps
        if criteria.min_steps is not None:
            if stat.steps < criteria.min_steps:
                return False

        # has_termination
        if criteria.has_termination is not None:
            if stat.has_termination != criteria.has_termination:
                return False

        return True

    def export_session_list(
        self,
        sessions: List,
        output_path: str,
        format: str = "txt"
    ) -> None:
        """
        导出session ID列表

        Args:
            sessions: session列表
            output_path: 输出文件路径
            format: 输出格式 (txt/json/csv)
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        session_ids = [s.session_id for s in sessions]

        if format == "txt":
            with open(output_file, 'w', encoding='utf-8') as f:
                for sid in session_ids:
                    f.write(f"{sid}\n")

        elif format == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(session_ids, f, indent=2)

        elif format == "csv":
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["session_id"])
                for sid in session_ids:
                    writer.writerow([sid])

        logger.info(f"已导出 {len(session_ids)} 个session到: {output_file}")

    def export_data_list(
        self,
        sessions: List,
        output_path: str
    ) -> None:
        """
        导出详细数据清单（CSV格式）

        Args:
            sessions: session统计列表
            output_path: 输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow([
                "session_id",
                "instruction",
                "has_label",
                "success",
                "confidence",
                "quality_score",
                "steps",
                "duration",
                "status"
            ])

            # 写入数据
            for s in sessions:
                writer.writerow([
                    s.session_id,
                    s.instruction,
                    "是" if s.has_label else "否",
                    "成功" if s.success else "失败" if s.has_label else "未知",
                    f"{s.confidence:.2f}" if s.confidence else "",
                    s.quality_score if s.quality_score is not None else "",
                    s.steps,
                    f"{s.duration:.1f}" if s.duration else "",
                    s.get_status_text()
                ])

        logger.info(f"已导出数据清单到: {output_file}")
