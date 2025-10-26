

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
    # Build prompt from config.prompts.score_gpt
    dates = cycle.get("dates", {})
    items = cycle.get("scoring", {}).get("unique_items", [])
    prompts = worker.get("prompts", {})
    tpl = str(prompts.get("score_gpt") or "")
    msg_text = tpl.format(
        FROM_ISO=str(dates.get("from") or ""),
        NOW_ISO=str(dates.get("now") or ""),
        ITEMS=str(items)[:5000]
    )
    out = env.tool(
        "call_llm",
        model=worker.get("llm_model"),
        messages=[{"role":"user","content": msg_text}],
        temperature=worker.get("llm_temperature", 0.3),
        response_format="json"
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

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
