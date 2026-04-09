---
name: weekly-schedule
description: "Generate a weekly content schedule for MAADS, AADS, SLISE, and WELLDONE social media channels. Assigns dates, brands, content formats, and drafts post copy following established rotation patterns and brand voice. Use when: plan next week's content, generate weekly schedule, create content calendar, schedule posts, what should we publish next week. Outputs: a weekly content schedule table with dates, brands, formats, and draft post text."
---

# Weekly Content Schedule Generator

Produces a ready-to-execute weekly content calendar for four crypto/adtech brands. Each week gets 8 posts spread across Monday–Saturday, with brand slots, content formats, and draft copy assigned according to the rotation patterns established since March 2026.

---

## the four brands

| Brand | Domain | What it is | Core message |
|-------|--------|-----------|--------------|
| **MAADS** | maads.com | Full-service crypto marketing agency. Owns AADS + Slise. | "We own the pipes that reach your audience." Performance data, market trends, strategic POV. |
| **AADS** | aads.com | Crypto ad network since 2011. 300M+ daily impressions, 2,500+ sites. No KYC. | Oldest network, lowest barrier, crypto-native. Product features, network stats, publisher/advertiser benefits. |
| **SLISE** | slise.xyz | On-chain ad targeting inside dApps (Etherscan, DexTools, BirdEye, Solscan). | Wallet-level targeting in active dApp sessions. CTR 0.4–0.6% vs 0.1% industry. Case results, publisher inventory, technical differentiation. |
| **WELLDONE** | (no public domain yet) | 30+ senior engineers. Full-ownership FinTech/Web3/AdTech development. T&M only. | Day-one code ownership, CX engineering embedded in sprints, one blended rate. |

See [references/brand-guide.md](references/brand-guide.md) for full brand voice, topics, and CTA patterns.

---

## weekly slot structure

Each week follows this default grid. Adjust days if holidays or events shift the calendar.

| Slot | Day | Brand | Format pool (pick one, rotate) |
|------|-----|-------|-------------------------------|
| 1 | Monday | MAADS | Hot take · Market Insight · Contrarian take |
| 2 | Tuesday | AADS | Market Insight · Mini offer / checklist |
| 3 | Tuesday | SLISE | Results breakdown · Market Insight |
| 4 | Wednesday | MAADS | Mistakes & Patterns · Hot take · Market Insight |
| 5 | Thursday | MAADS | Case study (numbers-first) · Contrarian take · Mistakes & Patterns |
| 6 | Thursday | AADS | Market Insight · Step-by-step logic |
| 7 | Friday | AADS / WELLDONE | Market Insight · Problem → DM CTA · Mini offer / checklist |
| 8 | Saturday | SLISE / WELLDONE | Hot take · Contrarian take · Results breakdown |

**When WELLDONE is in the rotation** (default since late March 2026): slots 7 and 8 alternate between AADS/WELLDONE and SLISE/WELLDONE respectively. WELLDONE gets 2–3 slots per week, reducing AADS and SLISE by one slot each.

**Rules:**
- No brand posts the same format two weeks in a row.
- No two posts on the same day use the same format.
- Maximum 2 posts per calendar day.
- Sunday is rest day — no posts.
- If a slot falls on a public holiday, move it to the nearest available day.

---

## content formats

Nine formats, each with a distinct structure. See [references/format-guide.md](references/format-guide.md) for full specs and examples.

| Format | Structure | Typical length | Best for |
|--------|-----------|---------------|----------|
| **Hot take (light)** | News hook → sharp opinion → one-line implication → domain | 80–150 words | MAADS, SLISE |
| **Market Insight** | Data point → context → "what this means for you" → domain | 80–150 words | All brands |
| **Results breakdown** | Metric headline → what we did → why it worked → CTA | 100–180 words | MAADS, SLISE, WELLDONE |
| **Mistakes & Patterns** | Counterintuitive claim → explanation → proof → domain | 80–150 words | MAADS |
| **Case study (numbers-first)** | Two metrics up front → lever 1 → lever 2 → "we own the platform" → CTA | 150–250 words | MAADS |
| **Mini offer / checklist** | Stat or context → short checklist / offer → CTA | 80–120 words | AADS, SLISE |
| **Problem → DM CTA** | Pain point → why standard approach fails → "Comment X" CTA | 80–150 words | AADS, SLISE |
| **Step-by-step logic** | Three numbered factors → explanation per factor → proof point → CTA | 120–180 words | SLISE |
| **Contrarian take** | "Everyone thinks X. Here's why Y." → evidence → domain | 80–150 words | MAADS, AADS, SLISE |

---

## how to generate a weekly schedule

### step 1: determine the target week

Ask the user:
1. **Which week?** (start date, e.g., "week of April 20, 2026")
2. **Any events or hooks?** (product launches, regulatory news, market events, conferences)
3. **WELLDONE active?** (default: yes, since late March 2026)
4. **Any brand to emphasize this week?** (default: even distribution)
5. **Any formats to skip or force?** (default: follow rotation)

If the user doesn't provide these, use the current date for the target week, assume no special events, WELLDONE active, even distribution, and standard rotation.

### step 2: check last week's schedule

Read the most recent entry in [references/content-archive.tsv](references/content-archive.tsv) to determine:
- Which formats each brand used last week (to avoid repeats)
- Which topics were covered (to avoid overlap)
- Which CTAs were used (to rotate them)

### step 3: assign brands and formats

Fill the 8-slot grid:
1. Place brands according to the slot structure.
2. For each slot, pick a format that:
   - Is in that slot's format pool.
   - Was NOT used by that brand last week.
   - Is NOT already used by another post on the same day.
3. If WELLDONE is active, assign it to 2–3 slots (typically slots 5, 7, or 8), adjusting other brands.

### step 4: draft post copy

For each slot, write the post following the format spec from [references/format-guide.md](references/format-guide.md).

**Copy rules:**
- Lead with a number, a name, or a sharp claim. Never open with "Did you know" or "In today's world."
- Every post ends with the brand domain on its own line (maads.com, aads.com, slise.xyz).
- Use real data. Pull from recent crypto/adtech news, on-chain metrics, or case studies in the archive. Do not fabricate statistics.
- CTA variations: "Comment [KEYWORD]", "Book a demo", "Link in bio", "[domain]" (soft). Rotate across the week — no two adjacent posts use the same CTA type.
- Tone: confident, specific, zero fluff. Write like a practitioner, not a marketer. No emojis except one max per post if it fits naturally.
- Avoid banned phrases: "game-changer", "here's the kicker", "the best part", "level up", "in today's fast-paced", "buckle up", "let's dive in", "without further ado".
- WELLDONE posts focus on engineering craft, not marketing claims. Tone is calmer, more technical.

### step 5: output the schedule

Present the schedule as a table:

```
| Day | Date | Brand | Format | Post text | CTA | Status |
|-----|------|-------|--------|-----------|-----|--------|
| Mon | 20.04 | MAADS | Hot take (light) | [full draft] | maads.com | Draft |
| Tue | 21.04 | AADS | Mini offer / checklist | [full draft] | aads.com | Draft |
| ... | ... | ... | ... | ... | ... | ... |
```

After presenting the schedule, ask:
- "Any posts you want me to revise or swap?"
- "Should I add this to the content archive?"

---

## maintaining the archive

After the user approves a schedule, append all 8 posts to [references/content-archive.tsv](references/content-archive.tsv) so future weeks can reference them for rotation tracking.

**TSV columns:**
```
date	day	brand	format	text	cta	status
```

---

## quick reference: brand × format matrix

Which formats work for which brands (based on 6+ weeks of published content):

| Format | MAADS | AADS | SLISE | WELLDONE |
|--------|:-----:|:----:|:-----:|:--------:|
| Hot take (light) | yes | — | yes | yes |
| Market Insight | yes | yes | yes | — |
| Results breakdown | yes | — | yes | yes |
| Mistakes & Patterns | yes | — | — | — |
| Case study (numbers-first) | yes | — | — | — |
| Mini offer / checklist | — | yes | yes | — |
| Problem → DM CTA | — | yes | yes | — |
| Step-by-step logic | — | — | yes | — |
| Contrarian take | yes | yes | yes | — |
