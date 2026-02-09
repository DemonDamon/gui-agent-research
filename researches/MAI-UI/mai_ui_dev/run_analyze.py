#!/usr/bin/env python3
"""
MAI-UI 数据分析脚本

对采集和打标的数据进行统计分析、筛选和报告生成。

使用方法:
    python run_analyze.py                    # 生成完整报告
    python run_analyze.py --filter-only     # 只筛选数据
    python run_analyze.py --export-list     # 导出成功列表
"""

import argparse
import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from automation.statistics import DataStatistics, OverallStatistics
from automation.data_filter import DataFilter, FilterCriteria
from automation.report_generator import ReportGenerator
from automation.utils.logger import get_logger


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="MAI-UI 数据分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_analyze.py                           # 生成完整报告
  python run_analyze.py --min-quality 7            # 筛选高质量数据
  python run_analyze.py --export-success           # 导出成功的session列表
  python run_analyze.py --filter --success true    # 筛选成功的数据
        """
    )

    parser.add_argument(
        "--collected-dir",
        type=str,
        default="data/collected",
        help="采集数据目录"
    )

    parser.add_argument(
        "--labeled-dir",
        type=str,
        default="data/labeled",
        help="打标数据目录"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/reports",
        help="报告输出目录"
    )

    # 筛选选项
    parser.add_argument(
        "--filter",
        action="store_true",
        help="启用筛选模式"
    )

    parser.add_argument(
        "--success",
        type=str,
        choices=["true", "false"],
        help="筛选成功/失败的数据"
    )

    parser.add_argument(
        "--min-quality",
        type=int,
        help="最低质量分数 (0-10)"
    )

    parser.add_argument(
        "--min-confidence",
        type=float,
        help="最低置信度 (0-1)"
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        help="最大步数"
    )

    # 导出选项
    parser.add_argument(
        "--export-success",
        action="store_true",
        help="导出成功的session列表"
    )

    parser.add_argument(
        "--export-list",
        action="store_true",
        help="导出数据清单CSV"
    )

    parser.add_argument(
        "--export-format",
        type=str,
        choices=["txt", "json", "csv"],
        default="txt",
        help="导出格式 (用于session列表)"
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    logger = get_logger(name="MAI-UI-Analyze")

    logger.info("=" * 60)
    logger.info("MAI-UI 数据分析工具")
    logger.info("=" * 60)
    logger.info(f"采集目录: {args.collected_dir}")
    logger.info(f"打标目录: {args.labeled_dir}")
    logger.info("=" * 60)

    # 1. 统计分析
    stats_analyzer = DataStatistics(args.collected_dir, args.labeled_dir)
    overall_stats = stats_analyzer.analyze()

    session_stats = stats_analyzer.get_session_stats()

    # 2. 生成报告
    report_gen = ReportGenerator(args.output_dir)

    # 保存统计JSON
    stats_file = report_gen.generate_statistics_json(overall_stats)
    logger.info(f"统计数据已保存: {stats_file}")

    # 生成HTML报告
    report_file = report_gen.generate_summary_report(overall_stats, session_stats)
    logger.info(f"汇总报告已生成: {report_file}")

    # 3. 筛选模式
    if args.filter:
        logger.info("\n启用筛选模式")

        criteria = FilterCriteria()

        if args.success:
            criteria.success = args.success == "true"

        if args.min_quality:
            criteria.min_quality = args.min_quality

        if args.min_confidence:
            criteria.min_confidence = args.min_confidence

        if args.max_steps:
            criteria.max_steps = args.max_steps

        data_filter = DataFilter(args.collected_dir, args.labeled_dir)
        filtered = data_filter.filter(session_stats, criteria)

        # 导出筛选结果
        timestamp = Path(stats_file).stem.replace("statistics_", "")
        data_filter.export_data_list(
            filtered,
            f"{args.output_dir}/filtered_{timestamp}.csv"
        )

    # 4. 导出成功的session列表
    if args.export_success:
        successful = stats_analyzer.get_successful_sessions()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{args.output_dir}/successful_sessions_{timestamp}.{args.export_format}"

        data_filter = DataFilter(args.collected_dir, args.labeled_dir)
        data_filter.export_session_list(
            [s for s in session_stats if s.has_label and s.success],
            output_file,
            args.export_format
        )

    # 5. 导出完整数据清单
    if args.export_list:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{args.output_dir}/data_list_{timestamp}.csv"

        data_filter = DataFilter(args.collected_dir, args.labeled_dir)
        data_filter.export_data_list(session_stats, output_file)

    # 打印摘要
    print("\n" + "=" * 60)
    print("数据摘要")
    print("=" * 60)
    print(f"总session数: {overall_stats.total_sessions}")
    print(f"  ✓ 成功: {overall_stats.successful_sessions}")
    print(f"  ✗ 失败: {overall_stats.failed_sessions}")
    print(f"  ⏳ 未打标: {overall_stats.unlabeled_sessions}")
    print(f"成功率: {overall_stats.success_rate * 100:.1f}%")
    print(f"平均质量分: {overall_stats.avg_quality_score:.1f}/10")
    print("=" * 60)

    print(f"\n报告文件:")
    print(f"  - HTML: {report_file}")
    print(f"  - JSON: {stats_file}")

    if args.export_success or args.export_list:
        print(f"\n导出文件: {args.output_dir}/")

    print("\n提示: 在浏览器中打开HTML报告查看详细数据")


if __name__ == "__main__":
    from datetime import datetime
    main()
