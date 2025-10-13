Tool Audit — audit d’un tool MCP unique (lecture-seule)

- Périmètre strict: uniquement le code du tool, sa spec JSON, son README local.
- Multi-LLM via tool call_llm, prompts et CDC externalisés (prompts/).
- Parallélisation bornée, timeouts configurables, retry 3× (10s) sur erreurs transitoires.
- Sortie compacte, paginée, anchors-only par défaut; scores multi-axes 0–10.

Étapes clés:
1) git_sensitive: fichiers sensibles suivis et marqueurs secrets (masqués)
2) build_context_pack: chunks bornés (cap par fichier et global)
3) LLM audits (perf, quality, maintain, invariants) — mode combined si possible
4) Fusion algorithmique (+ option LLM fuser) et scoring

Conformité LLM DEV GUIDE: parameters=object, limit/cursor, truncated, chroot, pas de side-effects, fichiers <7KB.
