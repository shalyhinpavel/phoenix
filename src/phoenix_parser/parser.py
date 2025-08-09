# -*- coding: utf-8 -*-
import json
import re
from pydantic import BaseModel, ValidationError
from typing import Type, Dict, Any, Optional, List


class ParsingError(Exception):
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context if context is not None else {}


class AdaptiveSemanticParser:
    def __init__(self):
        self.json_block_pattern = re.compile(
            r"```(?:json)?\s*\n(.*?)\n\s*```", re.DOTALL)
        self.comment_pattern = re.compile(r"//.*?$|/\*.*?\*/", re.MULTILINE)

    def _repair_and_load(self, json_string: str) -> Dict[str, Any]:
        """Tries to load JSON. If it fails, tries to repair and load again."""
        try:
            return json.loads(json_string)
        except json.JSONDecodeError:
            repaired_string = self._repair_truncated_json(json_string)
            return json.loads(repaired_string)

    def _repair_truncated_json(self, s: str) -> str:
        """A more robust function to fix truncated JSON strings."""
        # Find the last valid token by searching backwards
        last_token_pos = -1
        for i in range(len(s) - 1, -1, -1):
            if s[i] in '{},[]"\'0123456789':
                last_token_pos = i + 1
                break
        if last_token_pos != -1:
            s = s[:last_token_pos]
        # Balance braces and brackets
        open_braces = s.count('{') - s.count('}')
        open_brackets = s.count('[') - s.count(']')
        s += ']' * open_brackets
        s += '}' * open_braces
        return s

    def _heal_and_validate(self, data: Dict[str, Any], schema: Type[BaseModel]) -> Dict[str, Any]:
        """Tries to validate data. If it fails, it HEALS the data and tries again."""
        try:
            validated_model = schema.model_validate(data)
            return validated_model.model_dump()
        except ValidationError:
            healed_data = self._heal_data(data, schema)
            validated_model = schema.model_validate(healed_data)
            return validated_model.model_dump()

    def _heal_data(self, data: Dict[str, Any], schema: Type[BaseModel]) -> Dict[str, Any]:
        """The ultimate healing function based on all our findings."""
        healed_data = data.copy()
        for field_name, field_info in schema.model_fields.items():
            if field_name not in healed_data:
                continue
            expected_type = field_info.annotation
            current_value = healed_data[field_name]
            # Rule 1: Fix WRONG TYPES
            if expected_type is int and not isinstance(current_value, int):
                num_str = str(current_value)
                # Handles positive/negative integers
                match = re.search(r'[-+]?\d+', num_str)
                if match:
                    try:
                        healed_data[field_name] = int(match.group(0))
                    except (ValueError, TypeError):
                        pass
            # Rule 2: FLATTEN NESTED OBJECTS
            if expected_type in [str, int, float, bool] and isinstance(current_value, dict):
                # Intelligent search for a meaningful value inside the nested dict
                for key in ['value', 'data', 'text', 'result', 'overall', 'type', 'sentiment', 'name']:
                    if key in current_value:
                        healed_data[field_name] = current_value[key]
                        break  # Found a good key, stop searching
        return healed_data

    def parse(self, raw_llm_output: str, expected_schema: Type[BaseModel]) -> Dict[str, Any]:
        """The final, mirrored, most robust cascade, v6.0"""
        if not raw_llm_output or not raw_llm_output.strip():
            raise ParsingError("Input text is empty.")

        text_to_process = raw_llm_output

        match = self.json_block_pattern.search(text_to_process)
        if match:
            text_to_process = match.group(1)
        else:
            try:
                start = text_to_process.index('{')
                end = text_to_process.rindex('}') + 1
                text_to_process = text_to_process[start:end]
            except ValueError:
                pass
        # --------------------------------------------------------

        # Layer 2: Direct Parsing with Repair & Healing
        try:
            cleaned_text = text_to_process.replace('“', '"').replace('”', '"')
            cleaned_text = self.comment_pattern.sub('', cleaned_text)
            data = self._repair_and_load(cleaned_text)
            return self._heal_and_validate(data, expected_schema)
        except (json.JSONDecodeError, ValidationError):
            pass

        # Layer 3: Semantic Extraction (The Final Fallback)
        try:
            semantic_data = self._parse_semantic_fallback(
                raw_llm_output, expected_schema)
            return self._heal_and_validate(semantic_data, expected_schema)
        except (ParsingError, ValidationError) as e:
            raise ParsingError("Failed after all layers.",
                               context={"final_error": str(e)})

    def _parse_semantic_fallback(self, text: str, schema: Type[BaseModel]) -> Dict[str, Any]:
        # Cleaning "smart" quotes here as well
        text = text.replace('“', '"').replace('”', '"')
        extracted_data: Dict[str, Any] = {}
        schema_fields = schema.model_fields.items()
        for field_name, field_info in schema_fields:
            try:
                pattern_friendly_name = field_name.replace('_', '[\\s_-]*')
                key_pattern = re.compile(
                    f'["\']?{pattern_friendly_name}["\']?\\s*[:=]?', re.IGNORECASE)
                for match in key_pattern.finditer(text):
                    start_index = match.end()
                    potential_value_area = text[start_index:].lstrip()
                    value_to_add = None
                    value_match = re.match(
                        r'(-?\d+(?:\.\d+)?)', potential_value_area)
                    if value_to_add is None and value_match:
                        value_to_add = value_match.group(1)
                    value_match = re.match(
                        r'["\'](.*?)["\']', potential_value_area)
                    if value_to_add is None and value_match:
                        value_to_add = value_match.group(1)
                    value_match = re.match(
                        r'(true|false)', potential_value_area, re.IGNORECASE)
                    if value_to_add is None and value_match:
                        value_to_add = value_match.group(1).lower()
                    value_match = re.match(
                        r'([^\s,}\]]+)', potential_value_area)
                    if value_to_add is None and value_match:
                        value_to_add = value_match.group(1)
                    if value_to_add is not None:
                        value_to_add = value_to_add.rstrip('.,;/\\')
                        extracted_data[field_name] = value_to_add
                        break
            except Exception:
                continue
        if not extracted_data:
            raise ParsingError("Semantic layer couldn't extract any fields.")
        # Applying adaptive typing here as well
        for field_name, field_info in schema_fields:
            if field_name in extracted_data and field_info.annotation is int:
                if not isinstance(extracted_data[field_name], int):
                    try:
                        extracted_data[field_name] = int(
                            float(extracted_data[field_name]))
                    except (ValueError, TypeError):
                        pass
        # We don't return directly, we return it to the main parse function for a final heal/validation
        return extracted_data
