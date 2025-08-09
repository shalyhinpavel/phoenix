# Phoenix: A Robust Parser for LLM Outputs

[![PyPI Version](https://img.shields.io/pypi/v/phoenix-parser.svg)](https://pypi.org/project/phoenix-parser/)
[![License](https://img.shields.io/pypi/l/phoenix-parser.svg)](https://github.com/shalyhinpavel/phoenix/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/phoenix-parser.svg)](https://pypi.org/project/phoenix-parser/)

In the rapidly evolving world of AI, a single malformed JSON response from a Large Language Model (LLM) can lead to catastrophic failures in your application. This isn't an uncommon edge case; it's a persistent challenge for engineers building robust AI systems.

**Phoenix** is a lightweight, battle-tested Python library designed to make your AI applications resilient. It doesn't just parse data; it intelligently rescues it from chaotic LLM outputs.

---

## The Problem: "Cascading Collapse" in AI Systems

Modern AI applications, such as Retrieval-Augmented Generation (RAG) systems and autonomous agents, are rarely single LLM calls. Instead, they operate as **chains** of interdependent calls. If each individual call carries even a small probability of failure, the overall reliability of the entire chain degrades exponentially.

Consider a parser with **93%** reliability on a single LLM call:

*   A 3-step chain achieves only **80%** reliability (`0.93 * 0.93 * 0.93`).
*   A 5-step chain collapses to **70%** reliability.
*   A 10-step agent fails **more than half the time** (48% reliability).

This phenomenon is "Cascading Collapse," and **Phoenix was specifically engineered to prevent it.**

---

## Benchmark: Phoenix vs. Standard Parser

We conducted a benchmark against the `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` model. The test involved a "chaotic" prompt, intentionally designed to elicit messy, real-world LLM outputs, with the goal of extracting a JSON object.

| Parser                          | Reliability (Forgiving Schema) | Result                                                    |
| :------------------------------ | :----------------------------- | :-------------------------------------------------------- |
| **Standard Parser** (Regex + `json.loads`) | **93.33%**                     | Fails on approximately 7% of calls, introducing system instability. |
| **Phoenix Parser**              | **100.00%**                    | **Achieves total reliability**, completely preventing cascading collapse. |

Phoenix provides the robust foundation necessary for building reliable, multi-step AI systems.

---

## Key Features

*   **Resilient Cascade:** Implements a multi-layered defense system that intelligently finds, repairs, and validates JSON structures from ambiguous and messy text.
*   **Intelligent Repair:** Automatically corrects common LLM output errors, including truncated or incomplete JSON, extraneous comments, and non-standard quotation marks.
*   **Semantic Healing:** Leverages Pydantic to rectify semantic errors, such as type mismatches (e.g., transforming `"rating": "5/5"` into `rating: 5`).
*   **Semantic Fallback:** As a last resort, if no valid JSON is detected, Phoenix can reconstruct data from plain text by inferring its structure.

---

## Installation

```bash
pip install phoenix-parser
