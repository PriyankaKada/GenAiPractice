def is_prime(n):
    """
    Check if a number is prime.

    A prime number is a natural number greater than 1 that cannot be formed by multiplying two smaller natural numbers.
    This function returns True if the number is prime, otherwise False.
    """
    # Check if n is less than 2, which are not prime numbers
    if n < 2:
        return False
    # Check for factors from 2 to the square root of n
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False  # n is divisible by i, hence not prime
    return True  # No divisors found, n is prime