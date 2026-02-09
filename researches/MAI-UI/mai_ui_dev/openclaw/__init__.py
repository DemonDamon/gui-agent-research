"""
OpenClaw - MAI-UI Headless Agent & MCP Integration

将 MAI-UI GUI Agent 核心逻辑解耦为无头服务，
通过 MCP 协议接入 OpenClaw，实现自然语言端到端控制 Android 设备。
"""

from openclaw.headless_runner import HeadlessMAIAgent

__all__ = ["HeadlessMAIAgent"]
