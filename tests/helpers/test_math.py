from pathlib import Path

import pytest
import sys
from pathlib import Path as PathlibPath


from helpers.math import map_range


class TestMath:
    def test_map_range(self):
        assert map_range(5, 0, 10, 0, 50) == 25
        assert map_range(-5, -10, 10, 0, 50) == pytest.approx(12.5)
        assert map_range(0, -10, 10, 0, 50) == 25
        assert map_range(-10, 0, 10, 0, 100) == -100
