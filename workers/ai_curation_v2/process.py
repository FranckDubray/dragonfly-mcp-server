

















from py_orch import Process, SubGraphRef

PROCESS = Process(
    name="AI_CURATION_V2",
    entry="INIT",
    parts=[
        SubGraphRef("INIT", module="subgraphs.init", next={"success": "COLLECT"}),
        # Sur échec de COLLECT, on termine le process (pas de fallback OUTPUT)
        SubGraphRef("COLLECT", module="subgraphs.collect", next={"success": "SCORE"}),
        SubGraphRef("SCORE", module="subgraphs.score", next={"success": "VALIDATE"}),
        # ENRICH supprimé: on enchaîne directement vers OUTPUT après VALIDATE
        SubGraphRef("VALIDATE", module="subgraphs.validate", next={"success": "OUTPUT", "retry": "SCORE", "retry_exhausted": "OUTPUT"}),
        SubGraphRef("OUTPUT", module="subgraphs.output"),
    ],
    # IMPORTANT: toutes les metadata/variables runtime doivent vivre dans workers/<name>/config/
    metadata={}
)
