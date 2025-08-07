# app.py
# -*- coding: utf-8 -*-

import gradio as gr
import json
import re
from pydantic import BaseModel, ValidationError, create_model
from typing import Type, Dict, Any, List, Optional

# ==============================================================================
# 1. SEMANTIC PARSER CODE
# ==============================================================================

class ParsingError(Exception):
    """Custom exception for parsing failures."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context if context is not None else {}

class AdaptiveSemanticParser:
    """
    A robust parser that attempts to extract a JSON object from a string
    using a cascade of strategies.
    """
    def __init__(self):
        # Pre-compile the pattern for Markdown
        self.json_block_pattern = re.compile(
            r"```(?:json)?\s*\n({.*?})\n\s*```", re.DOTALL)

    def _validate_and_dump(self, data: Any, schema: Type[BaseModel]) -> Dict[str, Any]:
        """Helper function to validate and return data."""
        validated_model = schema.model_validate(data)
        return validated_model.model_dump()

        def _parse_semantic(self, text: str, schema: Type[BaseModel]) -> Dict[str, Any]:
        extracted_data: Dict[str, Any] = {}
        schema_fields = schema.model_fields
        
        for field_name in schema_fields.keys():
            try:
                pattern_friendly_name = field_name.replace('_', '[\\s_-]*')

                key_pattern = re.compile(f'["\']?{pattern_friendly_name}["\']?\\s*:', re.IGNORECASE)
                
                for match in key_pattern.finditer(text):
                    start_index = match.end()
                    potential_value_area = text[start_index:]
                                        
                    value_match = re.match(r'\s*(-?\d+\.?\d*)', potential_value_area)
                    if value_match:
                        extracted_data[field_name] = value_match.group(1)
                        continue

                    value_match = re.match(r'\s*["\'](.*?)["\']', potential_value_area)
                    if value_match:
                        extracted_data[field_name] = value_match.group(1)
                        continue

                    value_match = re.match(r'\s*(true|false)', potential_value_area, re.IGNORECASE)
                    if value_match:
                        extracted_data[field_name] = value_match.group(1).lower()
                        continue
                        
                    value_match = re.match(r'\s*([^\s,}\]]+)', potential_value_area)
                    if value_match:
                        value = value_match.group(1).rstrip('.')
                        extracted_data[field_name] = value
                        
            except Exception:
                continue

        if not extracted_data:
            raise ParsingError("Семантический слой не смог извлечь ни одного поля.")

        return self._validate_and_dump(extracted_data, schema)
                        
            except Exception:
                # If something went wrong while parsing a field, just skip it and move to the next one.
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

        # --- Layer 1: Find and extract JSON from Markdown blocks ---
        match = self.json_block_pattern.search(raw_llm_output)
        if match:
            json_str = match.group(1)
            try:
                # Try to parse the extracted JSON
                return self._validate_and_dump(json.loads(json_str), expected_schema)
            except (json.JSONDecodeError, ValidationError):
                # If it's broken, don't give up and pass it on
                raw_llm_output = json_str

        # --- Layer 2: Direct parsing (for clean JSON or extracted but broken JSON) ---
        try:
            # Remove JS/Python-style comments before parsing
            text_no_comments = re.sub(r'(?://|#).*', '', raw_llm_output)
            return self._validate_and_dump(json.loads(text_no_comments), expected_schema)
        except (json.JSONDecodeError, ValidationError):
            pass

        # --- Layer 3 (Final): Semantic extraction from text ---
        try:
            return self._parse_semantic(raw_llm_output, expected_schema)
        except (ParsingError, ValidationError) as e:
            # If even semantics didn't help, then it's over.
            raise ParsingError(
                "Failed to parse or validate the output after all layers.",
                context={"final_error": str(e)}
            )

# ==============================================================================
# 2. LOGIC FOR THE GRADIO DEMO
# ==============================================================================

adaptive_parser = AdaptiveSemanticParser()

TYPE_MAP = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": List,
    "dict": Dict,
    "any": Any,
}

def create_dynamic_schema(schema_definition: str) -> Type[BaseModel]:
    try:
        schema_dict = json.loads(schema_definition)
        if not isinstance(schema_dict, dict):
            raise TypeError("The schema definition must be a JSON object.")
        fields = {name: (TYPE_MAP.get(type_str.lower(), Any), ...) for name, type_str in schema_dict.items()}
        DynamicModel = create_model('DynamicModel', **fields)
        return DynamicModel
    except (json.JSONDecodeError, TypeError) as e:
        raise ValueError(f"Error in schema definition: {e}")

def run_parser_demo(raw_input: str, schema_definition: str):
    output_json = None
    output_error = ""
    if not raw_input.strip() or not schema_definition.strip():
        output_error = "Error: The input text and schema definition cannot be empty."
        return output_json, output_error
    try:
        expected_schema = create_dynamic_schema(schema_definition)
        parsed_data = adaptive_parser.parse(raw_input, expected_schema)
        output_json = parsed_data
    except (ParsingError, ValidationError, ValueError) as e:
        error_message = f"💥 An error occurred:\n\n{type(e).__name__}: {str(e)}"
        if hasattr(e, 'context') and e.context:
            error_message += f"\n\nError Context:\n{json.dumps(e.context, indent=2)}"
        output_error = error_message
    return output_json, output_error

# ==============================================================================
# 3. GRADIO INTERFACE DEFINITION
# ==============================================================================

description = """
# Adaptive Semantic Parser Demo 🚀
This tool demonstrates a parser that can extract structured data (JSON) even from messy, incomplete, or plain-text input.
**How to use:**
1.  **Define Schema:** In the "Schema Definition" box, specify the fields and types you expect in JSON format. E.g., `{"name": "str", "age": "int", "is_active": "bool"}`. Supported types: `str`, `int`, `float`, `bool`.
2.  **Enter Text:** In the "Messy JSON or Text to Parse" box, paste any text.
3.  **Click "Parse"** and see the result on the right!
"""

examples = [
    [
        'Here is the response from the LLM:\n\n```json\n{\n  "product_name": "Phoenix v1.4",\n  "version": 1.4,\n  "is_released": true\n}\n```\n\nAll done.',
        '{"product_name": "str", "version": "float", "is_released": "bool"}'
    ],
    [
        '{\n"user": "Alice",\n"login_attempts": 3,\n"last_login_at": "2025-08-07", // A comment that breaks JSON\n}',
        '{"user": "str", "login_attempts": "int", "last_login_at": "str"}'
    ],
    [
        'User profile data received. name: Bob, age: 30 years old, id: "user-123",',
        '{"name": "str", "age": "int", "id": "str"}'
    ],
    [
        'Here is some really messy output, missing a brace and quotes. \n{"city": "New York, \n"population": 8400000',
        '{"city": "str", "population": "int"}'
    ],
     [
        'Order number 42. Status: "in_progress". Amount: 199.99.',
        '{"order_number": "int", "status": "str", "amount": "float"}'
    ]
]

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown(description)
    with gr.Row():
        with gr.Column(scale=1):
            schema_input = gr.Textbox(label="1. Schema Definition (as JSON)", placeholder='E.g., {"name": "str", "age": "int"}', lines=5, value='{"name": "str", "age": "int", "city": "str"}')
            raw_text_input = gr.Textbox(label='2. Messy JSON or Text to Parse', placeholder="Paste any text here...", lines=10)
            parse_button = gr.Button("✅ Parse", variant="primary")
        with gr.Column(scale=1):
            gr.Markdown("### Result")
            output_json = gr.JSON(label="✅ Successfully Parsed & Validated")
            output_error = gr.Textbox(label="❌ Parsing Error", interactive=False, placeholder="Error details will appear here...")
    gr.Examples(examples=examples, inputs=[raw_text_input, schema_input], outputs=[output_json, output_error], fn=run_parser_demo, cache_examples=False)
    parse_button.click(fn=run_parser_demo, inputs=[raw_text_input, schema_input], outputs=[output_json, output_error])

if __name__ == "__main__":
    demo.launch()