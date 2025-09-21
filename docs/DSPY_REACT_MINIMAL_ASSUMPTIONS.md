# DSPy ReAct (Minimal) — Assumptions and Test Plan

This note captures the specific assumptions we want to validate with a minimal ReAct loop running outside τ², using LiteLLM with the OpenRouter provider. The goal is to confirm behaviors needed by the tau2 DSPy ReAct bridge agent (without importing any tau2 code).

## Assumptions to Validate

- ReAct formatting:
  - The model can reliably emit either a Final Answer or Action(s) when prompted with a clear schema and examples.
  - Actions are emitted as JSON-like `{name, arguments}` pairs; a single turn may include one or multiple actions, and never mix with Final Answer content.
- Intent capture (no execution):
  - The agent can parse out intended tool calls (name + JSON args) from the model output without executing anything.
  - Invalid or unknown tools are handled gracefully (no emission of invalid calls; fall back to a textual explanation).
- Argument normalization:
  - Near-JSON is common (e.g., single quotes, trailing commas). The agent can coerce/normalize or otherwise reject with a clear error marker.
- Observations loop:
  - Supplying a prior observation in the context reliably shifts the model’s next decision (e.g., choose a different tool or produce a final answer).
- Multi-action per turn:
  - If the model emits multiple actions in one decision, we can batch them into a single assistant turn.
  - If the model rarely emits multiple actions, falling back to single-action turns still yields a usable policy.
- Determinism and traceability:
  - Each emitted tool call is assigned a deterministic ID (per run) and is validated against a provided tool schema (name + parameters).
  - The script prints a compact JSON decision object per turn for easy inspection.

## Minimal Validation Script

- Location: `scripts/min_dspy_react_openrouter.py`
- Tech:
  - LiteLLM (OpenRouter provider) for LM calls.
  - Python-only, no τ² imports. `python-dotenv` to load `OPENROUTER_API_KEY` from `.env`.
- Inputs:
  - `--question` (user input)
  - `--observation` (optional prior tool result to test step-wise ReAct)
  - `--tools-json` (optional path to a JSON list of tool specs). Default: a tiny built-in toolset.
- Output (stdout): single JSON doc per run:
  - `{"decision_type": "tool_calls"|"final", "tool_calls": [...], "content": "...", "raw": "...", "errors": [...]}`

## Test Plan

1. Intent capture (single action)
   - Prompt encourages `Action: add {"a": 2, "b": 3}`.
   - Validate `decision_type == tool_calls` and a well-formed call.
2. Unknown tool
   - Ask for something outside listed tools; expect `final` decision or a graceful explanation, but no tool_calls.
3. Near-JSON arguments
   - Provide examples encouraging single quotes or trailing commas; validate normalization or explicit error.
4. Observations steering
   - Provide an observation via `--observation` and confirm model’s next decision changes accordingly.
5. Multi-action
   - Prompt with a scenario that nudges multiple actions; verify agent batches them if emitted.

This suffices to validate the core design constraints for the ReAct bridge agent.

