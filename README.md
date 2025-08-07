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
short_description: A resilient semantic parser for LLM output
---
![alt text](https://img.shields.io/badge/License-Apache_2.0-blue.svg)

Phoenix: A Resilient Semantic Parser for LLM Output

LLMs often fail when generating strict JSON, which leads to crashes in AI systems. Phoenix is a three-tiered cascading parser that can extract structured data even from unstructured text, solving the problem of unreliability.

The Problem is Proven: Google's Announcement

The importance of this problem was confirmed on August 7, 2025, when Google announced "JSON Mode" for Gemini. However, this solution is tied to a single provider and will not work if the model is fundamentally unable to provide a response in JSON format.

Phoenix offers a more universal and reliable solution.

Aspect	Google JSON Mode	Phoenix Adaptive Parser
Approach	Server-side	Client-side
Reliability	High (guarantees syntax)	Maximum (salvages data)
Versatility	Low (Gemini only)	Absolute (any LLM)
Control	Zero (hidden logic)	Full (open source)
How it works? The "Resilience Cascade"

Phoenix passes the LLM output through three layers of protection:

Markdown Search: First, it looks for JSON in standard ```json...``` blocks.

Direct Parsing: Then, it attempts to parse the output as pure JSON.

Semantic Extraction: If all else fails, it searches the text for key: value pairs and reconstructs the structure from them. This is its superpower.

Try it yourself

Instructions: Paste "broken" or unstructured output from any LLM (for example, plain text with pairs like "name: John, age: 30") into the demo interface. Watch how Phoenix extracts valid JSON from it.

Phoenix is a key component of the Mycelium architecture, ensuring the stability of its cognitive core.

