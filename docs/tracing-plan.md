**Title:** Tracing Plan for Separate Agent/User Spans

**Objective**
- Provide a minimal plan to instrument separate traces for the user simulator and the agent during a simulation run, without changing code right now.

**Call Flow Overview**
- Entry: `src/tau2/cli.py:main` wires `run` → `run_domain` via `RunConfig` (see `src/tau2/cli.py:88`).
- Batch runner: `src/tau2/run.py:run_domain`
  - Validates config, selects tasks, filters by agent type, computes `save_to`.
  - Delegates to `run_tasks`.
- Parallel execution: `src/tau2/run.py:run_tasks`
  - Seeds RNG; builds `Info`; handles resume/save.
  - Maps `(task, trial, seed)` to `_run` with `ThreadPoolExecutor`.
  - `_run` calls `run_task` and appends `SimulationRun`.
- Single simulation: `src/tau2/run.py:run_task`
  - Constructs `Environment`, `Agent`, `User` based on registry and agent type.
  - Creates `Orchestrator` and calls `orchestrator.run()`; then evaluates and returns the `SimulationRun`.
- Step orchestration: `src/tau2/orchestrator/orchestrator.py:Orchestrator.run`
  - Note: `@mlflow.trace` already decorates `run()`.
  - `initialize()` sets initial state and first message.
  - Loop calls `step()` until done; `get_trajectory()` returns ordered messages.
  - `SimulationRun` includes messages, costs, termination_reason.
- Step logic: `src/tau2/orchestrator/orchestrator.py:Orchestrator.step`
  - Branches by `from_role`/`to_role`:
    - User turn: calls `user.generate_next_message(...)`.
    - Agent turn: calls `agent.generate_next_message(...)`.
    - Env turn: executes tool calls via `environment.get_response(...)`.

**Where to Hook Traces**
- Keep `orchestrator.run()` as the parent span (already traced).
- Add two child spans per step:
  - Agent span around `agent.generate_next_message(...)` when `to_role == AGENT`.
  - User span around `user.generate_next_message(...)` when `to_role == USER`.
- Optional third child span for environment calls around `environment.get_response(...)` (tool invocations).

**Proposed Trace Structure**
- Span: `simulation` (existing) — `orchestrator.run()`
  - tags: `domain`, `task_id`, `trial`, `seed`, `agent_impl`, `agent_llm`, `user_impl`, `user_llm`, `solo_mode`
  - Span: `step_{i}_agent_generate`
    - tags: `role=agent`, `turn=i`, `is_tool_call`, `num_tool_calls`, `from_role`, `to_role`
  - Span: `step_{i}_user_generate`
    - tags: `role=user`, `turn=i`, `is_tool_call`, `num_tool_calls`, `from_role`, `to_role`
  - Span: `step_{i}_env_tool:{tool_name}` (per tool call)
    - tags: `tool_name`, `requestor` (`assistant`/`user`), `error`, `status`

**Minimal Implementation Steps**
1) Standard tags helper
   - Create a small helper to build a common tag dict from `domain`, `task`, `trial`, `seed`, `agent/user` config, and current `step_count`.

2) Instrument step transitions
   - In `Orchestrator.step`, wrap:
     - `user.generate_next_message(...)` with a `user` span.
     - `agent.generate_next_message(...)` with an `agent` span.
     - The loop over `environment.get_response(...)` with `env_tool` spans (one per tool call).

3) Include message-level metadata
   - After `*.generate_next_message(...)`, record tags like `is_tool_call`, `tool_count`, `content_length`, and any safety flags available.

4) Surface trial/seed
   - Ensure `trial` and `seed` are propagated to spans. `trial` is available in `run_tasks._run` when calling `run_task`; it becomes part of `SimulationRun` but can be attached to trace via orchestrator (e.g., pass via constructor or set as attribute before `run()`).

5) Concurrency safety
   - `ThreadPoolExecutor` runs multiple simulations; tracing contexts should be created inside `_run`/`run_task`/`orchestrator.run` to keep spans isolated per thread.

6) Validation pass
   - Run a small batch (1–2 tasks, 1 trial) and verify span tree: `simulation` → `step_*_user/agent` → `env_tool`.

**Notes and File Anchors**
- CLI handoff: `src/tau2/cli.py:88` (sets `func` to call `run_domain(RunConfig(...))`).
- Batch entry: `src/tau2/run.py:51` (`run_domain`).
- Batch execution: `src/tau2/run.py:97` (`run_tasks`).
- Single sim: `src/tau2/run.py:168` (`run_task`).
- Orchestrator parent span: `src/tau2/orchestrator/orchestrator.py:117` (`@mlflow.trace` on `run`).
- User turn: `src/tau2/orchestrator/orchestrator.py:184` (user `generate_next_message`).
- Agent turn: `src/tau2/orchestrator/orchestrator.py:199` (agent `generate_next_message`).
- Env/tool turn: `src/tau2/orchestrator/orchestrator.py:214` (`environment.get_response`).

**Outcome**
- Each step emits distinct user and agent spans under the per-simulation parent trace, enabling separate analysis of user simulator vs. agent behavior and costs.

