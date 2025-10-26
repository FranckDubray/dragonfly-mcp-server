from py_orch import Process, SubGraphRef

PROCESS = Process(
    name="AI_CURATION_V2",
    entry="INIT",
    parts=[
        SubGraphRef("INIT", module="subgraphs.init", next={"success": "COLLECT"}),
        SubGraphRef("COLLECT", module="subgraphs.collect", next={"success": "SCORE", "fail": "OUTPUT"}),
        SubGraphRef("SCORE", module="subgraphs.score", next={"success": "VALIDATE"}),
        SubGraphRef("VALIDATE", module="subgraphs.validate", next={"success": "ENRICH", "retry": "SCORE", "retry_exhausted": "ENRICH"}),
        SubGraphRef("ENRICH", module="subgraphs.enrich", next={"success": "OUTPUT"}),
        SubGraphRef("OUTPUT", module="subgraphs.output"),
    ],
    metadata={
        "description": "AI/LLM curation v2 (72h freshness, 4 sources, Sonar validation, FR reports)",
        "author": "orchestrator-team",
        "version": "2.0",
        # Unique DB for this worker (same file as runner state DB)
        "db_file": "worker_ai_curation_v2.db",
        "llm_model": "gpt-4o-mini",
        "sonar_model": "sonar",
        "llm_temperature": 0.3,
        "quality_threshold": 7,
        "max_retries": 3,
        "primary_sites": [
            "https://openai.com/index",
            "https://www.anthropic.com/news",
            "https://blog.google/technology/ai",
            "https://deepmind.google/discover/blog",
            "https://ai.meta.com/blog",
            "https://aws.amazon.com/blogs",
            "https://azure.microsoft.com/blog",
            "https://developer.nvidia.com/blog",
            "https://stability.ai/news",
            "https://arxiv.org"
        ]
    }
)
