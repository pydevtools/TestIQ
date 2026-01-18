"""
Simple Calculator - Source Code
This is intentionally simple to show how AI generates redundant tests.
"""

class Calculator:
    """Basic calculator operations"""

    def add(self, a: float, b: float) -> float:
        """Add two numbers"""
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a"""
        return a - b

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers"""
        return a * b

    def divide(self, a: float, b: float) -> float:
        """Divide a by b"""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    def power(self, a: float, b: float) -> float:
        """Raise a to power b"""
        return a ** b

    def modulo(self, a: int, b: int) -> int:
        """Get remainder of a / b"""
        if b == 0:
            raise ValueError("Cannot modulo by zero")
        return a % b

    def calculate(self, a: float, b: float, operation: str) -> float:
        """Perform calculation based on operation string"""
        if operation == '+':
            return self.add(a, b)
        elif operation == '-':
            return self.subtract(a, b)
        elif operation == '*':
            return self.multiply(a, b)
        elif operation == '/':
            return self.divide(a, b)
        elif operation == '**':
            return self.power(a, b)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def chain_operations(self, start: float, operations: list) -> float:
        """Chain multiple operations together
        operations is list of tuples: [(operation, value), ...]
        Example: [('+', 5), ('*', 2)] means start + 5, then * 2
        """
        result = start
        for operation, value in operations:
            result = self.calculate(result, value, operation)
        return result
