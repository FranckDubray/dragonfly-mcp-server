from __future__ import annotations
import os
from typing import Dict, Any, List

SEVERITY_W = {"critical": 2.0, "high": 1.2, "medium": 0.6, "low": 0.2}

# Rule -> axes weights
RULE_AXES = {
    # invariants
    "limit_param_missing": {"invariants": 2.0},
    "missing_truncated_flag": {"invariants": 1.5},
    "spec_not_canonical": {"invariants": 2.0},
    "side_effect_import": {"invariants": 2.0},
    # quality / maintainability
    "file_too_large": {"quality": 1.0, "size": 1.2, "maintainability": 0.6},
    "function_too_long": {"quality": 0.8, "complexity": 1.0},
    "duplication": {"quality": 0.8, "maintainability": 0.6},
    "god_file": {"maintainability": 1.2, "quality": 0.6},
    "high_coupling": {"maintainability": 1.0, "coupling": 1.2},
    "import_cycle": {"maintainability": 1.2, "coupling": 1.2},
    # performance
    "heavy_loop": {"performance": 1.5},
    "regex_compile_in_loop": {"performance": 1.2},
    "sync_io_in_async": {"performance": 1.5},
    "concat_str_in_loop": {"performance": 0.8},
    "unbounded_glob": {"performance": 1.0},
    # dead code
    "unused_import": {"dead_code": 0.8, "maintainability": 0.6},
}

AXES = ("performance", "quality", "maintainability", "invariants")
SUB_AXES = ("size", "complexity", "dead_code", "coupling")


def collect_metrics(files: List[str]) -> Dict[str, Any]:
    loc_total = 0
    big_files = 0
    for p in files:
        if not p.endswith(".py"):
            continue
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            loc_total += len(lines)
            if len(lines) > 250 or os.path.getsize(p) > 7 * 1024:
                big_files += 1
        except Exception:
            continue
    return {"loc_total": loc_total, "big_files": big_files}


def compute_scores(findings: List[Dict[str, Any]], files_metrics: Dict[str, Any]) -> Dict[str, Any]:
    loc_total = max(1, files_metrics.get("loc_total", 1))
    K = max(1.0, loc_total / 1000.0)  # normalize per KLOC

    acc = {ax: 0.0 for ax in AXES}
    acc_sub = {sax: 0.0 for sax in SUB_AXES}

    for f in findings:
        rule = (f.get("rule") or "").lower()
        sev = (f.get("severity") or "low").lower()
        w_sev = SEVERITY_W.get(sev, 0.2)
        axes = RULE_AXES.get(rule, {})
        for ax, w in axes.items():
            if ax in acc:
                acc[ax] += w_sev * w
            elif ax in acc_sub:
                acc_sub[ax] += w_sev * w

    def score_from_penalty(p: float) -> float:
        s = 10.0 - min(9.0, p / K)
        return max(0.0, min(10.0, s))

    axes_scores = {ax: round(score_from_penalty(v), 1) for ax, v in acc.items()}
    sub_scores = {sax: round(score_from_penalty(v), 1) for sax, v in acc_sub.items()}

    # bonuses
    if files_metrics.get("big_files", 0) == 0:
        axes_scores["quality"] = min(10.0, axes_scores["quality"] + 0.3)
        axes_scores["maintainability"] = min(10.0, axes_scores["maintainability"] + 0.3)
    if acc.get("invariants", 0.0) == 0.0:
        axes_scores["invariants"] = min(10.0, axes_scores["invariants"] + 0.5)

    # overall weighted average
    mix = {"invariants": 0.3, "maintainability": 0.3, "performance": 0.2, "quality": 0.2}
    overall = sum(axes_scores[a] * w for a, w in mix.items())

    # evidence: take up to 3 anchors from highest-penalty rules
    evid = []
    for f in findings[:3]:
        pth = f.get("path")
        if not pth:
            continue
        evid.append(f"{pth}#L1-L60")

    return {
        "method": "algo_v1",
        "overall": round(overall, 1),
        "axes": axes_scores,
        "sub_axes": sub_scores,
        "confidence": 0.5,
        "evidence": evid,
    }
