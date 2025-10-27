

from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="SCORE",
    entry="STEP_BUNDLE_SOURCES",
    exits={"success": "SCORE_DONE"}
)

@step
def STEP_BUNDLE_SOURCES(worker, cycle, env):
    # Build a complete bundle without pre-caps or pre-dedup; GPT-5 will deduplicate & rank
    fres = cycle.get("fresh", {})
    # IMPORTANT: ensure Sonar and arXiv are first so they are never dropped by any downstream size limits
    bundle = {
        "sonar": fres.get("sonar", []),
        "arxiv": fres.get("arxiv", []),
        "news":  fres.get("news", []),
        "reddit":fres.get("reddit", []),
    }
    out = env.transform("set_value", value=bundle)
    cycle.setdefault("scoring", {})["bundle"] = out.get("result") or bundle
    return Next("STEP_STRINGIFY_BUNDLE")

@step
def STEP_STRINGIFY_BUNDLE(worker, cycle, env):
    out = env.transform("json_stringify", value=cycle.get("scoring", {}).get("bundle", {}))
    cycle.setdefault("scoring", {})["items_json"] = out.get("json_string") or "{}"
    return Next("STEP_PREP_CRITIQUE")

@step
def STEP_PREP_CRITIQUE(worker, cycle, env):
    fb = cycle.get("validation", {}).get("feedback") or ""
    out = env.transform("set_value", value=fb)
    cycle.setdefault("scoring", {})["critique"] = out.get("result") or ""
    return Next("STEP_GPT_SCORE")

@step
def STEP_GPT_SCORE(worker, cycle, env):
    dates = cycle.get("dates", {})
    items_json = cycle.get("scoring", {}).get("items_json") or "{}"
    critique = cycle.get("scoring", {}).get("critique") or ""
    prompts = worker.get("prompts", {})
    tpl = str(prompts.get("score_gpt") or "")
    # Remove naive character-level truncation to avoid cutting arXiv/Sonar blocks or breaking JSON
    msg_text = tpl.format(
        FROM_ISO=str(dates.get("from") or ""),
        NOW_ISO=str(dates.get("now") or ""),
        ITEMS=items_json,
        CRITIQUE=critique
    )
    max_out = int(worker.get("scoring_max_output_tokens", 5000))
    out = env.tool(
        "call_llm",
        model=worker.get("scoring_model") or worker.get("llm_model"),
        messages=[{"role":"user","content": msg_text}],
        temperature=worker.get("llm_temperature", 0.3),
        response_format="json",
        max_output_tokens=max_out,
        max_tokens=max_out
    )
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
