# Tool Calling in τ²-bench

This guide explains how tool calling works in τ²-bench and how to implement your own agent that uses tools.

## Concepts Overview

- Tools are Python functions wrapped as `Tool` objects with OpenAI-style function schemas. LLMs can call these tools by returning a structured `tool_calls` payload.
- The orchestrator runs a conversation loop between Agent, User, and Environment. When an Agent (or User) returns tool calls, the Environment executes them and returns `ToolMessage` responses that are fed back to the caller.
- Each domain provides a policy and a set of tools. The registry wires together domains, agents, and users.

## Where to Look in the Codebase

- Tool wrapper: `src/tau2/environment/tool.py`
  - `Tool` schema exposed via `openai_schema`
  - Tools are auto-built from function signatures + docstrings using Pydantic
- LLM integration: `src/tau2/utils/llm_utils.py`
  - Converts τ² messages ↔ LiteLLM format, passes `tools` to the model, parses `tool_calls`
- Message data model: `src/tau2/data_model/message.py`
  - `AssistantMessage`, `UserMessage`: either text `content` or `tool_calls` (mutually exclusive)
  - `ToolCall` structure (`id`, `name`, `arguments`, `requestor`)
  - `ToolMessage` (tool responses), and `MultiToolMessage` (batch responses)
- Environment execution: `src/tau2/environment/environment.py`
  - Executes tool calls and returns `ToolMessage` via `get_response`
- Orchestrator loop: `src/tau2/orchestrator/orchestrator.py`
  - Routes messages among Agent/User/Environment; handles multi-tool calls per turn
- Built-in LLM agents: `src/tau2/agent/llm_agent.py`
  - `LLMAgent` (standard), `LLMGTAgent` (oracle plan), `LLMSoloAgent` (no user turns; must stop via a special tool)
- Agent base: `src/tau2/agent/base.py`
  - `LocalAgent` API you implement: `get_init_state` and `generate_next_message`
- Registry: `src/tau2/registry.py`
  - Register your agent via `registry.register_agent(MyAgent, "my_agent")`

## Tool Calling Flow

1. The agent builds the next message. It may be:
   - Text to the user (`AssistantMessage` with `content`), or
   - One or more tool calls (`AssistantMessage` with `tool_calls`)
2. If the message contains tool calls, the orchestrator sends them to the Environment.
3. The Environment runs each tool (`make_tool_call`), wraps results into `ToolMessage`(s), and returns them.
4. The orchestrator appends the tool result messages to the trajectory and delivers them back to the original caller (Agent or User) for the next turn.
5. The agent processes `ToolMessage` or `MultiToolMessage` inputs and produces the next `AssistantMessage`.

Notes:
- Messages must be either text or tool calls, not both (validation enforced).
- Multiple tool calls in a single turn are supported; responses may be wrapped as a `MultiToolMessage`.

## Messages and Types

- `AssistantMessage` / `UserMessage`
  - Either `content` (text) or `tool_calls` (structured calls).
- `ToolCall`
  - `{ id: str, name: str, arguments: dict, requestor: Literal['assistant'|'user'] }`
- `ToolMessage`
  - Response payload from a tool call; includes `error` flag and matching `id`.
- `MultiToolMessage`
  - Wrapper for multiple `ToolMessage` responses when multiple tools were called in one turn.

## Where tools come from

- Each domain’s `Environment` provides agent tools and optionally user tools.
  - Agent tools: `Environment.get_tools()`
  - User tools: `Environment.get_user_tools()`
- The orchestrator instantiates the environment for the selected domain and passes its tools to the agent constructor.

## Built-in LLM Agent Behavior

- `LLMAgent` composes a system prompt including the domain policy, and calls the configured LLM via LiteLLM with the tool schemas.
- The LLM can return either text content or tool calls. Parsed tool calls are placed into `AssistantMessage.tool_calls` for the orchestrator to execute.
- `LLMGTAgent` receives an oracle plan (ground truth steps) to bias/guide action selection.
- `LLMSoloAgent` operates without user messages; it must stop by calling a special `done` tool that the agent injects.

## Implement Your Own Agent

Implement a subclass of `LocalAgent` with two methods:

- `get_init_state(message_history) -> AgentState`
  - Create your initial agent state. You’ll receive prior valid agent-side history if a task specifies it.
- `generate_next_message(message, state) -> (AssistantMessage, AgentState)`
  - Called with either a `UserMessage`, `ToolMessage`, or `MultiToolMessage` (or `None` for the first solo turn). Return the next `AssistantMessage`:
    - Text response, or
    - One or more `ToolCall`s.

Constraints:
- Do not mix content and tool calls in one `AssistantMessage`.
- If you emit multiple tool calls, expect multiple `ToolMessage` responses next turn.

### Minimal Agent Skeleton

```python
# src/tau2/agent/my_agent.py
from pydantic import BaseModel
from tau2.agent.base import LocalAgent, ValidAgentInputMessage
from tau2.data_model.message import (
    AssistantMessage, UserMessage, ToolMessage, MultiToolMessage, ToolCall,
)

class MyState(BaseModel):
    saw_tool_result: bool = False

class MyAgent(LocalAgent[MyState]):
    def get_init_state(self, message_history=None) -> MyState:
        return MyState()

    def generate_next_message(self, message: ValidAgentInputMessage, state: MyState):
        # If we just got tool result(s), continue with a text update
        if isinstance(message, (ToolMessage, MultiToolMessage)):
            state.saw_tool_result = True
            return (
                AssistantMessage(role="assistant", content="Got it, here’s the update."),
                state,
            )

        # On first user input, call a tool
        if isinstance(message, UserMessage) and not state.saw_tool_result:
            tc = ToolCall(id="call-1", name="some_tool_name", arguments={"arg": "value"})
            return (
                AssistantMessage(role="assistant", tool_calls=[tc]),
                state,
            )

        # Default
        return (
            AssistantMessage(role="assistant", content="How else can I help?"),
            state,
        )
```

### Register Your Agent

Add your registration in `src/tau2/registry.py` alongside the other defaults:

```python
from tau2.agent.my_agent import MyAgent
registry.register_agent(MyAgent, "my_agent")
```

### Run With Your Agent

```bash
# Use any supported domain; pick your LLMs via LiteLLM names
tau2 run \
  --domain airline \
  --agent my_agent \
  --agent-llm gpt-4.1 \
  --user-llm gpt-4.1 \
  --num-trials 1 \
  --num-tasks 5
```

## Defining Tools (Optional quick refresher)

Wrap Python functions into tools using `as_tool`:

```python
from tau2.environment.tool import as_tool

# Example function to wrap
# docstring + type hints feed the tool signature

def lookup_booking(booking_id: str) -> dict:
    """Fetch booking details by ID."""
    ...

tools = [as_tool(lookup_booking)]
```

Domains expose these tools through their `Environment`; your agent receives them via the orchestrator.

## Inspecting Domain Tools and Policy

- Launch the domain API docs to see available tools and policy:

```bash
tau2 domain <domain>
# Visit http://127.0.0.1:8004/redoc
```

- Try the beta Environment CLI for quick manual tool testing:

```bash
make env-cli
```

## Key Gotchas

- An assistant or user message cannot have both `content` and `tool_calls`.
- If you send N tool calls, expect exactly N `ToolMessage` responses; the orchestrator enforces matching.
- `LLMSoloAgent` must stop by calling its injected `done` tool (name `done`, content token `###STOP###`).

---

If you want, we can scaffold `MyAgent` in `src/tau2/agent/my_agent.py` and add the registry entry for you.
