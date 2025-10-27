Top 10 AI news since {FROM_ISO}.

- Search broadly across official org blogs, arXiv, trusted media.
- Rank by: (1) impact/interest, (2) number of distinct credible sources referencing the same story.
- Deduplicate; pick the most canonical/primary URL per story.
- Return STRICT JSON ONLY (no prose, no code fences): array of up to 10 items.
- Each item: "title", "url", "source", "published_at" (UTC Z), "image_url", "coverage_count".
- Ensure published_at >= {FROM_ISO}.
