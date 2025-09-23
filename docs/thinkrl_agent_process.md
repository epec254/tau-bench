
## DONE MAUNALLY:

Run the sim

`tau2 run --domain telecom-workflow --agent-llm "openrouter/openai/gpt-5-nano" --user-llm "openrouter/openai/gpt-5" --max-concurrency 20`

tau2 run --domain telecom-workflow --agent-llm "openrouter/openai/gpt-5-nano" --user-llm "openrouter/openai/gpt-5" --max-concurrency 20 --save-to "data/simulations/2025-09-22T12:25:10.256274_telecom-workflow_llm_agent_gpt-5-nano_user_simulator_gpt-5.json"


## DONE MANUALLY:


CODE BASED CONTROL LOOP:
* Run judge for each trace that generates a pass/fail + root cause

Run this: `python src/thinkrl/utils/extract_simulations.py data/thinkrl/2025-09-21T19:10:46.051490_telecom_llm_agent_gpt-5-nano_user_simulator_gpt-5.json`

`python src/thinkrl/agentic_judge.py data/thinkrl/2025-09-22T12:25:10.256274_telecom-workflow_llm_agent_gpt-5-nano_user_simulator_gpt-5_rollouts_only.json --max-workers 10`


python src/thinkrl/agentic_judge.py data/thinkrl/2025-09-22T12:25:10.256274_telecom-workflow_llm_agent_gpt-5-nano_user_simulator_gpt-5.json --max-simulations 8

Run this: 

Outputs to the data model defined in `src/thinkrl/data_model/simulation_models.py` saved as a JSON: `data/thinkrl/2025-09-21T19:10:46.051490_telecom_llm_agent_gpt-5-nano_user_simulator_gpt-5_rollouts_only.json`


## IMPLEMENT THIS:

CODE BASED CONTROL LOOP: Sample 10 random wrong traces, pass to Agent 1

AGENT 1: 
    - aggregate the root causes from the judges to the data model
    - identify any other root causes based on insights across the 10 traces

Tools
- Get trace by ID
- Write root cause to hypothesis JSON
- Update existing hypothesis
- Look for existing hypothesis

outputs to src/thinkrl/data_model/hypothesis.py data model saves as a JSON

CODE-BASED CONTROL LOOP:
* Repeat until all traces are sampled, its ok if traces are sampled in multiple batches, but don't re-add the root causes from those

## STOP HERE for the future

AGENT 2:
* For each hypothesis, merge any other hypotheses that are the same, including the list of traces

CODE-BASED CONTROL LOOP:
* Repeat until each hypothesis is checked at least once

CODE-BASED CONTROL LOOP:
* List out the hypotheses and let the user pick one

AGNET 3: 
* Takes a root cause 
* Reads the traces, system prompt, policy, tools; generates 5 hypothesis for how to fix it
* Self-critiques and selects the most viable hypothesis (most likely to fix the root cause)

AGENT 4:
* Takes a root cause + hypothesis, generates a fix

CODE-BASED CONTROL LOOP:
* Re-runs the agent for those traces
* Re-runs the judge

AGENT 5:
* Reviews those traces
* Sees if the hypothesis was invalidated or validated
* Generates more hypothesis for the root cause if invalidated