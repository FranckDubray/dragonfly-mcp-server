from __future__ import annotations
from typing import Any, Dict, List, Tuple
import json

from .metrics import compute_scores, collect_metrics
from .prompts_loader import load_system_and_cdc
from .utils import extract_first_json_block
from .llm_runner import call_model_with_retry

MAX_TOKENS_FUSER = 500  # cap fusion output to keep result compact


def _norm_key_component(v: Any) -> str:
    if isinstance(v, (dict, list)):
        try:
            return json.dumps(v, ensure_ascii=False, sort_keys=True)
        except Exception:
            return str(v)
    return str(v or "")

# ... (unchanged merge_algorithmic and _build_histogram) ...

from .metrics import compute_scores, collect_metrics


def merge_algorithmic(results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    merged: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    summary_models: Dict[str, Any] = {"errors_by_model": {}, "models_used": []}

    for r in results:
        model = r.get("model")
        if model and model not in summary_models["models_used"]:
            summary_models["models_used"].append(model)
        if r.get("status") == "failed":
            summary_models["errors_by_model"][model] = r.get("error", "failed")
            continue
        report = r.get("report") or {}
        findings = report.get("findings") or []
        if not isinstance(findings, list):
            continue
        for f in findings:
            if not isinstance(f, dict):
                continue
            key = (
                _norm_key_component(f.get("path", "")),
                _norm_key_component(f.get("rule", "")),
                _norm_key_component(f.get("range", "")),
            )
            if key not in merged:
                f.setdefault("models", [])
                if model and model not in f["models"]:
                    f["models"].append(model)
                merged[key] = f
            else:
                if model and model not in merged[key].get("models", []):
                    merged[key].setdefault("models", []).append(model)

    merged_list = list(merged.values())
    return merged_list, summary_models


def _build_histogram(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev = (f.get("severity") or "low").lower()
        if sev in by_sev:
            by_sev[sev] += 1
        else:
            by_sev["low"] += 1
    return by_sev


def fuse_final(tool_name: str, merged_findings: List[Dict[str, Any]], summary_models: Dict[str, Any], git_sensitive: Dict[str, Any], ctx_manifest: Any, fuser_model: str | None, llm_timeout_sec: int | None = None, llm_top_n: int = 10) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    files_metrics = collect_metrics([m.get("path") for m in merged_findings if isinstance(m.get("path"), str)])
    scores = compute_scores(merged_findings, files_metrics)

    by_sev = _build_histogram(merged_findings)

    top = merged_findings[: max(1, llm_top_n)]
    draft = {
        "tool_name": tool_name,
        "summary": {
            "models_used": summary_models.get("models_used", []),
            "profiles_run": ["perf", "quality", "maintain", "invariants"],
            "total_findings": len(merged_findings),
            "by_severity": by_sev,
            "errors_by_model": summary_models.get("errors_by_model", {}),
        },
        "scores": scores,
        "git_sensitive": git_sensitive,
        "findings": top,
        "fs_requests": [],
    }

    try:
        system, cdc = load_system_and_cdc("fuser")
    except Exception:
        system, cdc = ("Fusion JSON stricte", "Produit un rapport final JSON strict. Ne modifie pas 'scores'.")

    # Ajout instruction de cap dans CDC
    cdc = cdc + "\nHard cap: output JSON under 500 tokens."

    draft_json = json.dumps(draft, ensure_ascii=False)
    messages = [
        {"role": "user", "content": cdc},
        {"role": "user", "content": f"DRAFT\n{draft_json}"},
    ]

    model = fuser_model or "gpt-5"
    fuser_usage: Dict[str, Any] = {}

    llm_out = call_model_with_retry(model=model, system=system, messages=messages, max_tokens=MAX_TOKENS_FUSER, temperature=0.2)
    content = ""
    if isinstance(llm_out, dict):
        content = llm_out.get("content") or ""
        if isinstance(llm_out.get("usage"), dict):
            fuser_usage = llm_out.get("usage")
    fused = extract_first_json_block(content)
    if not isinstance(fused, dict):
        raise RuntimeError("fusion_llm_failed: invalid_fuser_output")
    if "scores" not in fused:
        fused["scores"] = scores
    fused.setdefault("tool_name", tool_name)
    fused.setdefault("summary", draft["summary"])
    fused.setdefault("findings", top)
    fused.setdefault("actions", {"quick_wins": [], "backlog": []})
    fused.setdefault("fs_requests", [])
    return fused, fuser_usage
