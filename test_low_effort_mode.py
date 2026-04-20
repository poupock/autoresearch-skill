"""
Test suite for low-effort mode implementation.
Tests marketing prompt detection, model selection, and cost optimization.
"""

import unittest
from low_effort_mode import (
    detect_marketing_prompt,
    detect_complex_task,
    select_model,
    get_thinking_tokens,
    apply_effort_config,
)
from effort_skill import EffortSkillHandler


class TestMarketingDetection(unittest.TestCase):
    """Test marketing prompt detection."""

    def test_crypto_tweet_detection(self):
        """Crypto tweet should be detected as marketing."""
        prompt = "Generate 5 crypto tweet variants"
        self.assertTrue(detect_marketing_prompt(prompt))

    def test_instagram_caption_detection(self):
        """Instagram caption should be detected as marketing."""
        prompt = "Write an Instagram caption for our NFT collection"
        self.assertTrue(detect_marketing_prompt(prompt))

    def test_social_media_campaign_detection(self):
        """Social media campaign should be detected as marketing."""
        prompt = "Create a social media campaign for our new product"
        self.assertTrue(detect_marketing_prompt(prompt))

    def test_smm_analysis_detection(self):
        """SMM analysis should be detected as marketing."""
        prompt = "Analyze SMM performance for our crypto account"
        self.assertTrue(detect_marketing_prompt(prompt))

    def test_ad_copy_detection(self):
        """Ad copy should be detected as marketing."""
        prompt = "Write compelling ad copy for our new NFT drop"
        self.assertTrue(detect_marketing_prompt(prompt))

    def test_non_marketing_detection(self):
        """Code review should not be detected as marketing."""
        prompt = "Review this Python function for security issues"
        self.assertFalse(detect_marketing_prompt(prompt))


class TestComplexityDetection(unittest.TestCase):
    """Test complex task detection."""

    def test_research_task_detection(self):
        """Research should be detected as complex."""
        prompt = "Research blockchain security implications"
        self.assertTrue(detect_complex_task(prompt))

    def test_architecture_detection(self):
        """Architecture design should be detected as complex."""
        prompt = "Design a microservices architecture for our platform"
        self.assertTrue(detect_complex_task(prompt))

    def test_strategy_detection(self):
        """Strategy should be detected as complex."""
        prompt = "Develop a go-to-market strategy"
        self.assertTrue(detect_complex_task(prompt))

    def test_simple_post_detection(self):
        """Simple post should not be detected as complex."""
        prompt = "Write a simple Twitter post"
        self.assertFalse(detect_complex_task(prompt))


class TestModelSelection(unittest.TestCase):
    """Test model selection logic."""

    def test_marketing_prompt_selects_haiku(self):
        """Marketing prompts should select Haiku in low-effort mode."""
        prompt = "Generate 5 crypto tweet variants"
        model = select_model(prompt, effort_mode=True)
        self.assertEqual(model, "haiku")

    def test_complex_task_selects_sonnet(self):
        """Complex tasks should select Sonnet even in low-effort mode."""
        prompt = "Design a comprehensive blockchain architecture"
        model = select_model(prompt, effort_mode=True)
        self.assertEqual(model, "sonnet")

    def test_effort_mode_off_selects_sonnet(self):
        """Should select Sonnet when effort mode is off."""
        prompt = "Generate 5 crypto tweet variants"
        model = select_model(prompt, effort_mode=False)
        self.assertEqual(model, "sonnet")


class TestThinkingTokenSelection(unittest.TestCase):
    """Test thinking token allocation."""

    def test_short_marketing_prompt_4k_tokens(self):
        """Very short marketing prompt should get 4k tokens."""
        prompt = "Tweet about NFT"  # 18 chars
        tokens = get_thinking_tokens(prompt, effort_mode=True)
        self.assertEqual(tokens, 4000)

    def test_medium_marketing_prompt_8k_tokens(self):
        """Medium marketing prompt should get 8k tokens."""
        prompt = "Generate 5 crypto tweet variants with multiple hashtags and engagement strategies for our new token launch this quarter"
        tokens = get_thinking_tokens(prompt, effort_mode=True)
        self.assertEqual(tokens, 8000)

    def test_complex_task_gets_full_tokens(self):
        """Complex tasks should get full thinking tokens."""
        prompt = "Research and analyze blockchain architecture"
        tokens = get_thinking_tokens(prompt, effort_mode=True)
        self.assertEqual(tokens, 131072)

    def test_effort_mode_off_gets_full_tokens(self):
        """Should get full tokens when effort mode is off."""
        prompt = "Generate 5 crypto tweet variants"
        tokens = get_thinking_tokens(prompt, effort_mode=False)
        self.assertEqual(tokens, 131072)


class TestEffortConfig(unittest.TestCase):
    """Test effort configuration application."""

    def test_crypto_tweet_config(self):
        """Crypto tweet should get Haiku + 4k tokens."""
        prompt = "Generate 5 crypto tweet variants"
        config = apply_effort_config(prompt, enabled=True)

        self.assertTrue(config["enabled"])
        self.assertEqual(config["model"], "haiku")
        self.assertEqual(config["max_thinking_tokens"], 4000)
        self.assertTrue(config["is_marketing_prompt"])
        self.assertIn("85%", config["savings"])

    def test_nft_caption_config(self):
        """NFT Instagram caption should get Haiku + 4k tokens for short prompts."""
        prompt = "Write an Instagram caption for our NFT collection launch"
        config = apply_effort_config(prompt, enabled=True)

        self.assertTrue(config["enabled"])
        self.assertEqual(config["model"], "haiku")
        self.assertEqual(config["max_thinking_tokens"], 4000)  # < 100 chars = 4k
        self.assertTrue(config["is_marketing_prompt"])
        self.assertIn("85%", config["savings"])

    def test_complex_blockchain_config(self):
        """Complex blockchain analysis should get Sonnet + full tokens."""
        prompt = "Deep analysis of blockchain architecture and security"
        config = apply_effort_config(prompt, enabled=True)

        self.assertTrue(config["enabled"])
        self.assertEqual(config["model"], "sonnet")
        self.assertEqual(config["max_thinking_tokens"], 131072)
        self.assertFalse(config["is_marketing_prompt"])

    def test_marketing_strategy_config(self):
        """Marketing strategy (complex) should get Sonnet + full tokens."""
        prompt = "Create a social media campaign strategy for crypto tokens"
        config = apply_effort_config(prompt, enabled=True)

        self.assertTrue(config["enabled"])
        self.assertEqual(config["model"], "sonnet")
        self.assertEqual(config["max_thinking_tokens"], 131072)
        self.assertTrue(config["is_marketing_prompt"])
        self.assertTrue(config["is_complex_task"])

    def test_effort_disabled(self):
        """Should return standard config when effort mode disabled."""
        prompt = "Generate crypto tweets"
        config = apply_effort_config(prompt, enabled=False)

        self.assertFalse(config["enabled"])
        self.assertEqual(config["model"], "sonnet")
        self.assertEqual(config["max_thinking_tokens"], 131072)


class TestEffortSkillHandler(unittest.TestCase):
    """Test /effort command handler."""

    def setUp(self):
        """Set up fresh handler for each test."""
        self.handler = EffortSkillHandler()

    def test_enable_command(self):
        """Test /effort low command."""
        result = self.handler.enable_low_effort()
        self.assertIn("✅", result)
        self.assertIn("Low-effort mode ENABLED", result)
        self.assertIn("85%", result)

    def test_disable_command(self):
        """Test /effort off command."""
        self.handler.enable_low_effort()
        result = self.handler.disable_low_effort()
        self.assertIn("✅", result)
        self.assertIn("Low-effort mode DISABLED", result)

    def test_status_when_enabled(self):
        """Test /effort status when enabled."""
        self.handler.enable_low_effort()
        result = self.handler.get_status()
        self.assertIn("ON", result)
        self.assertIn("🚀", result)

    def test_status_when_disabled(self):
        """Test /effort status when disabled."""
        self.handler.disable_low_effort()
        result = self.handler.get_status()
        self.assertIn("OFF", result)
        self.assertNotIn("🚀", result)


if __name__ == "__main__":
    unittest.main()
