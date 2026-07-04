def fibonacci_series(n):
    # Check for invalid input
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    # Initialize the Fibonacci series list
    fib_series = []
    # Generate Fibonacci series up to n numbers
    for i in range(n):
        if i == 0:
            fib_series.append(0)  # First Fibonacci number
        elif i == 1:
            fib_series.append(1)  # Second Fibonacci number
        else:
            # Next Fibonacci number is the sum of the last two
            fib_series.append(fib_series[-1] + fib_series[-2])
    return fib_series