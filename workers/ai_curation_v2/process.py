
from py_orch import Process, SubGraphRef

PROCESS = Process(
    name="AI_CURATION_V2",
    entry="INIT",
    parts=[
        SubGraphRef("INIT", module="subgraphs.init", next={"success": "COLLECT"}),
        SubGraphRef("COLLECT", module="subgraphs.collect", next={"success": "SCRAPE_PRIMARY_EXTRACT"}),
        SubGraphRef("SCRAPE_PRIMARY_EXTRACT", module="subgraphs.scrape_primary_extract", next={"success": "SCORE"}),
        SubGraphRef("SCORE", module="subgraphs.score", next={"success": "VALIDATE"}),
        SubGraphRef("VALIDATE", module="subgraphs.validate", next={"success": "OUTPUT", "retry": "SCORE", "retry_exhausted": "OUTPUT"}),
        SubGraphRef("OUTPUT", module="subgraphs.output"),
    ],
    # IMPORTANT: toutes les metadata/variables runtime doivent vivre dans workers/<name>/config/
    metadata={}
)
