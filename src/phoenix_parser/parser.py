# src/phoenix_parser/parser.py (v1.2 - Robust)
# -*- coding: utf-8 -*-

import json
import re
from pydantic import BaseModel, ValidationError
from typing import Type, Dict, Any, Optional

class ParsingError(Exception):
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context if context is not None else {}

class AdaptiveSemanticParser:
    def __init__(self):
        self.json_block_pattern = re.compile(r"```(?:json)?\s*\n(.*?)\n\s*```", re.DOTALL)
        # Improved regex for removing comments, which works with multiline
        self.comment_pattern = re.compile(r"//.*?$|/\*.*?\*/", re.MULTILINE)

    def _clean_and_load(self, json_string: str, schema: Type[BaseModel]) -> Dict[str, Any]:
        """Universal method for cleaning and loading JSON."""
        # --- NEW CHANGE 1: Centralized cleaning ---
        # Replace "smart" quotes
        json_string = json_string.replace('“', '"').replace('”', '"')
        # Remove comments
        json_string = self.comment_pattern.sub('', json_string)
        
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            # If there's an error even after cleaning, let's try semantics
            raise e # Raise the error to move to the semantic layer

        # --- NEW CHANGE 2: Centralized type adaptation ---
        # This is the most important fix. It works for ANY clean JSON.
        for field_name, field_info in schema.model_fields.items():
            if field_name in data and field_info.annotation is int:
                # If the field should be an int, but it is not, we try to cast it
                if not isinstance(data[field_name], int):
                    try:
                        data[field_name] = int(float(data[field_name]))
                    except (ValueError, TypeError):
                        # If it fails, leave it as is, Pydantic will handle it
                        pass
        
        # Final validation
        validated_model = schema.model_validate(data)
        return validated_model.model_dump()

    def parse(self, raw_llm_output: str, expected_schema: Type[BaseModel]) -> Dict[str, Any]:
        """The main method that goes through a cascade of parsers."""
        if not raw_llm_output or not raw_llm_output.strip():
            raise ParsingError("Input text is empty or consists of whitespace.")

        text_to_parse = raw_llm_output
        
        # Layer 1: Search for a JSON block
        match = self.json_block_pattern.search(raw_llm_output)
        if match:
            text_to_parse = match.group(1) # We only work with the content of the block

        # Layers 2 and 3: Attempt direct parsing with cleaning, then semantics
        try:
            # Trying to parse in the most reliable way
            return self._clean_and_load(text_to_parse, expected_schema)
        except (json.JSONDecodeError, ValidationError):
            # If it failed - the last resort is semantic parsing
            # (The _parse_semantic code has not been changed, as it was not called in failures)
            try:
                # IMPORTANT: We are using the ENTIRE text again, not just the JSON block,
                # as there might be junk in the block, and semantics will work on the surrounding text.
                return self._parse_semantic_fallback(raw_llm_output, expected_schema)
            except (ParsingError, ValidationError) as e:
                 raise ParsingError("Failed after all layers.", context={"final_error": str(e)})

    def _parse_semantic_fallback(self, text: str, schema: Type[BaseModel]) -> Dict[str, Any]:
        """Semantic parser, used as a last resort."""
        # Cleaning "smart" quotes here as well
        text = text.replace('“', '"').replace('”', '"')
        
        extracted_data: Dict[str, Any] = {}
        schema_fields = schema.model_fields.items()

        for field_name, field_info in schema_fields:
            try:
                pattern_friendly_name = field_name.replace('_', '[\\s_-]*')
                key_pattern = re.compile(f'["\']?{pattern_friendly_name}["\']?\\s*[:=]?', re.IGNORECASE)
                
                for match in key_pattern.finditer(text):
                    start_index = match.end()
                    potential_value_area = text[start_index:].lstrip()
                    
                    value_to_add = None

                    value_match = re.match(r'(-?\d+(?:\.\d+)?)', potential_value_area)
                    if value_to_add is None and value_match: value_to_add = value_match.group(1)

                    value_match = re.match(r'["\'](.*?)["\']', potential_value_area)
                    if value_to_add is None and value_match: value_to_add = value_match.group(1)
                        
                    value_match = re.match(r'(true|false)', potential_value_area, re.IGNORECASE)
                    if value_to_add is None and value_match: value_to_add = value_match.group(1).lower()
                        
                    value_match = re.match(r'([^\s,}\]]+)', potential_value_area)
                    if value_to_add is None and value_match: value_to_add = value_match.group(1)
                    
                    if value_to_add is not None:
                        value_to_add = value_to_add.rstrip('.,;/\\')
                        extracted_data[field_name] = value_to_add
                        break
            except Exception:
                continue

        if not extracted_data:
            raise ParsingError("Semantic layer couldn't extract any fields.")

        # Applying adaptive typing here as well
        for field_name, field_info in schema.model_fields.items():
            if field_name in extracted_data and field_info.annotation is int:
                if not isinstance(extracted_data[field_name], int):
                    try:
                        extracted_data[field_name] = int(float(extracted_data[field_name]))
                    except (ValueError, TypeError):
                        pass

        validated_model = schema.model_validate(extracted_data)
        return validated_model.model_dump()
