#!/usr/bin/env python3
"""
Claude Code Skill: /effort [low|off]

Manages low-effort mode for cost reduction on marketing tasks.
Integrates with Claude Code to automatically select cheaper models
and reduced thinking tokens for routine marketing prompts.
"""

import json
import os
import sys
from pathlib import Path
from low_effort_mode import (
    apply_effort_config,
    format_effort_info,
    EffortConfig
)


class EffortSkillHandler:
    """Manages /effort command for Claude Code."""

    CONFIG_PATH = Path.home() / ".claude" / "effort_mode_config.json"

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load existing config or create new one."""
        if self.CONFIG_PATH.exists():
            try:
                with open(self.CONFIG_PATH) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"enabled": False, "max_thinking_tokens": 131072}

    def _save_config(self):
        """Save config to file."""
        self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=2)

    def enable_low_effort(self, max_tokens: int = 8000) -> str:
        """Enable low-effort mode."""
        self.config["enabled"] = True
        self.config["max_thinking_tokens"] = max_tokens
        self._save_config()

        os.environ["EFFORT_MODE"] = "low"
        os.environ["MAX_THINKING_TOKENS"] = str(max_tokens)

        return (
            "✅ Low-effort mode ENABLED\n"
            f"  Max thinking tokens: {max_tokens:,}\n"
            "  Marketing prompts → Haiku (85% cost savings)\n"
            "  Complex tasks → Sonnet (full capability)\n\n"
            "💡 Tip: Use '/effort off' to disable or '/effort status' to check settings"
        )

    def disable_low_effort(self) -> str:
        """Disable low-effort mode."""
        self.config["enabled"] = False
        self._save_config()

        if "EFFORT_MODE" in os.environ:
            del os.environ["EFFORT_MODE"]

        return (
            "✅ Low-effort mode DISABLED\n"
            "  Using standard Claude Sonnet with full thinking tokens\n\n"
            "💡 Tip: Use '/effort low' to re-enable for marketing tasks"
        )

    def get_status(self) -> str:
        """Get current effort mode status."""
        if not self.config["enabled"]:
            return (
                "Low-effort mode: **OFF**\n"
                "Using standard: Claude Sonnet, full thinking tokens (131,072)\n\n"
                "To enable: `/effort low`"
            )

        tokens = self.config["max_thinking_tokens"]
        return (
            "Low-effort mode: **ON** 🚀\n"
            f"Max thinking tokens: {tokens:,}\n"
                "Marketing prompts: Haiku (~85% savings)\n"
                "Complex tasks: Sonnet (full capability)\n\n"
                "To disable: `/effort off`"
            )

    def analyze_prompt(self, prompt: str) -> str:
        """Analyze how effort mode would handle a specific prompt."""
        if not self.config["enabled"]:
            return "Low-effort mode is disabled. Use '/effort low' to enable."

        config = apply_effort_config(prompt, enabled=True)
        return format_effort_info(config)

    def handle_command(self, args: list[str]) -> str:
        """Handle /effort command with arguments."""
        if not args:
            return self.get_status()

        command = args[0].lower()

        if command == "low":
            max_tokens = 8000
            if len(args) > 1:
                try:
                    max_tokens = int(args[1])
                except ValueError:
                    pass
            return self.enable_low_effort(max_tokens)

        elif command == "off":
            return self.disable_low_effort()

        elif command == "status":
            return self.get_status()

        elif command == "analyze" and len(args) > 1:
            prompt = " ".join(args[1:])
            return self.analyze_prompt(prompt)

        else:
            return (
                "Unknown /effort command. Available commands:\n"
                "  `/effort low [tokens]` — Enable low-effort mode (default: 8000 tokens)\n"
                "  `/effort off` — Disable low-effort mode\n"
                "  `/effort status` — Show current settings\n"
                "  `/effort analyze <prompt>` — Analyze how a prompt would be handled"
            )


def main():
    """CLI entry point for testing."""
    handler = EffortSkillHandler()

    if len(sys.argv) > 1:
        result = handler.handle_command(sys.argv[1:])
    else:
        result = handler.get_status()

    print(result)


if __name__ == "__main__":
    main()
