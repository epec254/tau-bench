
  
* Run judge for each trace that generates a pass/fail + root cause

AGENT 1: 
* Sample 10 random wrong traces 
    - aggregate the root causes from the judges to the data model
    - identify any other root causes based on insights across the 10 traces

CODE-BASED CONTROL LOOP:
* Repeat until all traces are sampled, its ok if traces are sampled in multiple batches, but don't re-add the root causes from those

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