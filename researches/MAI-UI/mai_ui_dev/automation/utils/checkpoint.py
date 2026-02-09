"""
检查点管理模块
用于保存和恢复任务执行进度
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from automation.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CheckpointData:
    """检查点数据结构"""
    pipeline_name: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    current_index: int
    completed_session_ids: List[str]
    failed_task_indices: List[int]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckpointData":
        """从字典创建实例"""
        return cls(**data)


class CheckpointManager:
    """
    检查点管理器

    负责保存和加载任务执行进度，支持断点续传
    """

    def __init__(self, checkpoint_dir: str = "data/reports"):
        """
        初始化检查点管理器

        Args:
            checkpoint_dir: 检查点文件存放目录
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def get_checkpoint_path(self, pipeline_name: str) -> Path:
        """获取指定pipeline的检查点文件路径"""
        return self.checkpoint_dir / f"{pipeline_name}_checkpoint.json"

    def save(self, data: CheckpointData) -> bool:
        """
        保存检查点

        Args:
            data: 检查点数据

        Returns:
            是否保存成功
        """
        with self._lock:
            try:
                checkpoint_path = self.get_checkpoint_path(data.pipeline_name)

                # 更新时间戳
                data.timestamp = datetime.now().isoformat()

                with open(checkpoint_path, 'w', encoding='utf-8') as f:
                    json.dump(data.to_dict(), f, ensure_ascii=False, indent=2)

                logger.info(f"检查点已保存: {checkpoint_path}")
                return True

            except Exception as e:
                logger.error(f"保存检查点失败: {e}")
                return False

    def load(self, pipeline_name: str) -> Optional[CheckpointData]:
        """
        加载检查点

        Args:
            pipeline_name: Pipeline名称

        Returns:
            检查点数据，如果不存在则返回None
        """
        with self._lock:
            try:
                checkpoint_path = self.get_checkpoint_path(pipeline_name)

                if not checkpoint_path.exists():
                    logger.info(f"检查点文件不存在: {checkpoint_path}")
                    return None

                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                checkpoint = CheckpointData.from_dict(data)
                logger.info(f"检查点已加载: {checkpoint_path}")
                logger.info(f"  - 总任务数: {checkpoint.total_tasks}")
                logger.info(f"  - 已完成: {checkpoint.completed_tasks}")
                logger.info(f"  - 已失败: {checkpoint.failed_tasks}")
                logger.info(f"  - 当前进度: {checkpoint.current_index}")

                return checkpoint

            except Exception as e:
                logger.error(f"加载检查点失败: {e}")
                return None

    def delete(self, pipeline_name: str) -> bool:
        """
        删除检查点

        Args:
            pipeline_name: Pipeline名称

        Returns:
            是否删除成功
        """
        with self._lock:
            try:
                checkpoint_path = self.get_checkpoint_path(pipeline_name)

                if checkpoint_path.exists():
                    checkpoint_path.unlink()
                    logger.info(f"检查点已删除: {checkpoint_path}")
                    return True

                return False

            except Exception as e:
                logger.error(f"删除检查点失败: {e}")
                return False
