"""
MAI-UI MCP Server - 通过 Model Context Protocol 暴露手机操控能力

使用 fastmcp 库将 HeadlessMAIAgent 封装为 OpenClaw 可识别的工具。
OpenClaw 通过 MCP 协议调用 perform_mobile_task，即可端到端控制 Android 设备。

启动方式::

    # 直接运行
    python openclaw/mai_mcp.py

    # 通过 MCP Inspector 调试
    npx @modelcontextprotocol/inspector python openclaw/mai_mcp.py

环境变量::

    API_BASE_URL  - vLLM 推理服务地址，默认 http://localhost:8000/v1
    API_KEY       - API Key，默认 empty
    MODEL_NAME    - 模型名称，默认 MAI-UI-8B
    DEVICE_ID     - ADB 设备 ID，留空自动检测
"""

import os
import sys
import builtins
import json
import logging

# ---------------------------------------------------------------------------
# 关键：拦截 print()，使其默认输出到 stderr
#
# MCP 协议通过 stdout 传输 JSON-RPC 消息（不能动 sys.stdout）。
# 底层模块（mai_naivigation_agent、adb_utils 等）大量使用 print() 做调试输出，
# 如果这些 print 写入 stdout 会污染 MCP 的 JSON 通道。
# 解决方案：覆写内置 print，让它默认写 stderr，而 sys.stdout 保持原样给 MCP 用。
# ---------------------------------------------------------------------------
_builtin_print = builtins.print


def _print_to_stderr(*args, **kwargs):
    """将 print() 默认输出重定向到 stderr，不影响 MCP 的 stdout JSON 通道。"""
    kwargs.setdefault("file", sys.stderr)
    _builtin_print(*args, **kwargs)


builtins.print = _print_to_stderr

# 确保项目根目录在 Python 路径中
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from mcp.server.fastmcp import FastMCP
from openclaw.headless_runner import HeadlessMAIAgent

# ---------------------------------------------------------------------------
# 日志配置（显式输出到 stderr，不干扰 MCP 通道）
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("openclaw.mcp")

# ---------------------------------------------------------------------------
# 全局单例：避免重复初始化 ADB 连接和模型客户端
# ---------------------------------------------------------------------------
_agent: HeadlessMAIAgent | None = None


def _get_agent() -> HeadlessMAIAgent:
    """获取或创建全局 HeadlessMAIAgent 单例。"""
    global _agent
    if _agent is None:
        _agent = HeadlessMAIAgent(
            model_url=os.environ.get("API_BASE_URL", "http://localhost:8000/v1"),
            api_key=os.environ.get("API_KEY", "empty"),
            model_name=os.environ.get("MODEL_NAME", "MAI-UI-8B"),
            device_id=os.environ.get("DEVICE_ID") or None,
        )
        logger.info("HeadlessMAIAgent 单例已创建")
    return _agent


# ---------------------------------------------------------------------------
# MCP Server 定义
# ---------------------------------------------------------------------------
mcp = FastMCP("MAI-Mobile-Agent")


@mcp.tool()
def perform_mobile_task(instruction: str) -> str:
    """
    Use this tool to control an Android phone via natural language.

    The agent will observe the phone screen, reason about the next action,
    and execute it step-by-step until the task is completed.

    Input should be a clear, specific instruction in natural language,
    for example:
      - "Open WeChat and send 'hello' to the first contact"
      - "Open Settings and turn down the brightness"
      - "打开高德地图搜索最近的加油站"

    Returns a JSON string with execution status and step-by-step logs.

    Args:
        instruction: A natural language instruction describing the task
                     to perform on the Android phone.
    """
    logger.info("收到 MCP 调用: %s", instruction)
    agent = _get_agent()

    try:
        result = agent.run_task(instruction, max_steps=15, step_delay=1.0)
    except Exception as e:
        logger.error("任务执行异常: %s", e)
        result = {"status": "failed", "steps": 0, "logs": [f"执行异常: {e}"]}

    # 格式化为易读文本返回给 OpenClaw
    status_emoji = "✅" if result["status"] == "success" else "❌"
    lines = [
        f"{status_emoji} 任务状态: {result['status']}",
        f"执行步数: {result['steps']}",
        "",
        "执行日志:",
    ]
    for log in result.get("logs", []):
        lines.append(f"  - {log}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("MAI-UI MCP Server 启动中...")
    mcp.run()
