import unittest

from tools.visual_guide_extractor.quality import FallbackDecisionEngine


class FallbackDecisionTests(unittest.TestCase):
    def test_simple_high_confidence_page_skips_gemma(self):
        decision = FallbackDecisionEngine().decide(
            confidence_score=0.95, warning_count=0, uncertainty_count=1,
            unsupported_claim_count=0, step_count=3, image_count=2,
        )
        self.assertFalse(decision.use_gemma)
        self.assertEqual("simple", decision.page_complexity)

    def test_complex_page_requires_gemma(self):
        decision = FallbackDecisionEngine().decide(
            confidence_score=0.92, warning_count=0, uncertainty_count=1,
            unsupported_claim_count=0, step_count=14, image_count=4,
        )
        self.assertTrue(decision.use_gemma)
        self.assertIn("complex_multi_step_page", decision.reasons)

    def test_quality_failure_requires_gemma(self):
        decision = FallbackDecisionEngine().decide(
            confidence_score=0.70, warning_count=3, uncertainty_count=6,
            unsupported_claim_count=2, step_count=2, image_count=1,
        )
        self.assertTrue(decision.use_gemma)
        self.assertIn("low_confidence", decision.reasons)
        self.assertIn("unsupported_structure", decision.reasons)


if __name__ == "__main__":
    unittest.main()
