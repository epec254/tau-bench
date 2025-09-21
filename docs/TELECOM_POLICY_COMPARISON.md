# Telecom Technical Support Policies: Manual vs Workflow

This note compares the two telecom technical support policies used by the domains `telecom` and `telecom-workflow`.

- Manual policy file: `data/tau2/domains/telecom/tech_support_manual.md`
- Workflow policy file: `data/tau2/domains/telecom/tech_support_workflow.md`

## High-Level Difference

- Manual (telecom): Narrative, reference-style guide with rich explanations. Designed to inform and let the agent decide the next best action.
- Workflow (telecom-workflow): Prescriptive, step-by-step runbook with explicit paths and numbered steps. Designed to constrain the agent to a specific troubleshooting flow.

## Structure and Tone

- Manual
  - Sections: “Understanding and Troubleshooting” for (1) Cellular Service, (2) Mobile Data, (3) MMS.
  - Includes “What the user can do on their device” with explicit function-like action names (e.g., `check_status_bar`, `toggle_data`).
  - Explanatory tone: describes why, when, and how to use tools; suggests referring to general policy.

- Workflow
  - Begins with an “Available User Actions Reference” written in plain language (e.g., “Check Network Status”, “Set Network Mode”), mapping to the same device capabilities/tools.
  - Core content is a decision tree with Paths (e.g., Path 1: No Service, Path 2.1: Mobile Data Unavailable, Path 2.2: Slow Data) and explicit Steps (e.g., Step 2.1.2: Verify if user is traveling, Step 2.1.4: Check Data Usage).
  - Instructional tone: tells the agent exactly which checks to perform and how to branch.

## Action Naming and Presentation

- Manual: Uses explicit tool/function identifiers in backticks (e.g., `check_network_status()`, `toggle_roaming()`), closely mirroring the API surface.
- Workflow: Uses human-readable action names (e.g., “Check Network Status”, “Toggle Data Roaming”), but they still correspond to the same underlying tools available in the environment.

## Troubleshooting Flow Differences (Examples)

- No Service / Connectivity
  - Manual: Explains concepts like airplane mode, SIM, signal strength, with guidance on which checks and fixes to try.
  - Workflow: Directs the agent through sequential checks and actions (e.g., verify service first before mobile data diagnostics; explicit branching if there is no service).

- Roaming
  - Manual: Advises verifying whether roaming is needed/enabled and whether the line is allowed to roam; references general policy.
  - Workflow: Explicit step (e.g., Step 2.1.2) to ask if the user is traveling → check/toggle data roaming → verify line roaming enablement, with follow-up speed tests and next steps.

- Mobile Data Unavailable vs Slow Data
  - Manual: Describes causes (data off, data saver, VPN, exceeded quota, network mode) and suggests tools to diagnose and fix.
  - Workflow: Splits into Path 2.1 (unavailable) and Path 2.2 (slow), with concretely ordered steps, mandatory re-tests (speed test), and escalation criteria.

- APN / MMSC for MMS
  - Manual: Details APN/MMSC importance; if missing, instructs `reset_apn_settings()` and then `reboot_device()` to apply.
  - Workflow: Embeds APN/MMS checks inside MMS troubleshooting steps (and other prerequisites) as part of the formal flow.

- Wi‑Fi Calling / VPN / Data Saver
  - Manual: Explains how these features can interfere and when to disable them.
  - Workflow: Integrates these checks into the step sequence where relevant.

## Coverage and Content Overlap

- Both policies cover similar problem spaces: cellular service, mobile data connectivity and speed, MMS prerequisites, APN, user device settings (airplane mode, data saver, VPN), network mode, roaming, and data plan limits.
- The workflow policy adds strong operational structure (Paths/Steps, retest checkpoints, escalation points). The manual adds more contextual explanations and rationale.

## Impact on Agent Behavior

- Manual policy (domain `telecom`)
  - Suited for agents with their own planning or ReAct-style strategies; encourages autonomous selection of next actions based on context.
  - The agent must translate narrative guidance into concrete tool calls.

- Workflow policy (domain `telecom-workflow`)
  - Suited for agents that benefit from explicit checklists and controlled branching; reduces ambiguity, enforces order of operations.
  - Easier to evaluate adherence: prompts reference numbered steps (“Step 2.1.2”, etc.).

## Practical Selection

- Prefer `telecom` when testing open-ended reasoning, adaptability, and the agent’s ability to synthesize from descriptive guidance.
- Prefer `telecom-workflow` when testing reliability in following a standard operating procedure and for clearer compliance evaluation.

## File References

- Manual: `data/tau2/domains/telecom/tech_support_manual.md`
- Workflow: `data/tau2/domains/telecom/tech_support_workflow.md`
- Environment selection of policy variants: `src/tau2/domains/telecom/environment.py`
- Policy path definitions: `src/tau2/domains/telecom/utils.py`
