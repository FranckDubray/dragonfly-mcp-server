
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
    # IMPORTANT: toutes les metadata/variables runtime doivent vivre dans workers/<name>/config.py
    # L'orchestrateur fusionne automatiquement CONFIG -> process.metadata (config prime)
    metadata={}
)
