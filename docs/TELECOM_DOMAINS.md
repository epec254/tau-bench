# Telecom vs Telecom-Workflow Domains

This note clarifies how the `telecom` and `telecom-workflow` domains differ and when to use each.

## Summary

- Both domains share the same tools and tasks; the difference lies in the policy content provided to the agent (and the derived domain name). 
- `telecom`: uses the manual (free-form) tech support policy.
- `telecom-workflow`: uses the workflow-structured tech support policy.

## What Changes Between Them

1. Policy Source
   - In `src/tau2/domains/telecom/environment.py`, the environment builder selects a tech support policy based on `policy_type`:
     - Manual policy: `TELECOM_TECH_SUPPORT_POLICY_MANUAL_PATH` (and `_SOLO_PATH` for solo mode)
     - Workflow policy: `TELECOM_TECH_SUPPORT_POLICY_WORKFLOW_PATH` (and `_SOLO_PATH` for solo mode)
   - The main policy (`TELECOM_MAIN_POLICY_PATH` or solo variant) is included in both cases.
   - The final policy is a concatenation of `<main_policy>` and `<tech_support_policy>` blocks.

2. Domain Name
   - If `policy_type == "manual"` → domain name is `"telecom"`.
   - If `policy_type == "workflow"` → domain name is `"telecom-workflow"`.

3. Registration
   - `registry.register_domain(get_environment_manual_policy, "telecom")`
   - `registry.register_domain(get_environment_workflow_policy, "telecom-workflow")`
   - Both variants register the same task loader(s): `telecom`, `telecom_full`, `telecom_small`, and `telecom-workflow` (workflow variant reuses `telecom` tasks).

4. Tools & Data
   - Tools: identical (`TelecomTools` and `TelecomUserTools`).
   - DBs: identical (`TelecomDB`, `TelecomUserDB`).
   - Sync behavior in `TelecomEnvironment.sync_tools()` is identical in both domains.

## Practical Impact

- `telecom` (manual policy):
  - Best when evaluating agents that rely on free-form procedural text or have their own internal planning.
  - Allows the agent to decide steps without a rigid workflow.

- `telecom-workflow` (workflow policy):
  - Provides a more structured, step-by-step policy. Prompts can reference explicit “Step X.Y” guidance.
  - Good for testing agents that follow checklists or are sensitive to explicit workflows.

## Solo Mode

- Both domains support a solo mode (used by `LLMSoloAgent`), swapping in the solo versions of the main and workflow/manual tech support policies.
- The environment factory toggles this when constructed with `solo_mode=True`.

## How to Select

- CLI examples (`README.md`):

```bash
# Manual policy
tau2 run \
  --domain telecom \
  --agent-llm gpt-4.1 \
  --user-llm gpt-4.1

# Workflow policy
tau2 run \
  --domain telecom-workflow \
  --agent-llm gpt-4.1 \
  --user-llm gpt-4.1
```

## References

- Environment builder and policy selection: `src/tau2/domains/telecom/environment.py`
- Policy paths and task sets: `src/tau2/domains/telecom/utils.py`
- Registry wiring: `src/tau2/registry.py`
- Tasks that reference workflow steps (comments): `src/tau2/domains/telecom/tasks/*`
