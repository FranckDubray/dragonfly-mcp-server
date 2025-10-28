Cutoff: {FROM_ISO}
Now: {NOW_ISO}

Context (curated Top10 JSON):
{TOP10}

Task
- You are a strict validator of the curated Top 10 AI/LLM news above (array of objects with rank, title, url, source, published_at, why, category, coverage_count).
- Evaluate quality against: (1) factuality/recency (>= {FROM_ISO}), (2) deduplication & canonical URLs, (3) diversity of sources/topics, (4) usefulness of summaries ("why"), (5) overall coherence.

Scoring rubric (0..10)
- 0–3: poor (outdated/incorrect, many duplicates, weak coverage)
- 4–6: mixed (some good items, but several issues)
- 7–8: good (minor issues, overall solid)
- 9–10: excellent (accurate, well-covered, diverse, well-justified)

Return STRICT JSON only (no prose before/after, no code fences):
{
  "score": 0..10,
  "feedback": "3–6 lines: strengths, misses (duplicates/outdated), source/topic diversity, improvements"
}
