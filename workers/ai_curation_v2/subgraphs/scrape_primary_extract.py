from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="SCRAPE_PRIMARY_EXTRACT",
    entry="STEP_PREP_URLS",
    exits={"success": "SCRAPE_DONE"}
)

@step
def STEP_PREP_URLS(worker, cycle, env):
    caps = worker.get("primary_site_caps") or {}
    urls = list(caps.keys())
    out = env.transform("set_value", value=urls)
    s = cycle.setdefault("scrape", {})
    s["urls"] = out.get("result") or urls
    s["idx"] = 0
    s["total"] = len(urls)
    s["pages"] = []
    return Next("COND_HAS_MORE_URLS")

@cond
def COND_HAS_MORE_URLS(worker, cycle, env):
    s = cycle.get("scrape", {})
    idx = int(s.get("idx") or 0)
    total = int(s.get("total") or 0)
    if idx < total:
        return Next("STEP_SET_URL")
    return Next("STEP_STRINGIFY_SCRAPES")

@step
def STEP_SET_URL(worker, cycle, env):
    s = cycle.setdefault("scrape", {})
    urls = s.get("urls") or []
    idx = int(s.get("idx") or 0)
    url_slice = urls[idx:idx+1]
    cur = (url_slice or [""])[0]
    out = env.transform("set_value", value=cur)
    s["current_url"] = out.get("result") or cur
    return Next("STEP_INIT_OFFSET")

@step
def STEP_INIT_OFFSET(worker, cycle, env):
    s = cycle.setdefault("scrape", {})
    out = env.transform("set_value", value=0)
    s["off"] = out.get("result") or 0
    return Next("COND_HAS_MORE_CHUNKS")

@cond
def COND_HAS_MORE_CHUNKS(worker, cycle, env):
    s = cycle.get("scrape", {})
    url = s.get("current_url") or ""
    off = int(s.get("off") or 0)
    caps = worker.get("primary_site_caps") or {}
    cap = int(caps.get(url) or 0)
    if cap == 0 and off == 0:
        return Next("STEP_FETCH_CHUNK")
    if cap > 0 and off < cap:
        return Next("STEP_FETCH_CHUNK")
    return Next("STEP_INC_URL_IDX")

@step
def STEP_FETCH_CHUNK(worker, cycle, env):
    s = cycle.setdefault("scrape", {})
    url = s.get("current_url") or ""
    off = int(s.get("off") or 0)
    chunk_bytes = int(worker.get("scrape_chunk_bytes", 4000))
    out = env.tool(
        "universal_doc_scraper",
        operation="extract_page",
        url=url,
        offset=off,
        max_bytes=chunk_bytes
    )
    txt = out.get("text") or out.get("content") or out.get("page_text") or out.get("raw") or ""
    s["chunk_text"] = str(txt)
    return Next("STEP_ACCUMULATE_CHUNK")

@step
def STEP_ACCUMULATE_CHUNK(worker, cycle, env):
    s = cycle.setdefault("scrape", {})
    url = s.get("current_url") or ""
    off = int(s.get("off") or 0)
    txt = s.get("chunk_text") or ""
    pages = s.get("pages") or []
    entry = {"url": url, "offset": off, "content": str(txt)}
    new_list = list(pages) + [entry]
    out = env.transform("set_value", value=new_list)
    s["pages"] = out.get("result") or new_list
    return Next("STEP_INC_OFFSET")

@step
def STEP_INC_OFFSET(worker, cycle, env):
    s = cycle.setdefault("scrape", {})
    off = int(s.get("off") or 0)
    chunk_bytes = int(worker.get("scrape_chunk_bytes", 4000))
    out = env.transform("arithmetic", op="inc", a=off, step=chunk_bytes)
    s["off"] = (out or {}).get("result") or (off + chunk_bytes)
    return Next("COND_HAS_MORE_CHUNKS")

@step
def STEP_INC_URL_IDX(worker, cycle, env):
    s = cycle.setdefault("scrape", {})
    idx = int(s.get("idx") or 0)
    out = env.transform("arithmetic", op="inc", a=idx, step=1)
    s["idx"] = (out or {}).get("result") or (idx + 1)
    return Next("COND_HAS_MORE_URLS")

@step
def STEP_STRINGIFY_SCRAPES(worker, cycle, env):
    pages = cycle.get("scrape", {}).get("pages") or []
    out = env.transform("json_stringify", value=pages)
    cycle["scrape"]["json"] = out.get("json_string") or "[]"
    return Next("STEP_PREP_PROMPT")

@step
def STEP_PREP_PROMPT(worker, cycle, env):
    dates = cycle.get("dates", {})
    sjson = cycle.get("scrape", {}).get("json", "[]")
    tpl = str((worker.get("prompts") or {}).get("extract_from_scrapes") or "")
    msg = env.transform("format_template", template=tpl, context={
        "FROM_ISO": str(dates.get("from") or ""),
        "NOW_ISO":  str(dates.get("now") or ""),
        "SCRAPES_JSON": sjson
    }).get("result","")
    cycle["scrape"]["prompt"] = msg
    return Next("STEP_LLM_EXTRACT")

@step
def STEP_LLM_EXTRACT(worker, cycle, env):
    prompt = cycle.get("scrape", {}).get("prompt", "")
    out = env.tool("call_llm", model=worker.get("llm_model"),
                   messages=[{"role":"user","content": prompt}],
                   temperature=worker.get("llm_temperature", 0.3),
                   response_format="text",
                   max_output_tokens=int(worker.get("collect_max_output_tokens", 1000)),
                   max_tokens=int(worker.get("collect_max_output_tokens", 1000)))
    cycle["scrape"]["raw_extract"] = out.get("content") or out.get("result") or "[]"
    return Next("STEP_NORMALIZE_EXTRACT")

@step
def STEP_NORMALIZE_EXTRACT(worker, cycle, env):
    raw = cycle.get("scrape", {}).get("raw_extract")
    out = env.transform("normalize_llm_output", content=raw, fallback_value=[])
    cycle["scrape"]["items"] = out.get("parsed") or []
    return Next("STEP_MERGE_INTO_FRESH")

@step
def STEP_MERGE_INTO_FRESH(worker, cycle, env):
    items = cycle.get("scrape", {}).get("items", [])
    out = env.transform("set_value", value=items)
    cycle.setdefault("fresh", {})["primary_extracted"] = out.get("result") or items
    return Exit("success")
