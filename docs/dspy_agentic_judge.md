Create a DSPY module that is an LLM judge.

Inputs:
* One rollout

    Rollout example: data/simulations/2025-09-21T13:52:54.208346_telecom_llm_agent_gpt-5_user_simulator_gpt-5_rollouts_only.json

    ^^ you will just get ONE element of the simluations array on line 30.
* The policy

    You will get the policy key on line 25 of data/simulations/2025-09-21T13:52:54.208346_telecom_llm_agent_gpt-5_user_simulator_gpt-5_rollouts_only.json

Outputs
* PASS/FAIL
* Rationale

Starting prompt: docs/agentic_judge.md
