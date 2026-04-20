---
name: news
description: "Monitor daily crypto news and match relevant stories to your content calendar. Fetches Crypto Integrated and The Block, filters by project keywords (AADS, MAADS, Slise, Welldone), and recommends which post slot to use each story in. Use when: find news for posts, check what's trending, news for MAADS, news for AADS, what should I post today, content research."
---

# News Monitor for Content Pipeline

Fetches daily crypto digests, filters by project keyword sets, and maps each story to the nearest upcoming post slot in your content calendar.

Run it every morning before writing posts. Takes 30 seconds. Prevents publishing outdated angles.

---

## Usage

### Default — all projects, last 2 days:
```
/news
```

### Filter by project:
```
/news MAADS
/news AADS
/news Slise
/news Welldone
```

### Widen the time window:
```
/news MAADS 5
/news AADS 7
```

### Check upcoming schedule:
```
/news check
```

---

## What It Does

### Step 1: Fetch
Pulls latest content from two sources:
- **Crypto Integrated** (`cryptointegrat.com`) — daily digest, Crypto + Ethereum + AI editions
- **The Block** (`theblock.co`) — breaking news, regulatory & institutional

### Step 2: Filter by project keywords

**AADS** — finds stories about:
crypto ad bans, Google/Meta/X restrictions, CPM trends, iGaming advertising, affiliate bans, display ad networks, programmatic crypto

**MAADS** — finds stories about:
CLARITY Act, SEC/CFTC actions, iGaming regulation, gambling bans, DraftKings/FanDuel, World Cup gambling, stablecoin adoption, Mastercard/Tether news, DAOs legal status, Polymarket, Australia AFSL

**Slise** — finds stories about:
Etherscan traffic, DexTools, dApp sessions, onchain targeting, wallet analytics, DeFi advertising, blockchain explorer data

**Welldone** — finds stories about:
Smart contract security, AI code vulnerabilities, EU AI Act, FinTech compliance, Ethereum upgrades, blind signing exploits, CertiK, STRIDE

### Step 3: Score & rank
Each story gets a relevance score based on keyword hit count. Higher = more specific match.

### Step 4: Match to calendar
For each story, finds the nearest upcoming post slot for that project within 14 days. Shows the post date + recommended format.

---

## Output Format

```
# 📰 News Monitor — 19 Apr 2026

Found 8 relevant items (last 2 days, all projects)

---

## MAADS (3 items)

**1. CLARITY Act faces four-way Senate standoff as May window closes**
   → Project: MAADS | Source: Crypto Integrated
   → Next post slot: 19 Apr (Sun) | Format: Hot take (light)
   → Angle: Hot take / Regulatory news → marketing window angle
   → Senate markup still has no date. Four open issues: DeFi provisions,
     ethics language, stablecoin yield, community bank provisions...

---

## AADS (2 items)

**2. Meta adds EU location surcharges starting July 1 — France +3%, Austria +5%**
   → Project: AADS | Source: The Block
   → Next post slot: 20 Apr (Mon) | Format: Market Insight
   → Angle: Market Insight: competitor restrictions → AADS advantage
   → European digital service taxes passed directly to advertisers...
```

---

## Sources & Schedules

### Monitored sources

| Source | URL | Update frequency |
|--------|-----|-----------------|
| Crypto Integrated | cryptointegrat.com | Daily (Mon–Fri) |
| The Block | theblock.co/latest | Continuous |

### Sources to add manually (check 1x/week)
- **r/CryptoCurrency** — sentiment, community reactions
- **r/ethfinance** — Ethereum developer discussions
- **DL News** (dlnews.com) — TradFi + onchain convergence
- **Finance Magnates** (financemagnates.com) — iGaming industry

---

## Content Calendar Integration

The skill reads your content calendar automatically:

| Date | Project | Format |
|------|---------|--------|
| 19 Apr | MAADS | Hot take (light) |
| 20 Apr | AADS | Market Insight |
| 21 Apr | MAADS | Hot take (light) |
| 22 Apr | AADS | Market Insight |
| 23 Apr | MAADS | Market Insight |
| 24 Apr | AADS | Market Insight |
| ... | ... | ... |
| 12 May | AADS | Market Insight |

Each news story is automatically matched to the nearest upcoming slot for its project.

---

## Recommended Workflow

### Daily (5 min):
```
1. Run /news
2. Scan top 2-3 items per project
3. If a story fits today's post → update the post with fresh data
4. If strong story found → update the draft in content calendar
```

### Before writing each post (2 min):
```
1. Run /news [PROJECT]
2. Check if today's angle is still the most current
3. Update numbers/names if something more recent found
```

### Weekly audit (10 min):
```
1. Run /news check → verify all 14 upcoming dates have topics
2. Flag any posts that need fresh news (show as "pending")
3. Reassign topics if major news broke that changes angles
```

---

## Limitations

- Crypto Integrated doesn't publish on weekends — `days_back=3` on Mondays
- The Block headlines may need clicking through to verify details
- Keyword matching is string-based, not semantic — some false positives possible
- Paywalled articles will show headline only, not full body

---

## Files

```
autoresearch-skill/
├── news_monitor.py       # Core: fetch, parse, score, rank
├── content_calendar.py   # Calendar: dates, formats, project mapping
├── news_skill.py         # /news command handler + output formatting
└── NEWS_MONITOR_SKILL.md # This file
```
