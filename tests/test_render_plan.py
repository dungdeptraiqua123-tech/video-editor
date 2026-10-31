"""Số luồng render và bộ đệm khung hình phải vừa RAM còn trống (máy ít RAM từng bị tràn khi render)."""
import unittest

from ve.env import render_plan
from ve.doctor import auto_model
from unittest import mock

GB = 1 << 30


class RenderPlanTest(unittest.TestCase):
    def test_measured_case(self):
        # 4 nhân, còn 4,9 GB: đã đo chạy hết với 4 luồng, bộ đệm 1 GB
        conc, cache = render_plan(4.9, 4)
        self.assertEqual(conc, 4)
        self.assertLessEqual(cache, 1.05 * GB)

    def test_low_ram_fewer_threads(self):
        self.assertEqual(render_plan(3.0, 4)[0], 2)
        self.assertEqual(render_plan(1.5, 8)[0], 1)

    def test_cache_bounds(self):
        self.assertEqual(render_plan(1.0, 4)[1], GB // 2)
        self.assertEqual(render_plan(64, 16)[1], 2 * GB)

    def test_unknown_ram_is_safe(self):
        conc, cache = render_plan(0, 32)
        self.assertLessEqual(conc, 4)
        self.assertEqual(cache, GB)

    def test_many_cores_keep_one_free(self):
        self.assertEqual(render_plan(32, 8)[0], 7)


class AutoModelTest(unittest.TestCase):
    def test_choice_by_ram(self):
        for ram, want in ((8.2, "large-v3-turbo"), (16, "large-v3"), (4, "large-v3-turbo"), (3, "small")):
            with mock.patch("ve.doctor.ram_gb", return_value=ram):
                self.assertEqual(auto_model(), want, ram)


if __name__ == "__main__":
    unittest.main()
