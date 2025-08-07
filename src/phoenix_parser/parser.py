# src/phoenix_parser/parser.py (v1.1)
# -*- coding: utf-8 -*-

import json
import re
from pydantic import BaseModel, ValidationError
from typing import Type, Dict, Any, Optional

# ==============================================================================
# PHOENIX v1.1: THE CORE PARSING LIBRARY
# ==============================================================================

class ParsingError(Exception):
    # ... (без изменений) ...
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context if context is not None else {}

class AdaptiveSemanticParser:
    """
    A robust parser that attempts to extract a JSON object from a string
    using a cascade of strategies.
    """
    def __init__(self):
        self.json_block_pattern = re.compile(
            r"```(?:json)?\s*\n(.*?)\n\s*```", re.DOTALL
        )

    def _validate_and_dump(self, data: Any, schema: Type[BaseModel]) -> Dict[str, Any]:
        validated_model = schema.model_validate(data)
        return validated_model.model_dump()

    def _parse_semantic(self, text: str, schema: Type[BaseModel]) -> Dict[str, Any]:
        extracted_data: Dict[str, Any] = {}
        schema_fields = schema.model_fields
        
        for field_name, field_info in schema_fields.items():
            try:
                pattern_friendly_name = field_name.replace('_', '[\\s_-]*')
                key_pattern = re.compile(f'["\']?{pattern_friendly_name}["\']?\\s*[:=]?', re.IGNORECASE)
                
                for match in key_pattern.finditer(text):
                    start_index = match.end()
                    potential_value_area = text[start_index:].lstrip()
                    
                    value_to_add = None
                    value_match = re.match(r'(-?\d+(?:\.\d+)?)', potential_value_area)
                    if value_match:
                        value_to_add = value_match.group(1)

                    if value_to_add is None:
                        value_match = re.match(r'["\'](.*?)["\']', potential_value_area)
                        if value_match:
                            value_to_add = value_match.group(1)

                    if value_to_add is None:
                        value_match = re.match(r'(true|false)', potential_value_area, re.IGNORECASE)
                        if value_match:
                            value_to_add = value_match.group(1).lower()
                        
                    if value_to_add is None:
                        value_match = re.match(r'([^\s,}\]]+)', potential_value_area)
                        if value_match:
                            value_to_add = value_match.group(1)
                    
                    if value_to_add is not None:
                        value_to_add = value_to_add.rstrip('.,;/\\')
                        
                        if field_info.annotation is int and '.' in str(value_to_add):
                            try:
                                value_to_add = str(round(float(value_to_add)))
                            except ValueError:
                                pass # Оставляем как есть, если не число
                        
                        extracted_data[field_name] = value_to_add
                        break 
                        
            except Exception:
                continue

        if not extracted_data:
            raise ParsingError("The semantic layer could not extract any fields.")

        return self._validate_and_dump(extracted_data, schema)

    def parse(self, raw_llm_output: str, expected_schema: Type[BaseModel]) -> Dict[str, Any]:
        """
        The main method that passes the LLM output through a cascade of parsers.
        """
        if not raw_llm_output or not raw_llm_output.strip():
            raise ParsingError("Input text is empty or consists of whitespace.")

        cleaned_output = raw_llm_output.replace('“', '"').replace('”', '"')

        match = self.json_block_pattern.search(cleaned_output)
        if match:
            json_str = match.group(1)
            try:
                return self._validate_and_dump(json.loads(json_str), expected_schema)
            except (json.JSONDecodeError, ValidationError):
                text_to_parse = json_str
        else:
           
            text_to_parse = cleaned_output

        try:
            return self._validate_and_dump(json.loads(text_to_parse), expected_schema)
        except (json.JSONDecodeError, ValidationError):
            pass

        try:
            return self._parse_semantic(text_to_parse, expected_schema)
        except (ParsingError, ValidationError) as e:
            raise ParsingError(
                "Failed to parse or validate the output after all layers.",
                context={"final_error": str(e)}
            )
