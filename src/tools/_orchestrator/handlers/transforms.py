# Transform handlers: arithmetic operations (pure functions, deterministic)

from .base import AbstractHandler

class IncrementHandler(AbstractHandler):
    """Increment a numeric value by 1"""
    
    @property
    def kind(self) -> str:
        return "increment"
    
    def run(self, value=0, **kwargs) -> dict:
        """
        Args:
            value: Number to increment (default: 0)
        
        Returns:
            {"result": value + 1}
        """
        try:
            result = float(value) + 1
            # Return int if no decimal part
            if result == int(result):
                result = int(result)
            return {"result": result}
        except (ValueError, TypeError):
            raise ValueError(f"increment: value must be numeric, got {type(value).__name__}")


class DecrementHandler(AbstractHandler):
    """Decrement a numeric value by 1"""
    
    @property
    def kind(self) -> str:
        return "decrement"
    
    def run(self, value=0, **kwargs) -> dict:
        """
        Args:
            value: Number to decrement (default: 0)
        
        Returns:
            {"result": value - 1}
        """
        try:
            result = float(value) - 1
            if result == int(result):
                result = int(result)
            return {"result": result}
        except (ValueError, TypeError):
            raise ValueError(f"decrement: value must be numeric, got {type(value).__name__}")


class AddHandler(AbstractHandler):
    """Add two numeric values"""
    
    @property
    def kind(self) -> str:
        return "add"
    
    def run(self, value=0, amount=0, **kwargs) -> dict:
        """
        Args:
            value: Base value
            amount: Amount to add
        
        Returns:
            {"result": value + amount}
        """
        try:
            result = float(value) + float(amount)
            if result == int(result):
                result = int(result)
            return {"result": result}
        except (ValueError, TypeError):
            raise ValueError(f"add: value and amount must be numeric")


class MultiplyHandler(AbstractHandler):
    """Multiply two numeric values"""
    
    @property
    def kind(self) -> str:
        return "multiply"
    
    def run(self, value=1, factor=1, **kwargs) -> dict:
        """
        Args:
            value: Base value
            factor: Multiplier
        
        Returns:
            {"result": value * factor}
        """
        try:
            result = float(value) * float(factor)
            if result == int(result):
                result = int(result)
            return {"result": result}
        except (ValueError, TypeError):
            raise ValueError(f"multiply: value and factor must be numeric")


class SetValueHandler(AbstractHandler):
    """Set a constant value"""
    
    @property
    def kind(self) -> str:
        return "set_value"
    
    def run(self, value, **kwargs) -> dict:
        """
        Args:
            value: Value to set (any type)
        
        Returns:
            {"result": value}
        """
        return {"result": value}
