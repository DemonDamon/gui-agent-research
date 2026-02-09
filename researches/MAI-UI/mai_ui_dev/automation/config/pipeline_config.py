"""
Pipeline配置管理模块
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TaskSourceConfig:
    """任务源配置"""
    type: str = "jsonl"  # txt 或 jsonl
    path: str = "tasks/tasks.jsonl"
    encoding: str = "utf-8"


@dataclass
class ExecutionConfig:
    """执行配置"""
    device_id: Optional[str] = None
    max_parallel_tasks: int = 1
    max_steps_per_task: int = 50
    timeout_per_task: int = 300  # 秒
    max_retries: int = 2
    retry_delay: int = 5

    # Agent配置
    llm_base_url: str = "http://192.168.127.10:5022/v1"
    model_name: str = "MAI-UI-2B"

    # 日志配置
    logs_dir: str = "data/collected"
    return_to_desktop: bool = True
    task_delay: float = 2.0


@dataclass
class JudgeConfig:
    """打标配置"""
    enabled: bool = True
    provider: str = "openai"
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"
    api_key: str = ""

    # 判断策略
    check_last_n_steps: int = 3
    require_termination: bool = True
    min_confidence: float = 0.7
    use_vision: bool = False  # 是否使用视觉模型（传入截图）

    # 成本控制
    max_tokens: int = 1000
    temperature: float = 0.1


@dataclass
class ReportingConfig:
    """报告配置"""
    enabled: bool = True
    output_dir: str = "data/reports"
    generate_plots: bool = False


@dataclass
class PipelineConfig:
    """Pipeline总配置"""

    name: str = "MAI-UI数据采集Pipeline"
    version: str = "1.0.0"

    # 子配置
    task_source: TaskSourceConfig = field(default_factory=TaskSourceConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    judge: JudgeConfig = field(default_factory=JudgeConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        """从字典创建配置"""
        config = cls()

        # 更新基本配置
        if "name" in data:
            config.name = data["name"]
        if "version" in data:
            config.version = data["version"]

        # 更新子配置
        if "task_source" in data:
            config.task_source = TaskSourceConfig(**data["task_source"])
        if "execution" in data:
            config.execution = ExecutionConfig(**data["execution"])
        if "judge" in data:
            config.judge = JudgeConfig(**data["judge"])
        if "reporting" in data:
            config.reporting = ReportingConfig(**data["reporting"])

        return config

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "task_source": self.task_source.__dict__,
            "execution": self.execution.__dict__,
            "judge": self.judge.__dict__,
            "reporting": self.reporting.__dict__,
        }


def load_config(config_path: str) -> PipelineConfig:
    """
    从YAML文件加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        PipelineConfig实例
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 处理 YAML 中有 pipeline 顶层键的情况
    if "pipeline" in data:
        data = data["pipeline"]

    return PipelineConfig.from_dict(data)


def save_config(config: PipelineConfig, config_path: str) -> None:
    """
    保存配置到YAML文件

    Args:
        config: Pipeline配置
        config_path: 保存路径
    """
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config.to_dict(), f, allow_unicode=True, default_flow_style=False)
