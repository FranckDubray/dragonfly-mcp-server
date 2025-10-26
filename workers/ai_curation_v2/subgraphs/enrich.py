from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="ENRICH",
    entry="STEP_ENSURE_TABLE",
    exits={"success": "ENRICH_DONE"}
)

@step
def STEP_ENSURE_TABLE(worker, cycle, env):
    env.tool(
        "sqlite_db", operation="execute", db=worker.get("db_file"),
        query=("CREATE TABLE IF NOT EXISTS sources ("
               "id INTEGER PRIMARY KEY AUTOINCREMENT,"
               "report_from TEXT, report_to TEXT, item_index INTEGER, "
               "topic_title TEXT, sources_json TEXT, inserted_at TEXT)")
    )
    return Next("STEP_INIT_INDEX")

@step
def STEP_INIT_INDEX(worker, cycle, env):
    out = env.transform("set_value", value=0)
    cycle.setdefault("enrich", {})["i"] = out.get("result")
    return Next("STEP_SLICE_SKIP")

@step
def STEP_SLICE_SKIP(worker, cycle, env):
    i = int(cycle.get("enrich", {}).get("i", 0))
    items = cycle.get("scoring", {}).get("top10", [])
    out = env.transform("array_ops", op="skip", items=items, count=i)
    cycle["enrich"]["slice"] = out.get("items") or []
    return Next("STEP_TAKE_ONE")

@step
def STEP_TAKE_ONE(worker, cycle, env):
    out = env.transform("array_ops", op="take", items=cycle.get("enrich", {}).get("slice", []), count=1)
    cycle["enrich"]["one"] = out.get("items") or []
    return Next("STEP_GET_ITEM")

@step
def STEP_GET_ITEM(worker, cycle, env):
    out = env.transform("json_ops", op="get", data=cycle.get("enrich", {}).get("one", []), path="items[0]", default=None)
    cycle["enrich"]["item"] = out.get("result")
    return Next("COND_HAS_ITEM")

@cond
def COND_HAS_ITEM(worker, cycle, env):
    if cycle.get("enrich", {}).get("item"):
        return Next("STEP_BUILD_QUERY")
    return Exit("success")

@step
def STEP_BUILD_QUERY(worker, cycle, env):
    item = cycle.get("enrich", {}).get("item") or {}
    out = env.transform("format_template", template="{{title}} official blog OR press OR research", context={"title": item.get("title", "")})
    cycle["enrich"]["query"] = out.get("result") or ""
    return Next("STEP_SEARCH_PRIMARY")

@step
def STEP_SEARCH_PRIMARY(worker, cycle, env):
    out = env.tool(
        "universal_doc_scraper", operation="search_across_sites",
        sites=worker.get("primary_sites", []), query=cycle.get("enrich", {}).get("query", ""),
        max_results=5, max_pages=2
    )
    cycle["enrich"]["primary"] = out.get("results") or []
    return Next("STEP_NEWS_PRIMARY")

@step
def STEP_NEWS_PRIMARY(worker, cycle, env):
    dates = cycle.get("dates", {})
    item = cycle.get("enrich", {}).get("item") or {}
    out = env.tool(
        "news_aggregator", operation="search_news",
        providers=["guardian"], query=str(item.get("title", "")),
        from_date=str(dates.get("from") or ""), to_date=str(dates.get("now") or ""),
        limit=5
    )
    cycle["enrich"]["news"] = out.get("articles") or []
    return Next("STEP_ARXIV_PRIMARY")

@step
def STEP_ARXIV_PRIMARY(worker, cycle, env):
    item = cycle.get("enrich", {}).get("item") or {}
    out = env.tool(
        "academic_research_super", operation="search_papers",
        sources=["arxiv"], query=str(item.get("title", "")), include_abstracts=False, max_results=5
    )
    cycle["enrich"]["arxiv"] = out.get("results") or []
    return Next("STEP_MERGE_SOURCES")

@step
def STEP_MERGE_SOURCES(worker, cycle, env):
    out = env.transform(
        "array_concat",
        lists=[cycle.get("enrich", {}).get("primary", []), cycle.get("enrich", {}).get("news", []), cycle.get("enrich", {}).get("arxiv", [])]
    )
    cycle["enrich"]["merged_all"] = out.get("items") or []
    return Next("STEP_DEDUPE")

@step
def STEP_DEDUPE(worker, cycle, env):
    out = env.transform("array_ops", op="unique_by", items=cycle.get("enrich", {}).get("merged_all", []), key="url")
    cycle["enrich"]["merged"] = out.get("items") or []
    return Next("STEP_STRINGIFY")

@step
def STEP_STRINGIFY(worker, cycle, env):
    out = env.transform("json_stringify", value=cycle.get("enrich", {}).get("merged", []))
    cycle["enrich"]["sources_json"] = out.get("json_string") or "[]"
    return Next("STEP_INSERT_ROW")

@step
def STEP_INSERT_ROW(worker, cycle, env):
    dates = cycle.get("dates", {})
    i = int(cycle.get("enrich", {}).get("i", 0))
    item = cycle.get("enrich", {}).get("item") or {}
    env.tool(
        "sqlite_db", operation="execute", db=worker.get("db_file"),
        query=("INSERT INTO sources (report_from, report_to, item_index, topic_title, sources_json, inserted_at) VALUES (?, ?, ?, ?, ?, ?)"),
        params=[str(dates.get("from") or ""), str(dates.get("now") or ""), i, str(item.get("title", "")), cycle.get("enrich", {}).get("sources_json") or "[]", str(cycle.get("validation", {}).get("timestamp", ""))]
    )
    return Next("STEP_INC_INDEX")

@step
def STEP_INC_INDEX(worker, cycle, env):
    i = int(cycle.get("enrich", {}).get("i", 0)) + 1
    out = env.transform("set_value", value=i)
    cycle["enrich"]["i"] = out.get("result")
    return Next("STEP_SLICE_SKIP")
