# Registry Guide: `register_domain` and `register_tasks`

This document explains what the `register_domain` and `register_tasks` functions do in the τ²-bench registry, and how they are used in `src/tau2/registry.py:173-199` to wire up the built-in domains and task sets.

## What is the Registry?

The registry (see `src/tau2/registry.py`) is a central mapping that stores constructors for:
- Users (`register_user`)
- Agents (`register_agent`)
- Domains (`register_domain`)
- Task sets (`register_tasks`)

A single global instance `registry` is created during import time and the defaults are registered immediately (lines 173–199). CLI commands and services query this registry to resolve names (e.g., `--domain airline`) to actual constructors.

## `register_domain`

- Location: `src/tau2/registry.py`
- Signature: `register_domain(get_environment: Callable[[], Environment], name: str)`
- Purpose: Register a function that constructs a domain `Environment` under a unique string key (`name`).
- Behavior:
  - Validates that `name` is not already registered; raises `ValueError` on duplicate.
  - Stores the mapping of `name -> get_environment` (a zero-argument callable that returns `Environment`).
  - Logs errors and re-raises if something goes wrong.
- Retrieval partner: `get_env_constructor(name)` returns the stored `get_environment` callable.

### Where it is used (173–199)
The following default domain constructors are registered:
- `registry.register_domain(mock_domain_get_environment, "mock")` — mock domain
- `registry.register_domain(airline_domain_get_environment, "airline")` — airline domain
- `registry.register_domain(retail_domain_get_environment, "retail")` — retail domain
- `registry.register_domain(telecom_domain_get_environment_manual_policy, "telecom")` — telecom domain (manual policy)
- `registry.register_domain(telecom_domain_get_environment_workflow_policy, "telecom-workflow")` — telecom domain (workflow policy variant)

These names (`mock`, `airline`, `retail`, `telecom`, `telecom-workflow`) are the values you pass to `--domain` in the CLI.

## `register_tasks`

- Location: `src/tau2/registry.py`
- Signature: `register_tasks(get_tasks: Callable[[], list[Task]], name: str)`
- Purpose: Register a function that loads a list of `Task` objects under a unique key (`name`). Usually one task set per domain name, but multiple sets can share a domain (e.g., `telecom_full`, `telecom_small`).
- Behavior:
  - Validates that `name` is not already registered; raises `ValueError` on duplicate.
  - Stores the mapping of `name -> get_tasks` (a zero-argument callable returning `list[Task]`).
  - Logs errors and re-raises on problems.
- Retrieval partner: `get_tasks_loader(name)` returns the stored `get_tasks` callable.

### Where it is used (173–199)
The following task loaders are registered:
- `registry.register_tasks(mock_domain_get_tasks, "mock")`
- `registry.register_tasks(airline_domain_get_tasks, "airline")`
- `registry.register_tasks(retail_domain_get_tasks, "retail")`
- `registry.register_tasks(telecom_domain_get_tasks_full, "telecom_full")` — telecom full task set
- `registry.register_tasks(telecom_domain_get_tasks_small, "telecom_small")` — telecom small task set
- `registry.register_tasks(telecom_domain_get_tasks, "telecom")` — default telecom set
- `registry.register_tasks(telecom_domain_get_tasks, "telecom-workflow")` — workflow variant uses the same tasks

These names are the values you pass to the `--task-ids` loader context or used internally by the runner to fetch tasks for a given domain selection.

## How The CLI Uses These Registrations

- The `tau2 run` flow (see `src/tau2/run.py`) resolves:
  - `environment_constructor = registry.get_env_constructor(domain)`
  - `task_loader = registry.get_tasks_loader(task_set_name)`
  - `AgentConstructor = registry.get_agent_constructor(agent)`
  - `UserConstructor = registry.get_user_constructor(user)`
- Then it constructs the `Environment`, loads `Task`s, and instantiates the selected Agent and User.

## Adding Your Own Domain and Tasks

1. Implement and export a zero-argument environment constructor that returns `Environment`:

```python
# your_package/environment.py
from tau2.environment.environment import Environment

def get_environment() -> Environment:
    # Build tools, policy, etc., and return Environment
    return Environment(domain_name="your_domain", policy="...", tools=..., user_tools=...)
```

2. Implement and export a zero-argument task loader that returns `list[Task]`:

```python
# your_package/environment.py (or tasks.py)
from tau2.data_model.tasks import Task

def get_tasks() -> list[Task]:
    # Construct and return task objects
    return [Task(...), ...]
```

3. Register both in `src/tau2/registry.py` alongside the defaults:

```python
from your_package.environment import get_environment as your_domain_get_environment
from your_package.environment import get_tasks as your_domain_get_tasks

registry.register_domain(your_domain_get_environment, "your_domain")
registry.register_tasks(your_domain_get_tasks, "your_domain")
```

Notes:
- Names must be unique across domains and task sets; duplicates raise `ValueError`.
- To retrieve later, use `get_env_constructor("your_domain")` and `get_tasks_loader("your_domain")`.

## Error Handling and Validation

- `register_domain` and `register_tasks` both:
  - Check for duplicate keys and raise `ValueError` when a name is already present.
  - Log errors via `loguru` and re-raise exceptions.
- `get_env_constructor`/`get_tasks_loader` raise `KeyError` if the name is not found.

## Related APIs

- `register_user` / `register_agent`: similar pattern for users and agents.
- `get_info()` aggregates all registered names; used by the API service and CLI to present options.

If you want, we can add your domain/task registration and verify it with `tau2 domain <your_domain>` and a small `tau2 run` locally.
