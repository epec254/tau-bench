# Metrics and Evaluation Criteria in τ²-bench

This note explains how metrics are computed in `src/tau2/run.py:136–137` and how the benchmark uses task-defined evaluation criteria to grade simulations.

## Where metrics are computed

- In `run_domain` (see `src/tau2/run.py`), after running all tasks and trials, the code computes and displays agent-level metrics:
  - `metrics = compute_metrics(simulation_results)` (`src/tau2/run.py:136`)
  - `ConsoleDisplay.display_agent_metrics(metrics)` (`src/tau2/run.py:137`)
- `compute_metrics` lives in `src/tau2/metrics/agent_metrics.py` and consumes a `Results` object containing all simulations.

## What is in `Results`

- `Results` aggregates:
  - `info`: run configuration and environment info
  - `tasks`: the `Task` definitions used
  - `simulations`: one `SimulationRun` per task × trial
- Each `SimulationRun` already includes a `reward_info` computed immediately after the simulation via the evaluator.

## How rewards are computed (per simulation)

- After each simulation finishes in `run_task`, the framework calls the evaluator:

```python
reward_info = evaluate_simulation(
    domain=domain,
    task=task,
    simulation=simulation,
    evaluation_type=evaluation_type,
    solo_mode=solo_mode,
)
simulation.reward_info = reward_info
```

- The evaluator (`src/tau2/evaluator/evaluator.py`) looks at the task’s `evaluation_criteria` to decide which checks to run:
  - `RewardType.DB` / `RewardType.ENV_ASSERTION` → `EnvironmentEvaluator`
  - `RewardType.ACTION` → `ActionEvaluator`
  - `RewardType.COMMUNICATE` → `CommunicateEvaluator`
  - `RewardType.NL_ASSERTION` → `NLAssertionsEvaluator` (when `ALL_WITH_NL_ASSERTIONS`)
- For `EvaluationType.ALL`, the evaluator computes all relevant components, then multiplies their rewards together, restricted to the task’s `reward_basis`.

## How tasks define evaluation criteria

- Task schema: `src/tau2/data_model/tasks.py`
  - Each `Task` may include an `evaluation_criteria: EvaluationCriteria`.
  - `EvaluationCriteria` fields:
    - `actions: list[Action] | None` — expected tool calls (with `requestor`, `name`, `arguments`, optional `compare_args`). Used by `ActionEvaluator` to match actual tool calls.
    - `env_assertions: list[EnvAssertion] | None` — environment-level checks (`env_type`, `func_name`, `arguments`, `assert_value`). Used by `EnvironmentEvaluator`.
    - `communicate_info: list[str] | None` — info the agent should communicate to the user. Used by `CommunicateEvaluator`.
    - `nl_assertions: list[str] | None` — WIP natural-language assertions.
    - `reward_basis: list[RewardType]` — which components to include when combining rewards. Defaults to `[DB, COMMUNICATE]`.

- Where tasks come from:
  - The registry maps a task-set name to a zero-arg loader that returns `list[Task]`:

```python
# src/tau2/run.py
task_loader = registry.get_tasks_loader(task_set_name)
tasks = task_loader()
```

  - For example, the telecom domains register loaders for `telecom`, `telecom_small`, `telecom_full`.

## From rewards to metrics

- `compute_metrics(results)` converts the batch of `SimulationRun`s into aggregate metrics:
  - Average reward across runs.
  - pass^k metrics per k (1..K), averaged across tasks.
  - Average agent cost.
- Internally (`src/tau2/metrics/agent_metrics.py`):
  - Builds a DataFrame from `Results` (via `Results.to_df()`), adds a boolean `success = (reward ≈ 1.0)`.
  - Computes pass^k per task (probability at least one success in k trials), then averages across tasks.

## Putting it together

1. Registry provides task definitions (`Task` objects) via `get_tasks_loader(name)`.
2. Each task’s `evaluation_criteria` instructs evaluators what to check and how to combine sub-scores (`reward_basis`).
3. `run_task` executes simulation, then `evaluate_simulation` returns a `RewardInfo` (with breakdowns) which is attached to the `SimulationRun`.
4. `run_domain` aggregates all runs into `Results` and calls `compute_metrics` to produce high-level metrics, then displays them.

## Practical implications for authors

- To change how a task is graded, edit its `evaluation_criteria`:
  - Add expected `actions` to validate tool usage and arguments.
  - Add `env_assertions` to validate environment state changes (DB or function outcomes).
  - Adjust `reward_basis` to include or exclude certain dimensions (e.g., `ACTION`, `COMMUNICATE`).
- To change aggregate metrics, update `metrics/agent_metrics.py` or consume `Results` differently.

## References

- Metrics: `src/tau2/metrics/agent_metrics.py`
- Evaluator: `src/tau2/evaluator/evaluator.py`
- Task and evaluation schema: `src/tau2/data_model/tasks.py`
- Task loading and metrics call site: `src/tau2/run.py`
