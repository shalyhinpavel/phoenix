# app.py
# -*- coding: utf-8 -*-

# ==============================================================================
# 0. IMPORT THE CORE PARSER FROM OUR LIBRARY
# ==============================================================================
from src.phoenix_parser.parser import AdaptiveSemanticParser, ParsingError

import gradio as gr
import json
from pydantic import BaseModel, ValidationError, create_model
from typing import Type, Dict, Any, List

# ==============================================================================
# 1. LOGIC FOR THE GRADIO DEMO
# ==============================================================================

adaptive_parser = AdaptiveSemanticParser()

TYPE_MAP = {
    "str": str, "int": int, "float": float, "bool": bool,
    "list": List, "dict": Dict, "any": Any,
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
            error_message += f"\n\nError Context:\n{json.dumps(e.context, indent=2, ensure_ascii=False)}"
        output_error = error_message
    return output_json, output_error

# ==============================================================================
# 2. GRADIO INTERFACE DEFINITION
# ==============================================================================
description = """
# Adaptive Semantic Parser Demo 🚀
This tool demonstrates a parser that can extract structured data (JSON) even from messy, incomplete, or plain-text input.
**How to use:**
1.  **Define Schema:** In the "Schema Definition" box, specify the fields and types you expect in JSON format. E.g., `{"name": "str", "age": "int"}`.
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
            schema_input = gr.Textbox(label="1. Schema Definition (as JSON)", placeholder='E.g., {"name": "str", "age": "int"}', lines=5, value='{"order_number": "int", "status": "str", "amount": "float"}')
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
