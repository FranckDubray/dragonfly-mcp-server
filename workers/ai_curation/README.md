# 🤖 AI/LLM Curation Worker

**Worker d'orchestration pour la curation automatisée des actualités IA/LLM**

---

## 📋 Description

Worker orchestré qui collecte, score et valide automatiquement les actualités IA/LLM des 3 derniers jours depuis 5 sources différentes, avec validation qualité par Perplexity Sonar et génération d'un rapport en français.

---

## 🎯 Architecture

### **Worker**
- **Nom** : `ai_curation`
- **Type** : One-shot (EXIT après exécution)
- **Base de données** : `worker_ai_curation.db`

### **Process**
- **Fichier** : `main.process.json`
- **Version** : 6.0.1-single-db
- **Architecture** : Modulaire avec $import

---

## 📊 Sources de données (5)

1. **📰 News** (NYT + Guardian) — 8 articles
2. **💬 Reddit** (MachineLearning, LocalLLaMA, OpenAI) — 3 posts/sub
3. **📄 arXiv** (papers académiques) — 8 papers
4. **💻 Papers With Code** (trending papers)
5. **🌐 Sonar** (Perplexity real-time web search) — 8-10 items

---

## 🔄 Workflow

### **Phase 1 : Collecte** (30-60s)
- Fetch 5 sources en parallèle
- Parse et normalisation

### **Phase 2 : Scoring Loop** (avec retry)
```
SCORING_LOOP
  ↓
  GPT-4o-mini scoring (Top 10)
  ↓
  Sonar validation (score 1-10)
  ↓
  Score >= 7 ? → [OUI] Format rapport FR → EXIT
               → [NON] Retry < 3 ? → [OUI] BACK TO LOOP
                                   → [NON] Format rapport → EXIT
```

**Critères de scoring** (GPT-4o-mini) :
- **Pertinence** (40%) : IA/LLM core (pas applications tangentielles)
- **Nouveauté** (30%) : Breaking news > recherche récente
- **Source Quality** (20%) : arXiv > GitHub > News > Reddit
- **Diversité** (10%) : Mix de sources

**Validation Sonar** :
- Score 1-10 avec feedback détaillé
- Seuil : **>= 7/10**
- Max retries : **3**

### **Phase 3 : Rapport** (30-60s)
- Génération rapport markdown en français (GPT-4o-mini)
- Format strict : Titre + Note + Résumé + URL × 10 items
- Sauvegarde DB + completion

---

## 📁 Structure du répertoire

```
workers/ai_curation/
├── main.process.json          # Process principal (avec $import)
├── config/
│   ├── worker_ctx.json         # Configuration worker
│   └── scopes.json             # Scopes lifecycle
├── prompts/
│   ├── sonar_fetch.json        # Prompt Sonar search
│   ├── gpt_scoring.json        # Prompt GPT scoring
│   ├── sonar_validation.json   # Prompt Sonar validation
│   └── gpt_format_fr.json      # Prompt format rapport FR
└── README.md                   # Ce fichier
```

---

## 🗄️ Base de données

### **worker_ai_curation.db**

#### Table `validation_logs`
Logs des tentatives de validation Sonar (retry loop).

```sql
CREATE TABLE validation_logs (
  id INTEGER PRIMARY KEY,
  timestamp TEXT NOT NULL,
  attempt INTEGER,
  score REAL,
  feedback TEXT,      -- Feedback Sonar complet
  top10_json TEXT     -- Top 10 à cette tentative
);
```

#### Table `reports`
Rapports finaux générés.

```sql
CREATE TABLE reports (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  date_from TEXT,
  date_to TEXT,
  report_markdown TEXT,  -- Rapport complet en français
  avg_score REAL,
  retry_count INTEGER,
  top10_json TEXT,
  completed_at TEXT
);
```

---

## 🚀 Lancement

### **Start**
```python
from src.tools.orchestrator import run

result = run(
    operation="start",
    worker_name="ai_curation",
    worker_file="workers/ai_curation/main.process.json",
    hot_reload=True
)
```

### **Status**
```python
status = run(
    operation="status",
    worker_name="ai_curation"
)
```

### **Stop**
```python
stop = run(
    operation="stop",
    worker_name="ai_curation",
    stop={"mode": "soft"}
)
```

---

## 📊 Exemple de rapport

```markdown
# 🤖 Top 10 IA/LLM — 2025-10-15 au 2025-10-18

**Score de qualité:** 7.6/10 | **Tentatives:** 0 | **Date:** 2025-10-18

---

## 📌 Top 10 Sélection (5 sources: News, Reddit, arXiv, Papers With Code, Sonar)

**1. Design Agentique de Machines Compositives** — Note: 9.0/10  
*Cette recherche propose une nouvelle perspective sur la création de machines par les LLM, représentant une avancée fondamentale dans les capacités de l'IA.*  
🔗 Source: [arxiv.org](http://arxiv.org/abs/2510.14980v1)

**2. L'Attention est Tout Ce Dont Vous Avez Besoin pour le Cache KV dans les LLM en Diffusion** — Note: 8.5/10  
*Cet article présente des améliorations dans la gestion du cache KV pour les LLM, augmentant ainsi l'efficacité des modèles de diffusion.*  
🔗 Source: [arxiv.org](http://arxiv.org/abs/2510.14973v1)

[...8 autres items]

---

## ✅ Évaluation Qualité

**Score final:** 7.6/10  
**Nombre de tentatives:** 0  
**Validé le:** 2025-10-18T21:22:10

---

## 🔍 Tendances clés

*Les thèmes principaux incluent des avancées dans la conception agentique des LLM, l'amélioration de l'efficacité des modèles via des techniques de cache optimisées...*
```

---

## ⚙️ Configuration

### **worker_ctx.json**
```json
{
  "timezone": "UTC",
  "llm_model": "gpt-4o-mini",
  "sonar_model": "sonar",
  "llm_temperature": 0.3,
  "quality_threshold": 7,
  "max_retries": 3,
  "db_name": "worker_ai_curation"
}
```

### **Scopes**
- `dates` : Date de collecte (from/now)
- `sources` : Données sources brutes
- `scoring` : Résultats scoring GPT
- `validation` : Résultats validation Sonar
- `result` : Rapport final
- `meta` : Métadonnées (retry_count, timestamps)

---

## 📈 Métriques

### **Temps d'exécution typique**
- **Total** : 70-120 secondes
  - Collecte : 30-60s
  - Scoring loop : 20-40s (1-3 tentatives)
  - Format rapport : 15-30s

### **Coûts LLM**
- **GPT-4o-mini** : ~2-3 appels (scoring + format)
- **Sonar** : ~1-3 appels (fetch + validation retry)

---

## 🔧 Dépannage

### **Retry loop infini**
Si le worker boucle > 3 fois :
- Vérifier les logs `validation_logs`
- Sonar retourne probablement du texte au lieu de JSON
- Solution : améliorer le prompt `prompts/sonar_validation.json`

### **Score toujours < 7**
- Sources trop faibles (vérifier diversité)
- Critères trop stricts (ajuster seuil à 6.5)

### **Parse failed sur top10**
- GPT-4o-mini a retourné du texte au lieu de JSON
- Vérifier `prompts/gpt_scoring.json` (instruction "ONLY JSON")

---

## 📝 Changelog

### v6.0.1 (2025-10-18)
- ✅ Base unique `worker_ai_curation.db`
- ✅ Architecture modulaire avec $import
- ✅ Retry loop avec validation Sonar
- ✅ Rapport français formaté
- ✅ 5 sources (ajout Sonar)

---

## 📚 Voir aussi

- [orchestrator_tool_design.md](../../membank/orchestrator_tool_design.md) — Specs orchestrator
- [orchestrator_process_schema.md](../../membank/orchestrator_process_schema.md) — Format JSON process
- [orchestrator_mcp_error_handling.md](../../membank/orchestrator_mcp_error_handling.md) — Gestion erreurs

---

**Status : ✅ Production-ready**
