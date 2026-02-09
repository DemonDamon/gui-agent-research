"""
轨迹打标器模块

使用LLM作为Judge，自动判断任务执行是否成功。
"""

import base64
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from automation.judge_prompts import JudgePrompts
from automation.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class JudgmentResult:
    """判断结果"""
    session_id: str
    instruction: str
    success: bool
    confidence: float
    reason: str
    quality_score: int
    judge_model: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "instruction": self.instruction,
            "success": self.success,
            "confidence": self.confidence,
            "reason": self.reason,
            "quality_score": self.quality_score,
            "judge_model": self.judge_model,
            "timestamp": self.timestamp
        }


@dataclass
class JudgeConfig:
    """Judge配置"""
    enabled: bool = True
    provider: str = "openai"
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"
    api_key: str = ""
    check_last_n_steps: int = 3
    require_termination: bool = True
    min_confidence: float = 0.7
    max_tokens: int = 1000
    temperature: float = 0.1
    use_vision: bool = False  # 是否使用视觉模型（传入截图）


class TrajectoryJudge:
    """
    轨迹打标器

    使用LLM分析任务执行轨迹，判断任务是否成功完成。
    """

    def __init__(self, config: JudgeConfig):
        """
        初始化打标器

        Args:
            config: Judge配置
        """
        self.config = config

        if not HAS_OPENAI:
            raise ImportError("需要安装 openai 库: pip install openai")

        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=config.api_key or os.environ.get("JUDGE_API_KEY") or os.environ.get("OPENAI_API_KEY"),
            base_url=config.api_base
        )

        logger.info(f"TrajectoryJudge初始化完成 (model: {config.model})")

    def judge_session(
        self,
        session_id: str,
        logs_dir: str = "data/collected"
    ) -> Optional[JudgmentResult]:
        """
        判断单个session的执行结果

        Args:
            session_id: Session ID
            logs_dir: 日志目录

        Returns:
            判断结果，如果失败返回None
        """
        # 1. 加载轨迹数据
        trajectory_data = self._load_trajectory(session_id, logs_dir)
        if trajectory_data is None:
            return None

        # 2. 提取关键信息
        instruction = trajectory_data.get("instruction", "")
        logs = trajectory_data.get("logs", [])

        if not logs:
            logger.warning(f"Session {session_id} 没有日志记录")
            return None

        # 3. 分析轨迹
        trajectory_summary = self._analyze_trajectory(logs)
        last_steps = logs[-self.config.check_last_n_steps:]

        # 4. 调用LLM判断
        try:
            if self.config.use_vision:
                # 使用视觉模型（传入最后一步截图）
                result = self._judge_with_vision(
                    session_id, instruction, trajectory_summary, last_steps, logs_dir
                )
            else:
                # 仅使用文本判断
                result = self._judge_text_only(
                    session_id, instruction, trajectory_summary, last_steps
                )

            # 5. 保存打标结果
            if result:
                self._save_label(result, logs_dir)

            return result

        except Exception as e:
            logger.error(f"判断Session {session_id} 失败: {e}")
            return None

    def _load_trajectory(
        self,
        session_id: str,
        logs_dir: str
    ) -> Optional[Dict[str, Any]]:
        """加载轨迹数据"""
        session_path = Path(logs_dir) / session_id
        trajectory_file = session_path / "trajectory.jsonl"

        if not trajectory_file.exists():
            logger.error(f"轨迹文件不存在: {trajectory_file}")
            return None

        logs = []
        instruction = ""

        try:
            with open(trajectory_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        log_entry = json.loads(line)
                        logs.append(log_entry)

                        # 提取任务指令
                        if not instruction and log_entry.get("instruction"):
                            instruction = log_entry["instruction"]

            return {
                "instruction": instruction,
                "logs": logs,
                "session_path": session_path
            }

        except Exception as e:
            logger.error(f"加载轨迹文件失败: {e}")
            return None

    def _analyze_trajectory(self, logs: List[Dict]) -> Dict[str, Any]:
        """分析轨迹统计信息"""
        total_steps = len(logs)

        # 统计动作类型
        action_types = {}
        has_termination = False
        termination_status = None

        for log in logs:
            action_type = log.get("action_type", "unknown")
            action_types[action_type] = action_types.get(action_type, 0) + 1

            if action_type == "terminate":
                has_termination = True
                termination_status = log.get("action", {}).get("status", "unknown")
            elif action_type == "answer":
                has_termination = True
                termination_status = "done"

        return {
            "total_steps": total_steps,
            "action_types": action_types,
            "has_termination": has_termination,
            "termination_status": termination_status
        }

    def _judge_text_only(
        self,
        session_id: str,
        instruction: str,
        trajectory_summary: Dict[str, Any],
        last_steps: List[Dict]
    ) -> Optional[JudgmentResult]:
        """仅使用文本判断"""
        # 构建摘要文本
        summary_text = JudgePrompts.build_trajectory_summary(
            **trajectory_summary
        )

        # 构建提示词
        user_prompt = JudgePrompts.build_user_prompt(
            instruction, summary_text, last_steps
        )

        # 调用LLM
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": JudgePrompts.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )

            result_text = response.choices[0].message.content.strip()
            logger.debug(f"LLM返回: {result_text}")

            # 解析结果
            parsed = self._parse_judgment(result_text)

            if parsed:
                return JudgmentResult(
                    session_id=session_id,
                    instruction=instruction,
                    success=parsed["success"],
                    confidence=parsed["confidence"],
                    reason=parsed["reason"],
                    quality_score=parsed["quality_score"],
                    judge_model=self.config.model,
                    timestamp=datetime.now().isoformat()
                )

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return None

    def _judge_with_vision(
        self,
        session_id: str,
        instruction: str,
        trajectory_summary: Dict[str, Any],
        last_steps: List[Dict],
        logs_dir: str
    ) -> Optional[JudgmentResult]:
        """使用视觉模型判断（含截图）"""
        # 获取最后一步截图
        last_step = last_steps[-1] if last_steps else None
        if not last_step:
            return self._judge_text_only(session_id, instruction, trajectory_summary, last_steps)

        screenshot_path = last_step.get("screenshot_path")
        if not screenshot_path:
            return self._judge_text_only(session_id, instruction, trajectory_summary, last_steps)

        # 读取并编码截图
        full_path = Path(logs_dir) / session_id / screenshot_path
        if not full_path.exists():
            logger.warning(f"截图不存在: {full_path}")
            return self._judge_text_only(session_id, instruction, trajectory_summary, last_steps)

        try:
            with open(full_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # 构建摘要文本
            summary_text = JudgePrompts.build_trajectory_summary(
                **trajectory_summary
            )

            # 构建多模态提示词
            messages = JudgePrompts.build_vision_prompt(
                instruction, summary_text, last_steps, image_data
            )

            # 调用LLM
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )

            result_text = response.choices[0].message.content.strip()
            logger.debug(f"LLM返回: {result_text}")

            # 解析结果
            parsed = self._parse_judgment(result_text)

            if parsed:
                return JudgmentResult(
                    session_id=session_id,
                    instruction=instruction,
                    success=parsed["success"],
                    confidence=parsed["confidence"],
                    reason=parsed["reason"],
                    quality_score=parsed["quality_score"],
                    judge_model=self.config.model,
                    timestamp=datetime.now().isoformat()
                )

        except Exception as e:
            logger.error(f"视觉判断失败: {e}")
            return self._judge_text_only(session_id, instruction, trajectory_summary, last_steps)

    def _parse_judgment(self, text: str) -> Optional[Dict[str, Any]]:
        """解析LLM返回的判断结果"""
        # 尝试提取JSON
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())

                # 验证必需字段
                if "success" in result:
                    # 设置默认值
                    result.setdefault("confidence", 0.8)
                    result.setdefault("reason", "")
                    result.setdefault("quality_score", 7)

                    return result
            except json.JSONDecodeError:
                pass

        # 尝试从文本中提取
        success = None
        for keyword in ["成功", "完成", "success", "completed"]:
            if keyword in text.lower():
                success = True
                break
        for keyword in ["失败", "未完成", "failed", "incomplete"]:
            if keyword in text.lower():
                success = False
                break

        if success is not None:
            return {
                "success": success,
                "confidence": 0.7,
                "reason": "从文本推断",
                "quality_score": 7 if success else 3
            }

        logger.warning(f"无法解析判断结果: {text}")
        return None

    def _save_label(self, result: JudgmentResult, logs_dir: str) -> None:
        """保存打标结果"""
        # 保存到 labeled 目录
        labeled_dir = Path(logs_dir).parent / "labeled" / result.session_id
        labeled_dir.mkdir(parents=True, exist_ok=True)

        label_file = labeled_dir / "label.json"

        try:
            with open(label_file, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

            logger.info(f"打标结果已保存: {label_file}")

        except Exception as e:
            logger.error(f"保存打标结果失败: {e}")

    def judge_batch(
        self,
        session_ids: List[str],
        logs_dir: str = "data/collected"
    ) -> List[JudgmentResult]:
        """
        批量判断多个session

        Args:
            session_ids: Session ID列表
            logs_dir: 日志目录

        Returns:
            判断结果列表
        """
        results = []
        total = len(session_ids)

        logger.info(f"开始批量打标 {total} 个session")

        for idx, session_id in enumerate(session_ids, 1):
            logger.info(f"[{idx}/{total}] 判断 {session_id}...")

            result = self.judge_session(session_id, logs_dir)
            if result:
                results.append(result)
                logger.info(
                    f"  结果: {'✓ 成功' if result.success else '✗ 失败'} "
                    f"(置信度: {result.confidence:.2f}, 质量: {result.quality_score}/10)"
                )
            else:
                logger.warning(f"  判断失败")

        # 汇总
        success_count = sum(1 for r in results if r.success)
        logger.info(f"\n批量打标完成:")
        logger.info(f"  总数: {len(results)}")
        logger.info(f"  成功: {success_count}")
        logger.info(f"  失败: {len(results) - success_count}")
        logger.info(f"  成功率: {success_count/len(results)*100:.1f}%")

        return results


def get_available_sessions(logs_dir: str = "data/collected") -> List[str]:
    """获取所有可用的session列表"""
    logs_path = Path(logs_dir)

    if not logs_path.exists():
        return []

    sessions = []
    for item in logs_path.iterdir():
        if item.is_dir():
            # 检查是否有trajectory.jsonl
            if (item / "trajectory.jsonl").exists():
                sessions.append(item.name)

    return sorted(sessions, reverse=True)
