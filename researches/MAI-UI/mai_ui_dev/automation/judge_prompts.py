"""
LLM Judge 提示词模板

定义用于任务执行结果判断的各种提示词模板。
"""

from typing import List, Dict, Any


class JudgePrompts:
    """Judge提示词模板类"""

    SYSTEM_PROMPT = """你是一个Android GUI任务执行质量评估专家。你的任务是分析用户给出的任务指令和Agent的执行轨迹，判断任务是否成功完成。

【评估标准】
1. 任务完成度：任务的主要目标是否达成？
2. 轨迹合理性：操作步骤是否合理、高效？
3. 异常检测：有无死循环、重复操作、无意义点击等异常？

【输出格式】
请严格按照以下JSON格式输出，不要添加任何其他内容：
```json
{{
    "success": true或false,
    "confidence": 0.0到1.0之间的数字,
    "reason": "简短判断理由（1-2句话）",
    "quality_score": 0到10之间的整数
}}
```

【评分说明】
- success: 任务是否成功完成（核心指标）
- confidence: 判断的置信度（0-1）
- reason: 判断理由
- quality_score: 轨迹质量评分（0-10分）
  - 9-10分：完美执行，步骤简洁高效
  - 7-8分：成功完成，有些许冗余
  - 5-6分：成功完成但有较多无效操作
  - 3-4分：部分完成，有明显问题
  - 1-2分：几乎失败，严重问题
"""

    @staticmethod
    def build_user_prompt(
        instruction: str,
        trajectory_summary: str,
        last_steps: List[Dict[str, Any]]
    ) -> str:
        """
        构建用户提示词

        Args:
            instruction: 任务指令
            trajectory_summary: 轨迹摘要
            last_steps: 最后N步的详细信息

        Returns:
            完整的用户提示词
        """
        prompt = f"""【任务指令】
{instruction}

【执行轨迹摘要】
{trajectory_summary}

【最后几步详细执行记录】
"""

        # 添加最后N步的详细信息
        for i, step in enumerate(last_steps, 1):
            prompt += f"\n--- 步骤 {step['step_index']} ---\n"
            prompt += f"动作类型: {step['action_type']}\n"

            if step.get('thinking'):
                thinking = step['thinking'][:200]  # 限制长度
                if len(step['thinking']) > 200:
                    thinking += "..."
                prompt += f"思考过程: {thinking}\n"

            if step.get('message'):
                prompt += f"执行结果: {step['message']}\n"

            # 标记是否有截图
            if step.get('screenshot_path'):
                prompt += f"[有截图: {step['screenshot_path']}]\n"

        prompt += """
---
请根据以上信息，分析任务是否成功完成，并按照指定的JSON格式输出判断结果。
"""

        return prompt

    @staticmethod
    def build_trajectory_summary(
        total_steps: int,
        action_types: Dict[str, int],
        has_termination: bool,
        termination_status: str = None
    ) -> str:
        """
        构建轨迹摘要

        Args:
            total_steps: 总步数
            action_types: 各类动作的统计
            has_termination: 是否有终止动作
            termination_status: 终止状态

        Returns:
            轨迹摘要字符串
        """
        summary = f"总执行步数: {total_steps}\n"
        summary += f"动作统计: "

        # 按动作类型排序
        sorted_actions = sorted(
            action_types.items(),
            key=lambda x: x[1],
            reverse=True
        )
        summary += ", ".join([f"{k}={v}" for k, v in sorted_actions[:5]])

        summary += f"\n正常终止: {'是' if has_termination else '否'}"

        if termination_status:
            summary += f"\n终止状态: {termination_status}"

        return summary

    @staticmethod
    def build_vision_prompt(
        instruction: str,
        trajectory_summary: str,
        last_steps: List[Dict[str, Any]],
        screenshot_base64: str
    ) -> List[Dict[str, Any]]:
        """
        构建多模态提示词（包含截图）

        Args:
            instruction: 任务指令
            trajectory_summary: 轨迹摘要
            last_steps: 最后N步详细信息
            screenshot_base64: 最后一步截图的base64编码

        Returns:
            OpenAI格式的消息列表
        """
        # 文本部分
        text_content = JudgePrompts.build_user_prompt(
            instruction, trajectory_summary, last_steps
        )

        # 添加截图说明
        text_content += f"\n\n【最后一步截图】\n请仔细查看最后一步的截图，结合任务指令判断任务是否成功完成。"

        messages = [
            {
                "role": "system",
                "content": JudgePrompts.SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text_content},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{screenshot_base64}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]

        return messages


