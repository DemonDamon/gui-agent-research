"""
任务加载器模块

负责从不同格式的文件中加载任务列表。
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from automation.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Task:
    """
    任务数据结构

    包含任务指令
    """
    id: str  # 任务唯一ID (基于instruction的MD5哈希)
    instruction: str  # 任务指令文本


class TaskLoader:
    """
    任务加载器

    支持从txt和jsonl格式加载任务。
    """

    def __init__(self, encoding: str = "utf-8"):
        """
        初始化任务加载器

        Args:
            encoding: 文件编码
        """
        self.encoding = encoding
        self._loaded_tasks: List[Task] = []

    def load_from_file(self, filepath: str, file_type: str = None) -> List[Task]:
        """
        从文件加载任务

        Args:
            filepath: 文件路径
            file_type: 文件类型 (txt/jsonl)，如果不指定则根据扩展名推断

        Returns:
            任务列表
        """
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"任务文件不存在: {filepath}")

        # 推断文件类型
        if file_type is None:
            file_type = path.suffix.lstrip('.')

        logger.info(f"开始加载任务文件: {filepath} (类型: {file_type})")

        # 根据类型选择加载方法
        if file_type == "txt":
            tasks = self._load_txt(path)
        elif file_type == "jsonl":
            tasks = self._load_jsonl(path)
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")

        logger.info(f"成功加载 {len(tasks)} 个任务")

        self._loaded_tasks = tasks
        return tasks

    def _load_txt(self, filepath: Path) -> List[Task]:
        """
        从txt文件加载任务

        每行一个任务，格式：任务指令文本
        空行会被忽略
        """
        tasks = []

        with open(filepath, 'r', encoding=self.encoding) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # 跳过空行
                if not line:
                    continue

                task = Task(
                    id=self._generate_task_id(line),
                    instruction=line
                )
                tasks.append(task)

        return tasks

    def _load_jsonl(self, filepath: Path) -> List[Task]:
        """
        从jsonl文件加载任务

        每行一个JSON对象，格式：
        {"instruction": "任务指令"}
        """
        tasks = []

        with open(filepath, 'r', encoding=self.encoding) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line:
                    continue

                try:
                    data = json.loads(line)

                    # 解析任务指令（支持多种字段名）
                    instruction = (
                        data.get("instruction") or
                        data.get("task") or
                        data.get("prompt") or
                        data.get("text")
                    )

                    if not instruction:
                        logger.warning(f"第{line_num}行缺少instruction字段，跳过")
                        continue

                    task = Task(
                        id=self._generate_task_id(instruction),
                        instruction=instruction
                    )
                    tasks.append(task)

                except json.JSONDecodeError as e:
                    logger.warning(f"第{line_num}行JSON解析失败: {e}")
                    continue

        return tasks

    def _generate_task_id(self, instruction: str) -> str:
        """
        为任务生成唯一ID

        Args:
            instruction: 任务指令

        Returns:
            任务ID (基于指令的MD5哈希)
        """
        hash_str = hashlib.md5(
            instruction.strip().encode('utf-8')
        ).hexdigest()
        return f"task_{hash_str[:12]}"

    def get_tasks(self) -> List[Task]:
        """获取已加载的任务列表"""
        return self._loaded_tasks

    def get_task_count(self) -> int:
        """获取任务数量"""
        return len(self._loaded_tasks)
