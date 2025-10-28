Global Top 10 AI/LLM news since {FROM_ISO} (last ~72h).

Search globally across the web (do not limit to a fixed provider list):
- Official org/lab/company blogs and press releases
- Mainstream and tech media (authoritative outlets)
- arXiv and reputable research venues/preprints
- Credible research/engineering blogs and newsletters
- Developer/community platforms when linking to verifiable sources

Requirements
- Rank by: (1) interest/impact, (2) number of distinct credible sources referencing the same story, (3) breadth (cover models, products, research, governance/safety, infra/tools, community)
- Deduplicate; pick the most canonical/primary URL per story
- Exclude rumors, unverifiable claims, or low-credibility sources
- Ensure published_at >= {FROM_ISO}

Return STRICT JSON ONLY (no prose, no code fences): array of up to 10 items.
Each item must include:
- "title": string
- "url": canonical primary URL (string)
- "source": domain or publisher name (string)
- "published_at": ISO8601 UTC Z (e.g., 2025-10-28T09:30:00Z)
- "image_url": string (empty if unknown)
- "coverage_count": integer (rough estimate of distinct credible sources covering the same story)
