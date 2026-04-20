---
name: effort
description: "Enable low-effort mode to reduce Claude API costs for marketing tasks. Automatically detects marketing prompts and optimizes model selection + thinking tokens. Use: '/effort low' to enable, '/effort off' to disable. Supports: crypto campaigns, social media, SMM analysis, content generation."
---

# Low-Effort Mode for Claude Code

Reduce Claude API costs by up to 85% on marketing tasks. Automatically detects routine prompts (social posts, ads, content) and switches to Haiku with reduced thinking tokens, while keeping Sonnet for complex tasks.

---

## Core Job

Enable intelligent cost optimization for marketing workflows without sacrificing quality for complex tasks.

**When enabled, low-effort mode:**
1. Detects marketing-related prompts via keyword matching
2. Routes simple marketing tasks → Haiku (4-8k thinking tokens)
3. Routes complex tasks → Sonnet (full thinking tokens)
4. Provides cost savings estimate for each prompt

---

## Usage

### Enable low-effort mode:
```
/effort low
```

### Disable (return to standard):
```
/effort off
```

### Environment fallback:
```bash
export EFFORT_MODE=low
export MAX_THINKING_TOKENS=8000
```

### Configuration via .claude/config:
```json
{
  "effort_mode": {
    "enabled": true,
    "max_thinking_tokens": 8000
  }
}
```

---

## How It Works

### Step 1: Prompt Detection
Analyzes incoming prompt for marketing keywords:
- Social media: "post", "tweet", "caption", "SMM", "Instagram", "TikTok"
- Campaign: "ad", "campaign", "crypto", "NFT", "content", "copywriting"
- Routine: "summary", "email", "subject line", "newsletter"

### Step 2: Task Classification
Separates complex tasks (which use Sonnet) from routine tasks:
- **Complex** (uses Sonnet): "research", "architecture", "strategy", "analysis", "design"
- **Routine** (uses Haiku): standalone social posts, captions, summaries

### Step 3: Model + Token Selection

| Task Type | Model | Thinking Tokens | Savings |
|-----------|-------|-----------------|---------|
| Short marketing prompt (<100 chars) | Haiku | 4,000 | ~85% |
| Marketing prompt (100-500 chars) | Haiku | 8,000 | ~85% |
| Complex + marketing | Sonnet | 131,072 | 0% |
| Complex non-marketing | Sonnet | 131,072 | 0% |

### Step 4: Output
Returns original response with metadata showing:
- Model used (Haiku/Sonnet)
- Thinking tokens allocated
- Estimated cost savings percentage
- Reason for selection

---

## Examples

### Example 1: Crypto Twitter Campaign (simple)
**Prompt:** "Generate 5 crypto tweet variants"

**Mode Decision:**
- Keywords: "crypto", "tweet" = marketing
- Length: short = simple
- Selection: Haiku + 4,000 tokens

**Result:** ✅ ~85% cost savings

---

### Example 2: NFT Social Media
**Prompt:** "Write an Instagram caption for our NFT collection launch"

**Mode Decision:**
- Keywords: "Instagram", "NFT", "caption" = marketing
- Complexity: routine social content
- Selection: Haiku + 4,000 tokens

**Result:** ✅ ~85% cost savings

---

### Example 3: Blockchain Architecture (complex)
**Prompt:** "Deep analysis of blockchain architecture and smart contract security implications"

**Mode Decision:**
- Keywords: "analysis", "architecture" = complex
- Task: requires deep thinking
- Selection: Sonnet + 131,072 tokens

**Result:** ⚠️ 0% savings (complexity requires full model)

---

### Example 4: Campaign Strategy
**Prompt:** "Create a social media campaign strategy for our new crypto product"

**Mode Decision:**
- Keywords: "social", "campaign", "crypto" = marketing
- Complexity: "strategy" = requires thinking
- Selection: Sonnet + 131,072 tokens (complex task overrides routine)

**Result:** ⚠️ 0% savings (strategy requires full thinking)

---

## Performance Metrics

**Cost Reduction:**
- Simple marketing tasks: 85% cheaper (Haiku 4-8k tokens)
- Complex tasks: no change (full Sonnet)
- Blended (70% marketing, 30% complex): ~60% average savings

**Quality Guarantee:**
- Marketing tasks: Haiku provides adequate quality for social media, ads, and routine content
- Complex tasks: Sonnet used automatically, no degradation
- Transparency: Users see cost-benefit trade-off in real time

---

## Anti-Patterns (What This Won't Do)

❌ **Don't use low-effort mode for:**
- Research or analysis requiring deep thinking
- Code reviews or security audits
- Architecture design decisions
- Customer-facing technical documentation
- Any task marked `[complex]` in prompt

✅ **Perfect for:**
- Social media content (posts, captions, tweets)
- Ad copy and promotional text
- Email templates and newsletters
- SMM analysis summaries
- Simple content transformations

---

## Configuration

### Enable by command:
```
/effort low
```

### Enable by env var:
```bash
EFFORT_MODE=low MAX_THINKING_TOKENS=8000
```

### Custom thinking token limit:
```bash
MAX_THINKING_TOKENS=6000  # override default 8000
```

### Disable:
```
/effort off
```
Or:
```bash
unset EFFORT_MODE
```

---

## Integration with Other Skills

Low-effort mode works with any Claude Code skill. When enabled:
- All skill invocations automatically detect task type
- Model + tokens adjusted on per-prompt basis
- No changes needed to existing skills
- Savings apply automatically across all skill usage

---

## Limitations & Caveats

1. **Keyword detection is heuristic** — some marketing tasks might require full Sonnet. Always monitor first run.
2. **Thinking tokens reduced to 4-8k** — for very nuanced marketing, might need higher tokens.
3. **No per-skill overrides yet** — future version will allow "always use Sonnet for skill X"
4. **Applies to new prompts only** — doesn't retroactively affect running tasks

---

## Testing the Implementation

Test with:
```bash
python low_effort_mode.py
```

Expected output shows cost savings for each prompt type:
- Crypto tweets: ~85%
- Instagram captions: ~85%
- Blockchain analysis: 0% (uses full Sonnet)
- Campaign strategy: 0% (uses full Sonnet due to complexity)

