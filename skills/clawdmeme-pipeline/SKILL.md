---
name: clawdmeme-pipeline
description: Generate and manage a meme-coin narrative pipeline with evidence-first sourcing (X + dashboards like Pump.fun/DexScreener/Jupiter), rank candidates, output strict JSON only, and enforce a CONFIRM_LAUNCH human gate (never execute).
---

# Clawdmeme Pipeline

This skill is a strict JSON-only pipeline for:
- Finding meme-token inspirations and narratives
- Producing pump.fun-ready metadata (name/symbol/description/imagePrompt)
- Producing evidence URLs and verification flags for each candidate
- Producing forum post drafts (ideation/progress)
- Preparing (but never executing) launch commands behind an explicit human gate phrase

## When to use this skill

Follow this skill when the user asks for any of:
- “Fetch and rank top meme token candidates today” (daily scan)
- “Brand this topic into names/tickers/lore + image prompts”
- “Prepare a launch package but DO NOT launch”
- “Write a forum post draft only”
- “If I reply CONFIRM_LAUNCH, output exact next commands/payload but never execute”

## Hard behavior override: "themes/trending/inspiration" must run evidence scan
If user asks for trending/themes/inspiration/hot right now, treat as Daily scan mode and output STRICT JSON using the standard template (even if user didn’t mention Pump.fun/DexScreener/Jupiter).

If the user asks anything like:
- "top three trending themes"
- "what's hot right now"
- "give me inspiration"
- "best themes for meme tokens"
- "what should I launch today"
- "daily top meme tokens"

THEN you MUST NOT answer with generic commentary.

Instead, you MUST run the same evidence-first scan pipeline and return STRICT JSON in the standard template:
- Default to config: {"mode":"daily","nTopics":5,"language":"en","sources":{"useX":true,"usePumpfun":true,"useDexScreener":true,"useJupiter":true}}
- If user asks for 3 themes, still populate `topics` with up to 5  candidates, but ensure the top 3 are clearly the highest-ranked and `bestPick` matches #1.
- Each candidate MUST include evidence URLs in `evidence.evidenceUrls` and set verification flags honestly.
- Never claim "right now" without evidence URLs; if a source is unavailable, set verification=false and explain in `verification.notes`.

Output must remain STRICT JSON only (no markdown, no commentary).


## Non-negotiable rules

- Output **STRICT JSON only**. No markdown. No commentary.
- Never execute on-chain actions. Never “auto-post” anywhere unless the user explicitly approves in the same session.
- Never print secrets. If an API key is required, reference it by ENV var name only.
- If user mentions APIs: assume keys are stored in environment (do NOT embed keys in outputs).
- Evidence must be URLs (public pages or public REST endpoints) and must not claim verification if not actually fetched.
- Always include `verification` booleans to indicate what was actually confirmed vs inferred/heuristic.

## Inputs

Assume plain text by default.

Optionally, user may provide a config JSON:
{
  "mode": "daily" | "one-shot",
  "nTopics": 10,
  "language": "en" | "zh",
  "riskTolerance": "low" | "medium" | "high",
  "postToForum": true | false,
  "includeImages": true | false,
  "sources": {
    "useX": true | false,
    "usePumpfun": true | false,
    "useDexScreener": true | false,
    "useJupiter": true | false
  }
}

Optional links: X URLs, Pump.fun URLs, DexScreener URLs, Jupiter URLs, etc.

### Env vars (do not print)
- BRAVE_API_KEY or BRAVE_SEARCH_API_KEY (if using Brave search)
- MORALIS_API_KEY (if using Moralis for Pump.fun-related indexing)
- COLOSSEUM_API_KEY (only if user asks to post to Colosseum forum)

## Core objective

Return candidates that are:
- meme-native and templateable (caption-this, reaction formats, sticker/emote packs)
- visually iconic (mascot/icon silhouette)
- have evidence URLs (X post URLs, Pump.fun token page, DexScreener pair/token endpoints, Jupiter token validation endpoints when available)

**Important:** If some data is blocked/unavailable, you must:
- set the corresponding `verification.*` flag to false
- put the reason in `verification.notes`
- avoid fabricating metrics

## Output format

Return exactly one JSON object matching:
`references/output-template.json`

### Required top-level keys
- statusSummary
- topics
- bestPick
- pumpfunMetadata
- launchGate
- forumPostDraft

## Candidate schema requirements (topics[])

Each item in `topics[]` must include:
- topic
- whyNow (evidence hints; short)
- originStage (one of: "X" | "TG" | "Dashboard" | "TikTok")
- viralityScore (0-100)
- memeabilityScore (0-100)
- longevityScore (0-100)
- riskScore (0-100; higher = riskier)
- recommendedAngle (neutral framing; how to present)
- nameOptions (array of 3)
- tickerOptions (array of 5; 2-6 chars; deduped)
- oneLinerLore
- imagePrompt (1:1 mascot/logo prompt; safe; no copyrighted refs)
- disclaimer (1-2 sentences)
- evidence (object; see template)

### Evidence + verification rules
- `evidenceUrls` should include any relevant URLs you used.
- `verification` flags must reflect what you truly fetched/parsed:
  - pumpfunVerified: true only if Pump.fun/Moralis data for the mint was actually fetched
  - dexVerified: true only if DexScreener endpoint(s) were fetched
  - xMetricsVerified: true only if X metrics were fetched from a real endpoint and parsed
  - jupiterVerified: true only if Jupiter endpoints confirm token list/route support

If a value is inferred (e.g., “pump mint endswith pump”), mark verified=false and explain in `verification.notes`.

## Launch safety gate

- Always include:
  "launchGate": {
    "ready": false,
    "requiresHumanConfirmation": true,
    "confirmPhrase": "CONFIRM_LAUNCH",
    "readyToLaunchPayload": {...}
  }

- Only when the user message is exactly `CONFIRM_LAUNCH`:
  - you may populate `readyToLaunchPayload` with exact next commands/payload
  - but you still must never execute anything automatically

## Minimalism

Keep text fields concise. Prefer short, structured sentences over long paragraphs.
## Scoring (must be explainable + capped when unverified)

You MUST compute and include `scoreBreakdown` for each candidate, and derive:
- viralityScore (0-100)
- memeabilityScore (0-100)
- longevityScore (0-100)
- riskScore (0-100, higher = riskier)

Rules:
- If `evidence.verification.xMetricsVerified=false`, cap `viralityScore` at 85.
- If only an X Community URL is available (no direct /status URL), treat X as partially verified and cap `xSignalScore`.
- Always prefer evidence-backed scores over intuition; if data is missing, lower the score and explain.

Suggested components:
- viralityScore = 0.6*dexMomentum + 0.3*xSignal + 0.1*evidenceCompleteness
- memeabilityScore = 0.3*iconClarity + 0.3*templateability + 0.2*nameTickerSimplicity + 0.2*communityLoops
- longevityScore = 0.3*collectiblePotential + 0.3*characterEngine + 0.2*notEventDependent + 0.2*crossPlatformFit
- riskScore = 0.3*lowLiquidityRisk + 0.2*abnormalVolToLiq + 0.1*txnImbalance + 0.1*xEvidenceGap + 0.1*verificationGap + 0.2*safetyIPRisk

## X Communities review requirement

If `evidence.xPostUrl` is an X Community link (`https://x.com/i/communities/...`), you MUST:
- Fetch and review the Community page content.
- Extract (if available):
  - pinned post summary
  - summaries of the newest 10 posts
  - repeated meme phrases / icon references / rallying calls
  - why this community is influential

Add this under `evidence.xCommunityReview`:
- xCommunityReviewed: true|false
- pinnedSummary: string
- recentPostSummaries: array of strings (up to 10)
- keyMemePatterns: array of strings
- whyInfluential: string

In `verification.notes`, explicitly state that conclusions were derived from reviewing:
X community (pinned + recent) + DexScreener + Pump.fun.
If the community cannot be fetched due to JS/blocks, set `xCommunityReviewed=false` and lower scores accordingly.
