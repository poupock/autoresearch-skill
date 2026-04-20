"""Low-effort mode for Claude Code — reduces API costs for marketing tasks."""

import os
import re
from dataclasses import dataclass
from typing import Optional, Literal

MARKETING_KEYWORDS = {
    "post", "tweet", "caption", "ad", "advertisement", "campaign",
    "crypto", "nft", "token", "smm", "social", "marketing",
    "ig", "instagram", "tiktok", "x", "linkedin", "facebook",
    "content", "copy", "copywriting", "summary", "summarize",
    "email", "newsletter", "subject line", "headline"
}

COMPLEX_KEYWORDS = {
    "research", "analysis", "deep", "comprehensive", "architecture",
    "design", "strategy", "plan", "implementation", "debug"
}

@dataclass
class EffortConfig:
    """Configuration for effort mode."""
    enabled: bool = False
    model: Literal["haiku", "sonnet"] = "sonnet"
    max_thinking_tokens: int = 131072  # default Claude max

    @classmethod
    def from_env(cls) -> "EffortConfig":
        """Load from environment or .claude/config."""
        config = cls()

        # Check environment variables
        if os.getenv("EFFORT_MODE") == "low":
            config.enabled = True

        max_tokens_env = os.getenv("MAX_THINKING_TOKENS")
        if max_tokens_env:
            try:
                config.max_thinking_tokens = int(max_tokens_env)
            except ValueError:
                pass

        return config


def detect_marketing_prompt(text: str) -> bool:
    """Auto-detect if prompt is marketing-related."""
    lower = text.lower()
    return any(keyword in lower for keyword in MARKETING_KEYWORDS)


def detect_complex_task(text: str) -> bool:
    """Detect if task is complex (should use Sonnet)."""
    lower = text.lower()
    return any(keyword in lower for keyword in COMPLEX_KEYWORDS)


def select_model(prompt: str, effort_mode: bool = False) -> str:
    """Select model based on prompt and effort mode."""
    if not effort_mode:
        return "sonnet"

    is_marketing = detect_marketing_prompt(prompt)
    is_complex = detect_complex_task(prompt)

    # Use Sonnet if complex, otherwise Haiku for marketing/routine tasks
    if is_complex and is_marketing:
        return "sonnet"

    if is_marketing:
        return "haiku"

    return "sonnet"


def get_thinking_tokens(prompt: str, effort_mode: bool = False) -> int:
    """Get max thinking tokens based on prompt complexity."""
    if not effort_mode:
        return 131072  # Claude default

    is_marketing = detect_marketing_prompt(prompt)
    is_complex = detect_complex_task(prompt)

    # Simple marketing prompts: 4k tokens
    if is_marketing and not is_complex:
        # Check for very simple tasks
        if len(prompt) < 100:
            return 4000
        return 8000

    # Complex or non-marketing: full tokens
    return 131072


def apply_effort_config(prompt: str, enabled: bool = False) -> dict:
    """Apply low-effort mode configuration to a prompt."""
    if not enabled:
        return {
            "enabled": False,
            "model": "sonnet",
            "max_thinking_tokens": 131072,
            "savings": None
        }

    model = select_model(prompt, effort_mode=True)
    thinking_tokens = get_thinking_tokens(prompt, effort_mode=True)

    # Estimate cost savings (rough approximation)
    is_marketing = detect_marketing_prompt(prompt)
    savings = None
    if is_marketing:
        if model == "haiku" and thinking_tokens <= 8000:
            savings = "~85% (Haiku + reduced thinking)"
        elif model == "haiku":
            savings = "~60% (Haiku model)"
        elif thinking_tokens <= 8000:
            savings = "~40% (reduced thinking tokens)"

    return {
        "enabled": True,
        "model": model,
        "max_thinking_tokens": thinking_tokens,
        "is_marketing_prompt": is_marketing,
        "is_complex_task": detect_complex_task(prompt),
        "savings": savings
    }


def format_effort_info(config: dict) -> str:
    """Format effort configuration info for display."""
    if not config["enabled"]:
        return "Effort mode: OFF (standard Claude Sonnet, full thinking)"

    model_name = config["model"].upper()
    tokens = config["max_thinking_tokens"]
    info = f"🚀 Effort mode: LOW\n"
    info += f"  Model: {model_name}\n"
    info += f"  Max thinking: {tokens:,} tokens\n"

    if config["is_marketing_prompt"]:
        info += f"  ✓ Detected marketing prompt\n"

    if config.get("savings"):
        info += f"  💰 Estimated savings: {config['savings']}\n"

    return info


# Test the implementation
if __name__ == "__main__":
    test_prompts = [
        "Generate 5 crypto tweet variants",
        "Write an Instagram caption for our NFT collection",
        "Deep analysis of blockchain architecture",
        "Create a social media campaign for our new product launch",
    ]

    print("=== LOW-EFFORT MODE TEST ===\n")

    for prompt in test_prompts:
        print(f"Prompt: {prompt}")
        config = apply_effort_config(prompt, enabled=True)
        print(format_effort_info(config))
        print()
