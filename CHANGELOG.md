


# Changelog

## [1.27.4] - 2025-10-15

### 🛠 Workers Realtime — Correctifs UI/UX & Mermaid (compléments)
- Time Machine:
  - Contrôles “magnétophone” (⏮ ⏪ ▶︎/⏸ ⏩ ⏭) pour rejouer pas‑à‑pas ou en auto.
  - Surlignage synchronisé: clic nœud Mermaid → sélection/scroll de l’étape dans la timeline; nœud courant surligné.
  - Timeline chargée jusqu’à 200 événements, ~15 lignes visibles (scroll dédié), horodatage FR (date+heure).
  - Alerte claire si incohérence logs ↔ schéma (nœuds inconnus) avec détails (id + date/heure), échantillons limités.
  - Cache du code Mermaid pendant le replay (perf): plus de requêtes DB par step.
- Galerie/Lightbox:
  - Galerie fermée par défaut; ouverture/fermeture via l’icône seulement.
  - Scroll horizontal accéléré dans la galerie; lightbox uniquement pour vignettes/data‑full (jamais l’avatar).
- VU Ring:
  - Anneau vert/jaune/rouge plus visible, lissage EMA + boost non linéaire, compat APIs legacy.
- CSS/Thème:
  - Thème clair confirmé; avatar 64×64 rond, recadrage; timeline ~15 lignes visibles.
- Prompt système / Contexte:
  - DB complétée (timezone, working_hours, bio) puis nettoyage (email/tags retirés) conformément aux demandes.

### 🔔 Sonnerie & Audio
- Sonnerie “Skype-like” par défaut (≈400/450 Hz), cadence tu‑tu‑tuu tu‑tu‑tu, agréable et familière pour 2–10 s.
- Volume par défaut 50% et curseur unique pilotant à la fois la sonnerie et la voix IA (setVolume partagé).
- Préchargement de Mermaid au chargement de page (/workers) pour supprimer la latence (fallback + retry garantis côté JS si CDN lent).

### 🧠 VAD & Interruption IA
- Détection rapide: dès que l’utilisateur parle, arrêt immédiat du haut-parleur IA et cancel de la réponse courante.
- Reprise rapide au silence stable; option d’accentuation (<200ms) possible.

### 📊 KPIs Process (overlay)
- Nouveau panneau “Activité (dernière heure)” dans l’overlay Process: 
  - Tâches (succeeded/failed), Appels call_llm, Cycles (sleep_interval ou fallback finish_mailbox_db)
  - Recalcul à chaque refresh (10 s) pendant l’overlay.

### 🎨 Couleur cartes selon activité (1h)
- 0–15 → vert, 16–40 → orange, >40 → rouge (classes activity-*)

### 🐛 Corrections Mermaid
- Chargeur Mermaid robuste (retry) + fallback “Diagramme indisponible” avec message explicite.
- Normalisation du source Mermaid (quotes, backslashes) + surlignage du nœud courant.

### 🗄 Données & Seeds de test
- Injection de cycles cohérents (nomail + mail occasionnels), durées réalistes: sleep 10 min, LLM 1 min, enchaînement strict des nœuds.
- Lot par ~50 lignes, répété pour couvrir une plage temporelle jusqu’à atteindre des tests denses.

---

