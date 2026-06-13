import unittest

from common.metrics import bit_error_count, bit_error_rate, text_bit_error_rate
from common.performance import longest_message_bytes_for_goal, plan_transmission


class MetricsTests(unittest.TestCase):
    def test_bit_error_count(self):
        self.assertEqual(bit_error_count(b"\x00", b"\x01"), 1)
        self.assertEqual(bit_error_count(b"\xff", b"\x00"), 8)

    def test_bit_error_rate(self):
        self.assertEqual(bit_error_rate(b"\x00", b"\x01"), 1 / 8)
        self.assertEqual(text_bit_error_rate("Hola", "Hola"), 0.0)


class PerformancePlanTests(unittest.TestCase):
    def test_4ask_halves_frame_count_for_500_character_goal(self):
        ook_plan = plan_transmission(
            "A" * 500,
            error_correction_bytes=16,
            frame_duration_ms=400,
            modulation="ook",
        )
        ask4_plan = plan_transmission(
            "A" * 500,
            error_correction_bytes=16,
            frame_duration_ms=400,
            modulation="4ask",
        )

        self.assertEqual(ook_plan.frame_count, 10)
        self.assertEqual(ask4_plan.frame_count, 5)
        self.assertEqual(ask4_plan.payload_capacity_bytes, 123)

    def test_500_character_goal_with_current_settings(self):
        plan = plan_transmission("A" * 500, error_correction_bytes=16, frame_duration_ms=150)

        self.assertEqual(plan.frame_count, 10)
        self.assertLessEqual(plan.estimated_seconds, 10.0)
        self.assertTrue(plan.meets_time_goal)
        self.assertTrue(plan.meets_sampling_goal)

    def test_repeated_sequence_still_fits_time_goal(self):
        plan = plan_transmission("A" * 500, error_correction_bytes=16, frame_duration_ms=150, repeat=2)

        self.assertEqual(plan.estimated_seconds, 3.0)
        self.assertTrue(plan.meets_time_goal)

    def test_longest_message_capacity_is_above_project_target(self):
        self.assertGreaterEqual(longest_message_bytes_for_goal(), 500)


if __name__ == "__main__":
    unittest.main()

