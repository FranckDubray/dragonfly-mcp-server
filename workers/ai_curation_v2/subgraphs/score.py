from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="SCORE",
    entry="STEP_CONCAT_SOURCES",
    exits={"success": "SCORE_DONE"}
)

@step
def STEP_CONCAT_SOURCES(worker, cycle, env):
    # Concatenate fresh sources arrays
    fres = cycle.get("fresh", {})
    out = env.transform(
        "array_concat",
        lists=[
            fres.get("news", []),
            fres.get("reddit", []),
            fres.get("arxiv", []),
            fres.get("sonar", []),
        ]
    )
    cycle.setdefault("scoring", {})["all_items"] = out.get("items") or []
    return Next("STEP_DEDUPE_BY_URL")

@step
def STEP_DEDUPE_BY_URL(worker, cycle, env):
    out = env.transform(
        "array_ops", op="unique_by",
        items=cycle.get("scoring", {}).get("all_items", []),
        key="url"
    )
    cycle.setdefault("scoring", {})["unique_items"] = out.get("items") or []
    return Next("STEP_GPT_SCORE")

@step
def STEP_GPT_SCORE(worker, cycle, env):
    # Build a compact prompt; expect JSON array with top-scored items
    dates = cycle.get("dates", {})
    items = cycle.get("scoring", {}).get("unique_items", [])
    msg = (
        "You are an expert AI/LLM curator. STRICT JSON ONLY.\n"
        f"Cutoff (ISO): {str(dates.get('from') or '')}\nNow (ISO): {str(dates.get('now') or '')}\n\n"
        "Score and rank ALL these items (keep only >= cutoff). Return up to 10 as JSON array.\n"
        f"ITEMS:\n{str(items)[:5000]}"
    )
    out = env.tool("call_llm", model=worker.get("llm_model"), messages=[{"role":"user","content": msg}],
                   temperature=worker.get("llm_temperature", 0.3), response_format="json")
    cycle.setdefault("scoring", {})["raw"] = out.get("content") or out.get("result") or "[]"
    return Next("STEP_NORMALIZE_SCORE")

@step
def STEP_NORMALIZE_SCORE(worker, cycle, env):
    raw = cycle.get("scoring", {}).get("raw")
    out = env.transform("normalize_llm_output", content=raw)
    cycle["scoring"]["top10"] = out.get("parsed") or []
    return Next("STEP_STRINGIFY_TOP10")

@step
def STEP_STRINGIFY_TOP10(worker, cycle, env):
    out = env.transform("json_stringify", value=cycle.get("scoring", {}).get("top10", []))
    cycle["scoring"]["top10_json"] = out.get("json_string") or "[]"
    return Exit("success")
