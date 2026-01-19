#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Evaluation script for MAI-UI Models.

This script evaluates a MAI-UI agent using the upstream MobileWorld runner,
aligning action parsing, logging format, and scoring logic with upstream.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable

from mobile_world.core.runner import run_agent_with_evaluation


def _load_tasks(tasks: str | None) -> list[str]:
    if not tasks:
        return []
    tasks_path = Path(tasks)
    if tasks_path.exists():
        return [line.strip() for line in tasks_path.read_text().splitlines() if line.strip()]
    return [t.strip() for t in tasks.split(",") if t.strip()]


def _split_list(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _dump_results(results: Iterable[dict], output_path: str | None) -> None:
    if not output_path:
        return
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(list(results), handle, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_type", type=str, default="mai_ui_agent")
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--llm_base_url", type=str, required=True)
    parser.add_argument("--api_key", type=str, default=os.getenv("OPENAI_API_KEY", "empty"))
    parser.add_argument("--log_root", type=str, required=True)
    parser.add_argument("--tasks", type=str, default=None)
    parser.add_argument("--aw_urls", type=str, default=None)
    parser.add_argument("--max_step", type=int, default=-1)
    parser.add_argument("--step_wait_time", type=float, default=1.0)
    parser.add_argument("--suite_family", type=str, default="mobile_world")
    parser.add_argument("--env_name_prefix", type=str, default="mobile_world_env")
    parser.add_argument("--env_image", type=str, default="mobile_world")
    parser.add_argument("--enable_mcp", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--shuffle_tasks", action="store_true")
    parser.add_argument("--max_concurrency", type=int, default=None)
    parser.add_argument("--output_path", type=str, default=None)
    args = parser.parse_args()

    task_list = _load_tasks(args.tasks)
    aw_urls = _split_list(args.aw_urls)
    results, failed_tasks = run_agent_with_evaluation(
        agent_type=args.agent_type,
        model_name=args.model_name,
        llm_base_url=args.llm_base_url,
        log_file_root=args.log_root,
        tasks=task_list,
        max_step=args.max_step,
        aw_urls=aw_urls,
        api_key=args.api_key,
        step_wait_time=args.step_wait_time,
        suite_family=args.suite_family,
        env_name_prefix=args.env_name_prefix,
        env_image=args.env_image,
        dry_run=args.dry_run,
        enable_mcp=args.enable_mcp,
        max_concurrency=args.max_concurrency,
        shuffle_tasks=args.shuffle_tasks,
    )

    _dump_results(results, args.output_path)
    if failed_tasks:
        print(f"Tasks with no results: {failed_tasks}")


if __name__ == "__main__":
    main()
