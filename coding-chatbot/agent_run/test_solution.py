import pytest
from solution import is_prime

def test_is_prime():
    # Typical cases
    assert is_prime(2) == True
    assert is_prime(3) == True
    assert is_prime(4) == False
    assert is_prime(5) == True
    assert is_prime(29) == True
    assert is_prime(30) == False

    # Edge cases
    assert is_prime(1) == False  # 1 is not prime
    assert is_prime(0) == False  # 0 is not prime
    assert is_prime(-1) == False  # Negative numbers are not prime
    assert is_prime(-5) == False  # Negative numbers are not prime

    # Boundary cases
    assert is_prime(97) == True  # 97 is prime
    assert is_prime(100) == False  # 100 is not prime
    assert is_prime(101) == True  # 101 is prime

    # Invalid input cases
    with pytest.raises(TypeError):
        is_prime('a')  # String input
    with pytest.raises(TypeError):
        is_prime(None)  # None input
