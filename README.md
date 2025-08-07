![alt text](https://img.shields.io/badge/License-Apache_2.0-blue.svg)

Phoenix: A Resilient Semantic Parser for LLM Output

Getting reliable structured data from LLMs is a fundamental engineering challenge. It's so crucial that Google recently released its open-source library, google/langextract, to tackle it using a classic, grammar-based approach.
Classic methods are dependable but rigid. They break the moment an LLM's output deviates from predefined rules. Phoenix introduces a next-generation solution. It doesn’t just follow rules—it understands meaning.
Here’s how the two approaches compare:

Classic Parsers (like google/langextract)

Technology: Relies on rigid Regular Expressions and Grammars.
Flexibility: Low, requiring the output to strictly follow predefined rules.
Failure Response: Typically results in a hard parsing error.
Paradigm: "Fixing chaos with rules."
License: Apache 2.0

The Phoenix Adaptive Parser
Technology: A hybrid model combining direct parsing with semantic understanding.
Flexibility: High, capable of interpreting natural language and messy structures.
Failure Response: Performs semantic data recovery to salvage information.
Paradigm: "Using intelligence to understand chaos."
License: Apache 2.0

The "Resilience Cascade": Phoenix's Secret Weapon

Phoenix processes LLM output through three layers of defense, ensuring you always get a result:
Markdown Search: It first looks for JSON inside standard ```json...``` code blocks.
Direct Parsing: It then attempts to parse the output as clean, raw JSON.
Semantic Extraction: If all else fails, Phoenix activates its superpower: it analyzes the raw text, finds key: value pairs within the unstructured content, and rebuilds the data from scratch.
