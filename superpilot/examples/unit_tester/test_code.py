def factorial_iterative(n):
    """Calculate factorial using an iterative approach."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def factorial_recursive(n):
    """Calculate factorial using a recursive approach."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    if n == 0 or n == 1:
        return 1
    return n * factorial_recursive(n - 1)

def main():
    """Main function to get user input and compute factorial."""
    try:
        number = int(input("Enter a non-negative integer to compute its factorial: "))
        if number < 0:
            raise ValueError("The number must be a non-negative integer.")
        
        print(f"Factorial of {number} (iterative): {factorial_iterative(number)}")
        print(f"Factorial of {number} (recursive): {factorial_recursive(number)}")
        
    except ValueError as e:
        print(f"Invalid input: {e}")

if __name__ == "__main__":
    main()
