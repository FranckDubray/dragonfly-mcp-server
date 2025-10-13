from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Any, Dict, List, Tuple

from .llm_runner import run_task
from .usage_merge import merge_usage

Profile = str
Task = Tuple[str, Profile, Dict[str, Any]]


PROFILES = ["perf", "quality", "maintain", "invariants"]


def build_tasks(models: List[str], profile_mode: str, context_pack: Dict[str, Any]) -> List[Task]:
    tasks: List[Task] = []
    if profile_mode == "combined":
        # 1 CDC combiné par modèle (x4)
        for m in models:
            tasks.append((m, "combined", context_pack))
    elif profile_mode == "per_profile":
        # 4 CDC par modèle (x16)
        for m in models:
            for prof in PROFILES:
                tasks.append((m, prof, context_pack))
    else:  # auto → hybride: 4 combined + 4 profils (premier modèle)
        # 4 combined d'abord (tous modèles)
        for m in models:
            tasks.append((m, "combined", context_pack))
        # Puis 4 profils sur le premier modèle pour monter à 8 tâches
        if models:
            first = models[0]
            for prof in PROFILES:
                tasks.append((first, prof, context_pack))
    return tasks


def run_tasks_parallel(tasks: List[Task], max_concurrency: int, max_concurrency_per_model: int) -> List[Dict[str, Any]]:
    if not tasks:
        return []

    global_sem = threading.Semaphore(max_concurrency)
    model_sems: Dict[str, threading.Semaphore] = {}

    results: List[Dict[str, Any]] = []
    usage_cumulative: Dict[str, Any] = {}

    def wrapper(model: str, profile: Profile, ctx: Dict[str, Any]) -> Dict[str, Any]:
        with global_sem:
            if model not in model_sems:
                model_sems[model] = threading.Semaphore(max_concurrency_per_model)
            with model_sems[model]:
                return run_task(model=model, profile=profile, context_pack=ctx)

    with ThreadPoolExecutor(max_workers=max_concurrency) as ex:
        futures = [ex.submit(wrapper, m, prof, ctx) for (m, prof, ctx) in tasks]
        for fut in as_completed(futures):
            try:
                res = fut.result(timeout=0)
                usage = res.get("usage") if isinstance(res, dict) else None
                if isinstance(usage, dict):
                    merge_usage(usage_cumulative, usage)
                results.append(res)
            except Exception as e:
                results.append({"error": str(e), "status": "failed"})

    if usage_cumulative:
        results.append({"model": "__cumulative__", "profile": "__all__", "usage": usage_cumulative, "status": "ok"})

    return results
