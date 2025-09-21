# Plan: DSPy ReAct Tool-Calling Agent for τ²-bench

Goal: Implement a DSPy-based ReAct agent that is a drop‑in replacement for `src/tau2/agent/llm_agent.py`, fully compatible with τ² tool-calling flow, evaluation, and registry. The agent must emit structured `tool_calls` (never execute tools internally), handle `ToolMessage`/`MultiToolMessage` observations, support emitting one or multiple tool calls per turn when appropriate, and integrate with metrics collection.

## Compatibility Targets

- Adhere to `LocalAgent` API (src/tau2/agent/base.py):
  - `get_init_state(message_history)` returns agent state.
  - `generate_next_message(message, state)` returns `(AssistantMessage, state)` with either `content` or `tool_calls`, not both.
- Tool flow per guides (TOOL_CALLING_GUIDE.md, src/tau2/agent/TOOL_CALLING.md):
  - Agent emits `AssistantMessage.tool_calls` → Orchestrator → Environment executes → returns `ToolMessage`/`MultiToolMessage` → fed back to Agent next turn.
- Evaluation compatibility (src/tau2/METRICS_AND_EVAL_CRITERIA.md):
  - ActionEvaluator matches expected tool calls and arguments from the trajectory. Therefore, the agent must not call tools internally.
  - Agent cost is optional; if available from DSPy LM, attach to `AssistantMessage.cost/usage`.
- Registry pluggable under a unique name (e.g., `dspy_react_tc`), similar CLI as other agents.

## Current Gap (Why a new agent)

- Existing `src/tau2/agent/dspy_react_agent.py` converts τ² tools to callable Python functions and lets DSPy execute them internally. This bypasses the orchestrator and prevents the benchmark from recording tool calls and tool results in the trajectory, breaking action-based evaluation and environment-side state updates.

## Design Overview

We build a “ReAct bridge” agent that uses DSPy for reasoning and tool selection but never executes environment tools directly. Instead, it:

1. On user input or tool results, formats a conversation context and prompts the LM (via DSPy) to emit a strict JSON decision.
2. Parse the LM’s decision:
   - If it proposes tool use, extract one or more `{name, arguments}` items and return an `AssistantMessage.tool_calls` list (requestor=`"assistant"`). If the model proposes multiple calls in one decision, emit them together in the same message.
   - If it proposes a final answer, return an `AssistantMessage.content`.
3. On the next turn, when `ToolMessage`/`MultiToolMessage` arrives, feed those observations back into the context before asking for the next step.

Primary mechanism: parsing-first (no validation). We steer the model with a strict, example-led schema to output exactly one of:
```
{"type": "tool_calls", "tool_calls": [{"name": string, "arguments": object}, ...]}
{"type": "final", "content": string}
```
We never mix tool_calls and final content in the same turn. We do not compact, coerce, or validate tool arguments — we emit exactly what the model proposes. If the output is unparseable, we fall back to a textual reply. Optional/secondary: If DSPy exposes a stable tool-intent hook in the future, we can adopt it; parsing remains the default.

## State and Turn Logic

- State model (Pydantic):
  - `system_messages: list[SystemMessage]` with a policy-composed ReAct instruction.
  - `messages: list[APICompatibleMessage]` (agent-visible history).
  - `pending_intent: Optional[ToolCall]` (set when DSPy plans a tool call; cleared after we emit it).
  - `react_module: dspy.ReAct` (configured with our proxy tools and LM).
- Turn handling:
  - If input is `UserMessage` or `ToolMessage`/`MultiToolMessage`, append to history.
  - Build a compact, role-tagged context string (system + conversation + last tool results) for DSPy.
  - Run a single decision step per τ² turn (we only emit one assistant message per turn). If DSPy proposes multiple actions in that decision, emit them together as `AssistantMessage(tool_calls=[...])`.
  - If DSPy produced tool invocation intent(s) → `AssistantMessage(tool_calls=[ToolCall(...), ...])`.
  - Else → `AssistantMessage(content=...)`.

## DSPy Integration Details

- LM configuration: prefer `dspy.LM(model=...)` (LiteLLM under the hood) and rely on provider env vars for keys. Examples:
  - OpenAI: `dspy.LM("openai/gpt-4o-mini")` with `OPENAI_API_KEY` set.
  - OpenRouter: `dspy.LM("openrouter/anthropic/claude-3.5-sonnet:beta")` with `OPENROUTER_API_KEY` set.
  Pass through `llm_args` (temperature, seed when provided). Do not hardcode API keys in code.
- ReAct prompting: provide a compact, role-tagged context and strict decision schema with examples. The LM returns either a `tool_calls` object (one or many calls) or a `final` object.
- Parsing-first path: parse the returned JSON and emit it as-is. Do not normalize or validate arguments; trust the model output.
- Optional future hook: if DSPy offers a stable tool-intent hook that surfaces `(name, args)` without executing, we can adopt it; not required for v1.
- Tool schema mapping: expose tool names, descriptions, and JSON parameter schemas from τ² `Tool` metadata to guide selection; do not enforce or validate against these at runtime.

## Tool-Call Emission and Observations

- Emit one or more tool calls per assistant message:
  - If the model returns multiple actions in a single decision, emit them together; the environment will execute each and return a `MultiToolMessage` next turn.
- On receiving `ToolMessage` or `MultiToolMessage` next turn:
  - Feed the observation content back verbatim as context (e.g., `Observation: <content>`) and let DSPy plan the next step. No compaction beyond minimal tagging.

## Cost and Usage (Metrics)

- If DSPy LM returns token usage/cost, set `AssistantMessage.cost` and `AssistantMessage.usage` per turn.
- If not available, leave unset; metrics pipeline tolerates missing cost (it reports avg cost over available data).

## Guardrails and Constraints

- Never execute environment tools inside the agent; all execution must go through the Environment via orchestrator.
- One τ² assistant message per turn; do not interleave tool execution and text in the same message.
- Allow multiple tool calls in one message when the DSPy ReAct decision returns them together; do not attempt to infer dependencies—trust the policy output and let the environment return observations next turn.
- Generate deterministic `ToolCall.id` values (e.g., per-turn counter or UUID4) and set `requestor="assistant"`.
- Do not validate or coerce tool calls; emit exactly what the model proposes.
- Include tool error signals in the observation text (e.g., `Observation(id=..., name=..., error=..., content=...)`) to inform subsequent reasoning.

## Error Handling

- If DSPy fails to produce a parseable tool intent or response, fall back to a helpful textual reply acknowledging error.
- If DSPy suggests a non-existent tool, reply to user explaining the limitation instead of emitting an invalid tool call.

## API and Registry

- New agent file: `src/tau2/agent/dspy_react_tc_agent.py` (tc = tool-calling bridge).
- Register in `src/tau2/registry.py` as `"dspy_react_tc"` without modifying existing agents.
- CLI usage example (same as others):
  ```bash
  tau2 run \
    --domain telecom \
    --agent dspy_react_tc \
    --agent-llm gpt-4.1 \
    --user-llm gpt-4.1 \
    --num-trials 1 \
    --num-tasks 5
  ```

## Implementation Steps

1. Add `dspy_react_tc_agent.py` implementing `LocalAgent` with the state and turn logic above.
2. Context builder: format system policy + compact conversation history + last tool observations, and include a strict JSON decision schema with examples.
3. Parsing layer:
   - Parse the model output into a decision object. If parsing fails, fall back to a textual reply.
4. Emission: return either `AssistantMessage(tool_calls=[...])` (one or multiple) or `AssistantMessage(content=...)`, never both.
5. Attach cost/usage if available from DSPy LM; otherwise leave unset.
6. Registry: register agent name `dspy_react_tc`.
7. Smoke test locally on a small task set to ensure trajectories contain alternating `AssistantMessage(tool_calls)` and `ToolMessage` as expected, and ActionEvaluator recognizes actions.

## Risks and Mitigations

- DSPy ReAct may eagerly execute functions: mitigate by using proxy tools that signal intent rather than executing.
- Argument formatting mismatches expected schemas: add lightweight JSON argument formatting and validation against τ² `Tool.params.model_json_schema()`; fallback to string-to-type casts where feasible.
- Multi-tool per turn vs ReAct’s stepwise dependence: if the ReAct decision yields multiple actions together, batch them; otherwise emit a single action and await observations next turn.

## Out-of-Scope (v1)

- Full token-cost integration from DSPy for billing parity with LiteLLM.
- Training/optimizing a DSPy program; we focus on inference-time ReAct.

## Definition of Done

- Agent compiles and runs, appears in registry as `dspy_react_tc`.
- Emits valid `AssistantMessage` with either `content` or `tool_calls` (single or multiple).
- Tool calls executed by Environment and returned as `ToolMessage`/`MultiToolMessage`.
- Evaluation runs without errors; ActionEvaluator can match actions.
- Basic smoke test across at least one domain (e.g., `telecom_small`).
