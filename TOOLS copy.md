Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## Clawdmeme-pipeline (local cheat sheet)

### Paths
- Skill: /root/.openclaw/workspace/skills/clawdmeme-pipeline/SKILL.md
- Output template: /root/.openclaw/workspace/skills/clawdmeme-pipeline/references/output-template.json
- Brave/X trend script (if used): /root/.openclaw/workspace/skills/clawdmeme-pipeline/fetch_x_trends_brave.py

### Env vars (do NOT print values)
- BRAVE_API_KEY (or BRAVE_SEARCH_API_KEY)  # Brave Search
- MORALIS_API_KEY                          # Pump.fun data via Moralis (if enabled)
- (optional) any other keys required by your custom pipeline

Quick check:
- env | grep -i brave
- env | grep -i moralis

### Data sources used by the pipeline
- DexScreener (public REST): token/pair metrics (volume/liquidity/txns)
- Pump.fun: mint -> https://pump.fun/coin/<MINT>
- X: prefer /status/ URLs; if only communities link exists, record it and set xMetricsVerified=false

### Common debug commands
- Validate JSON output quickly:
  python3 -m json.tool < output.json >/dev/null && echo OK || echo BAD_JSON

- Smoke test DexScreener endpoint (token):
  curl -s "https://api.dexscreener.com/latest/dex/tokens/<MINT>" | head

- Smoke test Pump.fun link:
  curl -I "https://pump.fun/coin/<MINT>" | head -n 20

### Rate limit notes
- If Brave returns 429: slow down / backoff / reduce queries.
- If a source is blocked/unavailable: set verification flags false and write notes (don’t guess).

### Output discipline
- If user says “Output STRICT JSON”: no markdown, no commentary, JSON only.
- Never execute on-chain actions unless user says CONFIRM_LAUNCH.