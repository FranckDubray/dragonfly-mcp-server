from __future__ import annotations
from typing import Any, Dict

from .validators import validate_params
from .fileset import collect_tool_files
from .git_sensitive import scan_git_sensitive
from .context import build_context_pack
from .scheduler import build_tasks, run_tasks_parallel
from .fuse import merge_algorithmic, fuse_final
from .output import build_response
from .usage_merge import merge_usage


def run(**params: Any) -> Dict[str, Any]:
    p = validate_params(params)

    tool_name = p["tool_name"]
    files = collect_tool_files(tool_name)

    git_res = scan_git_sensitive(files)

    ctx = build_context_pack(
        files=files,
        strategy="full_pack",
        max_bytes_per_file=p["max_bytes_per_file"],
        max_total_context_bytes=p["max_total_context_bytes"],
        fields=p["fields"],
    )

    tasks = build_tasks(
        models=p["models"],
        profile_mode=p["profile_mode"],
        context_pack=ctx,
    )

    results = run_tasks_parallel(
        tasks=tasks,
        max_concurrency=p["llm_max_concurrency"],
        max_concurrency_per_model=p["llm_max_concurrency_per_model"],
    )

    cumulative_usage = {}
    filtered = []
    for r in results:
        if r.get("model") == "__cumulative__" and isinstance(r.get("usage"), dict):
            cumulative_usage = r.get("usage")
        else:
            filtered.append(r)

    merged_findings, summary_models = merge_algorithmic(filtered)

    fused, fuser_usage = fuse_final(
        tool_name=tool_name,
        merged_findings=merged_findings,
        summary_models=summary_models,
        git_sensitive=git_res,
        ctx_manifest=ctx["manifest"],
        fuser_model=p.get("fuser_model"),
        llm_timeout_sec=p["llm_timeout_sec"],
        llm_top_n=p.get("llm_top_n", 10),
    )

    if isinstance(fuser_usage, dict):
        merge_usage(cumulative_usage, fuser_usage)

    out = build_response(
        tool_name=tool_name,
        fused=fused,
        limit=p["limit"],
        cursor=p.get("cursor"),
        fields=p["fields"],
    )

    if cumulative_usage:
        out["usage"] = cumulative_usage

    return out
