from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ValidationType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ENUM = "enum"
    DICT = "dict"
    LIST = "list"

@dataclass
class ValidationRule:
    type: ValidationType
    required: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None
    custom_validator: Optional[callable] = None

class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class Validator:
    def __init__(self, schema: Dict[str, ValidationRule]):
        self.schema = schema
    
    def validate(self, data: Dict) -> Dict[str, Any]:
        """Validate data against schema"""
        errors = {}
        validated_data = {}
        
        # Check required fields
        for field, rule in self.schema.items():
            if rule.required and field not in data:
                errors[field] = "Field is required"
                
        # Validate provided fields
        for field, value in data.items():
            if field in self.schema:
                try:
                    validated_data[field] = self._validate_field(
                        field, value, self.schema[field]
                    )
                except ValidationError as e:
                    errors[field] = e.message
        
        if errors:
            raise ValidationError("validation_failed", str(errors))
            
        return validated_data
    
    def _validate_field(self, field: str, value: Any, 
                       rule: ValidationRule) -> Any:
        """Validate a single field"""
        # Check custom validator first
        if rule.custom_validator:
            try:
                value = rule.custom_validator(value)
            except Exception as e:
                raise ValidationError(field, str(e))
        
        # Type validation
        if rule.type == ValidationType.STRING:
            if not isinstance(value, str):
                raise ValidationError(field, "Must be a string")
            if rule.min_length and len(value) < rule.min_length:
                raise ValidationError(
                    field, f"Must be at least {rule.min_length} characters"
                )
            if rule.max_length and len(value) > rule.max_length:
                raise ValidationError(
                    field, f"Must be at most {rule.max_length} characters"
                )
            if rule.pattern and not re.match(rule.pattern, value):
                raise ValidationError(field, "Does not match required pattern")
                
        elif rule.type == ValidationType.INTEGER:
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise ValidationError(field, "Must be an integer")
                
        elif rule.type == ValidationType.FLOAT:
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise ValidationError(field, "Must be a number")
                
        elif rule.type == ValidationType.BOOLEAN:
            if not isinstance(value, bool):
                raise ValidationError(field, "Must be a boolean")
                
        elif rule.type == ValidationType.ENUM:
            if rule.allowed_values and value not in rule.allowed_values:
                raise ValidationError(
                    field, f"Must be one of: {rule.allowed_values}"
                )
                
        elif rule.type == ValidationType.LIST:
            if not isinstance(value, list):
                raise ValidationError(field, "Must be a list")
                
        elif rule.type == ValidationType.DICT:
            if not isinstance(value, dict):
                raise ValidationError(field, "Must be a dictionary")
        
        # Range validation for numbers
        if rule.type in [ValidationType.INTEGER, ValidationType.FLOAT]:
            if rule.min_value is not None and value < rule.min_value:
                raise ValidationError(
                    field, f"Must be greater than or equal to {rule.min_value}"
                )
            if rule.max_value is not None and value > rule.max_value:
                raise ValidationError(
                    field, f"Must be less than or equal to {rule.max_value}"
                )
        
        return value
