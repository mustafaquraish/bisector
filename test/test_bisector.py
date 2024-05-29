import pytest
from bisector import Bisector, BisectionResult, Status

class TestBisector:
    def run_bisect_test(self, options, bad_option, skips, expected_result, expected_value=None):
        b = Bisector(options)
        while not b.is_done():
            x = b.current
            if x in skips:
                b.set_skip()
            elif x < bad_option:
                b.set_good()
            else:
                b.set_bad()
        result, value = b.get_result()
        assert result == expected_result
        if expected_value is not None:
            assert value == expected_value

    @pytest.mark.parametrize("bad_option", [1, 2, 10, 25, 50, 75, 90, 99])
    def test_bisector_bad_no_skips(self, bad_option):
        self.run_bisect_test(list(range(100)), bad_option, {}, BisectionResult.FOUND_BAD, bad_option)

    @pytest.mark.parametrize("bad_option", [1, 2, 10, 25, 50, 75, 90, 99])
    def test_bisector_bad_with_statuses(self, bad_option):
        statuses = [
            Status.GOOD if i < bad_option else Status.BAD
            for i in range(100)
        ]
        options = list(range(100))
        b = Bisector(options, statuses)
        result, value = b.get_result()
        assert result == BisectionResult.FOUND_BAD
        assert value == bad_option
