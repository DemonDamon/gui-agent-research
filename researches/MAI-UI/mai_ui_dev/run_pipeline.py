#!/usr/bin/env python3
"""
MAI-UI 数据采集 Pipeline 启动脚本

使用方法:
    python run_pipeline.py                    # 使用默认配置
    python run_pipeline.py --config custom.yaml    # 使用自定义配置
    python run_pipeline.py --resume           # 从检查点恢复
"""

import argparse
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "web_ui"))
sys.path.insert(0, str(project_root / "src"))

from automation.config.pipeline_config import load_config
from automation.pipeline import DataCollectionPipeline
from automation.utils.logger import get_logger


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="MAI-UI 数据采集 Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_pipeline.py                    # 使用默认配置运行
  python run_pipeline.py --config custom.yaml    # 使用自定义配置
  python run_pipeline.py --resume           # 从检查点恢复执行
  python run_pipeline.py --tasks my_tasks.jsonl  # 指定任务文件
        """
    )

    parser.add_argument(
        "--config", "-c",
        type=str,
        default="automation/config/pipeline_config.yaml",
        help="配置文件路径 (默认: automation/config/pipeline_config.yaml)"
    )

    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        help="从检查点恢复执行"
    )

    parser.add_argument(
        "--tasks", "-t",
        type=str,
        help="任务文件路径（覆盖配置文件中的设置）"
    )

    parser.add_argument(
        "--device", "-d",
        type=str,
        help="指定设备ID（覆盖配置文件中的设置）"
    )

    parser.add_argument(
        "--model", "-m",
        type=str,
        help="指定模型名称（覆盖配置文件中的设置）"
    )

    parser.add_argument(
        "--api-base",
        type=str,
        help="指定LLM API地址（覆盖配置文件中的设置）"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        help="指定输出目录（覆盖配置文件中的设置）"
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 检查配置文件是否存在
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}")
        print(f"提示: 请先创建配置文件或使用 --config 指定正确的路径")
        sys.exit(1)

    # 加载配置
    try:
        config = load_config(str(config_path))
    except Exception as e:
        print(f"错误: 加载配置文件失败: {e}")
        sys.exit(1)

    # 命令行参数覆盖
    if args.tasks:
        config.task_source.path = args.tasks
        # 根据扩展名推断类型
        if args.tasks.endswith(".txt"):
            config.task_source.type = "txt"
        elif args.tasks.endswith(".jsonl"):
            config.task_source.type = "jsonl"

    if args.device:
        config.execution.device_id = args.device

    if args.model:
        config.execution.model_name = args.model

    if args.api_base:
        config.execution.llm_base_url = args.api_base

    if args.output:
        config.execution.logs_dir = args.output
        config.reporting.output_dir = f"{args.output}/reports"

    # 设置API密钥（环境变量优先）
    judge_api_key = os.environ.get("JUDGE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if judge_api_key and config.judge.enabled:
        config.judge.api_key = judge_api_key

    # 创建日志
    logger = get_logger(
        name="MAI-UI-Pipeline",
        log_file=f"pipeline_{config.name.replace(' ', '_')}.log"
    )

    logger.info("=" * 60)
    logger.info(f"配置文件: {config_path}")
    logger.info(f"任务文件: {config.task_source.path}")
    logger.info(f"设备ID: {config.execution.device_id or '自动检测'}")
    logger.info(f"模型: {config.execution.model_name}")
    logger.info(f"输出目录: {config.execution.logs_dir}")
    logger.info(f"断点恢复: {'是' if args.resume else '否'}")
    logger.info("=" * 60)

    # 创建并运行Pipeline
    try:
        pipeline = DataCollectionPipeline(config)
        result = pipeline.run(resume=args.resume)

        # 根据结果设置退出码
        if result.failed_tasks > 0:
            sys.exit(1)  # 有失败的任务
        else:
            sys.exit(0)  # 全部成功

    except KeyboardInterrupt:
        logger.warning("\n收到中断信号，Pipeline停止")
        sys.exit(130)  # 128 + SIGINT(2)

    except Exception as e:
        logger.error(f"Pipeline执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
