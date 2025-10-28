
from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="COLLECT",
    entry="STEP_FETCH_NEWS",
    exits={"success": "COLLECT_DONE", "fail": "COLLECT_FAIL"}
)

@step
def STEP_FETCH_NEWS(worker, cycle, env):
    # News (72h window)
    dates = cycle.get("dates", {})
    # Normalize dates to YYYY-MM-DD for news_aggregator
    fd = str(dates.get("from") or "")[:10]
    td = str(dates.get("now") or "")[:10]
    out = env.tool(
        "news_aggregator", operation="search_news",
        query=("(AI OR \"artificial intelligence\" OR \"large language model\" OR LLM OR transformer) "
               "AND (OpenAI OR Anthropic OR Google OR DeepMind OR Meta OR NVIDIA OR Microsoft OR Gemini OR Claude OR GPT)"),
        from_date=fd,
        to_date=td,
        providers=["guardian"],
        limit=30
    )
    cycle.setdefault("sources", {})["news"] = out.get("articles") or out.get("results") or []
    return Next("STEP_FETCH_REDDIT")

@step
def STEP_FETCH_REDDIT(worker, cycle, env):
    out = env.tool(
        "reddit_intelligence", operation="multi_search",
        subreddits=["MachineLearning", "LocalLLaMA", "OpenAI"],
        query="AI OR LLM OR transformer OR GPT OR Claude OR Gemini",
        limit_per_sub=10,
        time_filter="week"
    )
    cycle.setdefault("sources", {})["reddit"] = out.get("results") or []
    return Next("STEP_FETCH_ARXIV")

@step
def STEP_FETCH_ARXIV(worker, cycle, env):
    out = env.tool(
        "academic_research_super", operation="search_papers",
        sources=["arxiv"], query="large language model OR transformer OR LLM",
        include_abstracts=False, max_results=25
    )
    cycle.setdefault("sources", {})["arxiv"] = out.get("results") or []
    # Passer directement à Sonar (Top 10 global, toutes sources confondues)
    return Next("STEP_FETCH_SONAR")

@step
def STEP_FETCH_SONAR(worker, cycle, env):
    # Ask Sonar-Pro for a global Top 10 across sources since {FROM_ISO}
    dates = cycle.get("dates", {})
    prompts = worker.get("prompts", {})
    tpl = str(prompts.get("collect_sonar") or "")
    msg = tpl.format(FROM_ISO=str(dates.get("from") or ""))
    messages = [{"role": "user", "content": msg}]
    out = env.tool("call_llm", model=worker.get("sonar_model"), messages=messages, temperature=0.3)
    cycle.setdefault("sources", {})["sonar_raw"] = out.get("content") or out.get("result") or "[]"
    return Next("STEP_NORMALIZE_SONAR")

@step
def STEP_NORMALIZE_SONAR(worker, cycle, env):
    raw = cycle.get("sources", {}).get("sonar_raw")
    out = env.transform("normalize_llm_output", content=raw, fallback_value=[])
    cycle["sources"]["sonar"] = out.get("parsed") or []
    return Next("STEP_FILTER_NEWS")

@step
def STEP_FILTER_NEWS(worker, cycle, env):
    dates = cycle.get("dates", {})
    out = env.transform(
        "array_ops", op="filter",
        items=cycle.get("sources", {}).get("news", []),
        predicate={"kind":"date_gte", "path":"published_at", "cutoff":str(dates.get("from") or "")}
    )
    fres = cycle.setdefault("fresh", {})
    fres["news"] = out.get("items") or []
    fres.setdefault("metrics", {})["news_kept"] = len(fres["news"])
    return Next("STEP_FILTER_REDDIT")

@step
def STEP_FILTER_REDDIT(worker, cycle, env):
    dates = cycle.get("dates", {})
    out = env.transform(
        "array_ops", op="filter",
        items=cycle.get("sources", {}).get("reddit", []),
        predicate={"kind":"date_gte", "path":"created_utc", "cutoff":str(dates.get("from") or ""), "unix": True}
    )
    fres = cycle.setdefault("fresh", {})
    fres["reddit"] = out.get("items") or []
    fres.setdefault("metrics", {})["reddit_kept"] = len(fres["reddit"])
    return Next("STEP_FILTER_ARXIV")

@step
def STEP_FILTER_ARXIV(worker, cycle, env):
    dates = cycle.get("dates", {})
    # Tolerant: arXiv results often use 'published' (not 'publication_date')
    out = env.transform(
        "array_ops", op="filter",
        items=cycle.get("sources", {}).get("arxiv", []),
        predicate={"kind":"date_gte", "path":"published", "cutoff":str(dates.get("from") or "")}
    )
    fres = cycle.setdefault("fresh", {})
    fres["arxiv"] = out.get("items") or []
    fres.setdefault("metrics", {})["arxiv_kept"] = len(fres["arxiv"])
    # Filtrer Sonar après normalisation pour garantir la fenêtre temporelle
    return Next("STEP_FILTER_SONAR")

@step
def STEP_FILTER_SONAR(worker, cycle, env):
    dates = cycle.get("dates", {})
    out = env.transform(
        "array_ops", op="filter",
        items=cycle.get("sources", {}).get("sonar", []),
        predicate={"kind":"date_gte", "path":"published_at", "cutoff":str(dates.get("from") or "")}
    )
    fres = cycle.setdefault("fresh", {})
    fres["sonar"] = out.get("items") or []
    fres.setdefault("metrics", {})["sonar_kept"] = len(fres["sonar"])
    return Next("STEP_TAKE_ARXIV")

@step
def STEP_TAKE_ARXIV(worker, cycle, env):
    # Limiter arXiv proprement (pas de coupe JSON) pour éviter de flooder le LLM
    items = cycle.get("fresh", {}).get("arxiv", [])
    n = int((worker.get("per_source_take") or {}).get("arxiv", 20))
    out = env.transform("array_ops", op="take", items=items, count=n)
    cycle.setdefault("fresh", {})["arxiv"] = out.get("items", [])
    return Next("STEP_HAS_DATA")

@cond
def STEP_HAS_DATA(worker, cycle, env):
    m = cycle.get("fresh", {}).get("metrics", {})
    total = int(m.get("news_kept", 0)) + int(m.get("reddit_kept", 0)) + int(m.get("arxiv_kept", 0)) + int(m.get("sonar_kept", 0))
    if total >= 1:
        return Exit("success")
    return Exit("fail")
