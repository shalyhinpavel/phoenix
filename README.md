---
title: Phoenix
emoji: 🔥
colorFrom: purple
colorTo: red
sdk: gradio
sdk_version: 5.41.1
app_file: app.py
pinned: false
license: apache-2.0
short_description: An open, more reliable architecture for parsing LLM output.
---
![alt text](https://img.shields.io/badge/License-Apache_2.0-blue.svg)

Phoenix: A Resilient Semantic Parser for LLM Output

Obtaining reliable structured data from LLMs is a fundamental problem that, until recently, lacked an elegant solution. The fact that commercial services (like LangExtract.io) and this open-source project were born at virtually the same time proves one thing: the industry has reached a critical point where this problem MUST be solved.
Phoenix is not a reaction to a trend. It is an independent, architectural solution that was developed as a key component of a larger system, Mycelium.
Unlike commercial "black boxes," Phoenix offers an open, universal, and more reliable approach.

Comparison of Phoenix and Commercial Parsers

Aspect: Philosophy
Commercial Parsers: "Black box" as a service.
Phoenix Adaptive Parser: A transparent component in your code.

Aspect: Reliability
Commercial Parsers: Unknown (failure = data loss).
Phoenix Adaptive Parser: Maximum (semantically salvages data).

Aspect: Versatility
Commercial Parsers: Low (tied to a single service).
Phoenix Adaptive Parser: Absolute (works with any LLM).

Aspect: Cost
Commercial Parsers: Service fee + margin.
Phoenix Adaptive Parser: Only the cost of the direct LLM call.

The "Resilience Cascade": Phoenix's Secret Weapon
Unlike simple parsers, Phoenix passes the LLM output through three layers of protection, guaranteeing a result:
Markdown Search: Looks for JSON in standard ```json...``` blocks.
Direct Parsing: Attempts to parse the output as pure JSON.
Semantic Extraction: If all else fails, Phoenix activates its superpower: it finds key: value pairs in the raw text and reconstructs the structure from them. This is something "black boxes" cannot do.

Try it yourself
Instructions: Paste "broken" or unstructured output from any LLM (for example, plain text: "Client name: John, his age: 30, order status: delivered") into the demo interface. Phoenix will return a valid JSON for you.
