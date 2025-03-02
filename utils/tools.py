from typing import Dict, Any, Callable, Tuple, Optional
from pydantic import BaseModel
from openai import pydantic_function_tool
import inspect

class ToolRegistry:
    """A registry class to manage tools and their schemas"""
    def __init__(self):
        self.schemas: Dict[str, BaseModel] = {}
        self.functions: Dict[str, Callable] = {}
    
    def register(self, func: Callable, schema: BaseModel) -> None:
        """
        Register a new tool with its schema.
        
        Args:
            func: The function to register
            schema: The pydantic model schema for the function
        """
        self.schemas[func.__name__] = schema
        self.functions[func.__name__] = func
    
    def get_schema(self, name: str) -> BaseModel:
        """Get schema by function name"""
        return self.schemas.get(name)
    
    def get_function(self, name: str) -> Callable:
        """Get function by name"""
        return self.functions.get(name)
    
    def call_function(self, name: str, args: dict) -> Any:
        """Call a function by name with arguments"""
        func = self.get_function(name)
        return func(**args)
    
    def generate_openai_schema(self, func: Callable) -> dict:
        """Generate OpenAI compatible schema for a function"""
        json_schema = pydantic_function_tool(self.schemas[func.__name__])
        json_schema["description"] = inspect.getdoc(func) or "No description available."
        return json_schema
    
    def get_all_tool_schemas(self) -> list:
        """Generate schemas for all registered tools"""
        return [self.generate_openai_schema(func) for func in self.functions.values()]