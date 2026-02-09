"""
报告生成模块

生成HTML格式的数据报告，便于人工审核。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from automation.utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """报告生成器"""

    def __init__(self, output_dir: str = "data/reports"):
        """
        初始化报告生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_summary_report(
        self,
        stats: Any,
        session_stats: List,
        output_path: str = None
    ) -> str:
        """
        生成汇总报告

        Args:
            stats: 总体统计数据
            session_stats: session统计列表
            output_path: 输出文件路径

        Returns:
            生成的报告文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"summary_{timestamp}.html"
        else:
            output_path = Path(output_path)

        # 分组数据
        successful = [s for s in session_stats if s.has_label and s.success]
        failed = [s for s in session_stats if s.has_label and not s.success]
        unlabeled = [s for s in session_stats if not s.has_label]

        # 生成HTML
        html = self._build_html_template(stats, successful, failed, unlabeled)

        # 保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"报告已生成: {output_path}")
        return str(output_path)

    def _build_html_template(
        self,
        stats: Any,
        successful: List,
        failed: List,
        unlabeled: List
    ) -> str:
        """构建HTML模板"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MAI-UI 数据采集报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 20px; }}
        h2 {{ color: #555; margin-top: 30px; margin-bottom: 15px; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-label {{ color: #888; font-size: 14px; }}
        .stat-value {{ color: #333; font-size: 28px; font-weight: bold; margin-top: 5px; }}
        .stat-value.success {{ color: #4CAF50; }}
        .stat-value.fail {{ color: #f44336; }}
        .stat-value.pending {{ color: #FF9800; }}

        .session-list {{ background: white; border-radius: 8px; overflow: hidden; }}
        .session-item {{
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .session-item:last-child {{ border-bottom: none; }}
        .session-item:hover {{ background: #f9f9f9; }}

        .session-info {{ flex: 1; }}
        .session-id {{ font-weight: bold; color: #333; }}
        .session-instruction {{ color: #666; font-size: 14px; margin-top: 4px; }}
        .session-meta {{ color: #999; font-size: 12px; margin-top: 4px; }}

        .session-badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-success {{ background: #E8F5E9; color: #2E7D32; }}
        .badge-fail {{ background: #FFEBEE; color: #C62828; }}
        .badge-pending {{ background: #FFF3E0; color: #E65100; }}

        .quality-bar {{
            width: 100px;
            height: 8px;
            background: #eee;
            border-radius: 4px;
            overflow: hidden;
            margin-left: 10px;
        }}
        .quality-fill {{ height: 100%; transition: width 0.3s; }}
        .quality-high {{ background: linear-gradient(90deg, #4CAF50, #8BC34A); }}
        .quality-medium {{ background: linear-gradient(90deg, #FFC107, #FFEB3B); }}
        .quality-low {{ background: linear-gradient(90deg, #f44336, #FF5722); }}

        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 MAI-UI 数据采集报告</h1>
        <p style="color: #666; margin-bottom: 30px;">
            生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </p>

        <!-- 统计卡片 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">总session数</div>
                <div class="stat-value">{stats.total_sessions}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">已打标</div>
                <div class="stat-value">{stats.labeled_sessions}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">成功</div>
                <div class="stat-value success">{stats.successful_sessions}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">失败</div>
                <div class="stat-value fail">{stats.failed_sessions}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">成功率</div>
                <div class="stat-value {'success' if stats.success_rate >= 0.7 else 'fail'}">{stats.success_rate * 100:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">平均质量分</div>
                <div class="stat-value">{stats.avg_quality_score:.1f}/10</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">平均步数</div>
                <div class="stat-value">{stats.avg_steps:.1f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">终止率</div>
                <div class="stat-value">{stats.termination_rate * 100:.1f}%</div>
            </div>
        </div>

        <!-- 成功的session -->
        <h2>✅ 成功的任务 ({len(successful)})</h2>
        {self._render_session_list(successful, 'success')}

        <!-- 失败的session -->
        <h2>❌ 失败的任务 ({len(failed)})</h2>
        {self._render_session_list(failed, 'fail')}

        <!-- 未打标的session -->
        <h2>⏳ 未打标的任务 ({len(unlabeled)})</h2>
        {self._render_session_list(unlabeled, 'pending')}

    </div>
</body>
</html>"""

    def _render_session_list(self, sessions: List, status: str) -> str:
        """渲染session列表"""
        if not sessions:
            return '<div class="empty-state">暂无数据</div>'

        items = []
        for s in sessions[:100]:  # 最多显示100个
            badge_class = f"badge-{status}"

            if status == 'pending':
                badge_text = "未打标"
                quality_bar = ""
            else:
                badge_text = "成功" if s.success else "失败"
                quality_bar = self._render_quality_bar(s.quality_score)

            items.append(f"""
                <div class="session-item">
                    <div class="session-info">
                        <div class="session-id">{s.session_id}</div>
                        <div class="session-instruction">{self._escape_html(s.instruction)}</div>
                        <div class="session-meta">
                            {s.steps}步 | {f"{s.duration:.1f}秒" if s.duration else "无耗时数据"}
                            {f" | 质量: {s.quality_score}/10" if s.quality_score is not None else ""}
                        </div>
                    </div>
                    <div style="display:flex;align-items:center;">
                        <span class="session-badge {badge_class}">{badge_text}</span>
                        {quality_bar}
                    </div>
                </div>
            """)

        if len(sessions) > 100:
            items.append(f'<div class="empty-state">... 还有 {len(sessions) - 100} 个session未显示</div>')

        return f'<div class="session-list">{"".join(items)}</div>'

    def _render_quality_bar(self, score: int) -> str:
        """渲染质量条"""
        if score is None:
            return ""

        color_class = "quality-high" if score >= 7 else "quality-medium" if score >= 5 else "quality-low"
        return f'<div class="quality-bar"><div class="quality-fill {color_class}" style="width:{score * 10}%"></div></div>'

    def _escape_html(self, text: str) -> str:
        """转义HTML"""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))

    def generate_statistics_json(
        self,
        stats: Any,
        output_path: str = None
    ) -> str:
        """
        生成统计JSON文件

        Args:
            stats: 总体统计数据
            output_path: 输出文件路径

        Returns:
            生成的文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"statistics_{timestamp}.json"
        else:
            output_path = Path(output_path)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"统计JSON已生成: {output_path}")
        return str(output_path)
