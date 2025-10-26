from py_orch import Process, SubGraphRef

PROCESS = Process(
    name="ROOT",
    entry="INIT",
    parts=[
        SubGraphRef("INIT", module="subgraphs.init", next={"success": "LOOP"}),
        SubGraphRef("LOOP", module="subgraphs.loop", next={"success": "ANALYZE", "maxed": "WAIT"}),
        SubGraphRef("WAIT", module="subgraphs.wait", next={"success": "RETRY"}),
        SubGraphRef("RETRY", module="subgraphs.retry", next={"success": "FINALIZE", "error": "FINALIZE"}),
        SubGraphRef("ANALYZE", module="subgraphs.analyze", next={"success": "FINALIZE", "warn": "FINALIZE"}),
        SubGraphRef("FINALIZE", module="subgraphs.finalize"),
    ],
    metadata={"description": "Test Python Orchestrator - advanced", "version": "1.3"}
)
