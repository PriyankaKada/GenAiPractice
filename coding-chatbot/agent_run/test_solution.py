import pytest
from solution import fibonacci_series

def test_fibonacci_series():
    # Test typical case
    assert fibonacci_series(5) == [0, 1, 1, 2, 3]
    # Test edge case: n = 0 (should return an empty list)
    assert fibonacci_series(0) == []
    # Test edge case: n = 1 (should return the first Fibonacci number)
    assert fibonacci_series(1) == [0]
    # Test edge case: n = 2 (should return the first two Fibonacci numbers)
    assert fibonacci_series(2) == [0, 1]
    # Test edge case: n = 3 (should return the first three Fibonacci numbers)
    assert fibonacci_series(3) == [0, 1, 1]
    # Test edge case: n = 10 (to check larger input)
    assert fibonacci_series(10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    # Test invalid input: n = -5 (should ideally raise an error or return an empty list)
    with pytest.raises(ValueError):
        fibonacci_series(-5)