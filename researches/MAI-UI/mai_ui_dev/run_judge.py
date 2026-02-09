#!/usr/bin/env python3
"""
MAI-UI 数据打标脚本

使用LLM作为Judge，对已采集的任务执行结果进行自动打标。

使用方法:
    python run_judge.py                            # 打标所有session
    python run_judge.py --session 20250206_120000  # 打标指定session
    python run_judge.py --limit 10                 # 只打标最近10个
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
from automation.trajectory_judge import TrajectoryJudge, JudgeConfig, get_available_sessions
from automation.utils.logger import get_logger


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="MAI-UI 数据打标工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_judge.py                            # 打标所有session
  python run_judge.py --session 20250206_120000  # 打标指定session
  python run_judge.py --limit 10                 # 只打标最近10个
  python run_judge.py --model gpt-4o             # 指定模型
        """
    )

    parser.add_argument(
        "--config", "-c",
        type=str,
        default="automation/config/pipeline_config.yaml",
        help="配置文件路径"
    )

    parser.add_argument(
        "--session", "-s",
        type=str,
        help="指定单个session ID进行打标"
    )

    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="限制处理的session数量"
    )

    parser.add_argument(
        "--logs-dir",
        type=str,
        default="data/collected",
        help="数据目录"
    )

    parser.add_argument(
        "--model", "-m",
        type=str,
        help="指定LLM模型（覆盖配置文件）"
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="指定API密钥"
    )

    parser.add_argument(
        "--api-base",
        type=str,
        help="指定API地址"
    )

    parser.add_argument(
        "--vision",
        action="store_true",
        help="启用视觉模型（传入截图）"
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 加载配置
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"错误: 加载配置文件失败: {e}")
        sys.exit(1)

    # 命令行参数覆盖
    if args.model:
        config.judge.model = args.model
    if args.api_base:
        config.judge.api_base = args.api_base
    if args.vision:
        config.judge.use_vision = True

    # 设置API密钥（环境变量优先）
    api_key = (
        args.api_key or
        os.environ.get("JUDGE_API_KEY") or
        os.environ.get("OPENAI_API_KEY") or
        config.judge.api_key
    )

    config.judge.api_key = api_key

    if not api_key:
        print("错误: 未设置API密钥")
        print("请通过以下方式之一设置:")
        print("  1. 环境变量: export JUDGE_API_KEY=sk-xxx")
        print("  2. 环境变量: export OPENAI_API_KEY=sk-xxx")
        print("  3. 命令行: --api-key sk-xxx")
        print("  4. 配置文件: automation/config/pipeline_config.yaml")
        sys.exit(1)

    # 创建日志
    logger = get_logger(
        name="MAI-UI-Judge",
        log_file="judge.log"
    )

    logger.info("=" * 60)
    logger.info("MAI-UI 数据打标工具")
    logger.info("=" * 60)
    logger.info(f"配置文件: {args.config}")
    logger.info(f"数据目录: {args.logs_dir}")
    logger.info(f"Judge模型: {config.judge.model}")
    logger.info(f"视觉模式: {'是' if config.judge.use_vision else '否'}")
    logger.info("=" * 60)

    # 初始化Judge
    try:
        judge_config = JudgeConfig(
            enabled=config.judge.enabled,
            provider=config.judge.provider,
            api_base=config.judge.api_base,
            model=config.judge.model,
            api_key=config.judge.api_key,
            check_last_n_steps=config.judge.check_last_n_steps,
            require_termination=config.judge.require_termination,
            min_confidence=config.judge.min_confidence,
            max_tokens=config.judge.max_tokens,
            temperature=config.judge.temperature,
            use_vision=config.judge.use_vision
        )

        judge = TrajectoryJudge(judge_config)

    except Exception as e:
        logger.error(f"初始化Judge失败: {e}")
        sys.exit(1)

    # 获取要处理的session列表
    if args.session:
        session_ids = [args.session]
        logger.info(f"指定单个session: {args.session}")
    else:
        session_ids = get_available_sessions(args.logs_dir)
        logger.info(f"找到 {len(session_ids)} 个session")

        if args.limit:
            session_ids = session_ids[:args.limit]
            logger.info(f"限制处理数量: {len(session_ids)}")

    if not session_ids:
        logger.warning("没有找到需要打标的session")
        sys.exit(0)

    # 执行打标
    try:
        results = judge.judge_batch(session_ids, args.logs_dir)

        # 打印汇总
        logger.info("\n" + "=" * 60)
        logger.info("打标完成")
        logger.info("=" * 60)

        if results:
            success_count = sum(1 for r in results if r.success)
            avg_confidence = sum(r.confidence for r in results) / len(results)
            avg_quality = sum(r.quality_score for r in results) / len(results)

            logger.info(f"  总数: {len(results)}")
            logger.info(f"  成功: {success_count}")
            logger.info(f"  失败: {len(results) - success_count}")
            logger.info(f"  平均置信度: {avg_confidence:.2f}")
            logger.info(f"  平均质量分: {avg_quality:.1f}/10")

            # 打印失败的session
            failed = [r.session_id for r in results if not r.success]
            if failed:
                logger.info(f"\n失败的session ({len(failed)}):")
                for sid in failed[:10]:  # 最多显示10个
                    logger.info(f"  - {sid}")
                if len(failed) > 10:
                    logger.info(f"  ... 还有 {len(failed) - 10} 个")

        logger.info("=" * 60)

        # 打标结果存储在 data/labeled/{session_id}/label.json

    except KeyboardInterrupt:
        logger.warning("\n收到中断信号")
        sys.exit(130)

    except Exception as e:
        logger.error(f"打标失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
