


## Goal
The goal is to see if I can prove this loop of:

I ran an agent for some task and then I ran some analysis of its trajectory.

I did that for another 10 examples.

I reviewed those trajectories and I developed a hypothesis.

I made some change based on that hypothesis.

I evaluated it again.

I repeated.

## Hypothesis

Iterative improvement of AI agents can be achieved using only qualitative, criteria-based evaluation (via LLM judge) without access to ground truth labels or deterministic benchmarks.

## Rough plan

1. Run simluations (manual)

tau2 run --domain telecom --agent-llm "openrouter/openai/gpt-5-nano" --user-llm "openrouter/openai/gpt-5" --max-concurrency 10

2. Run the agentic judge

3. 


* 
    * Tasks  
      * Judge program  
      * Stripped down data file with traces  
      * Data model  
    *   
    * Prompt  
      * Things you can do  
      * Data model for traces  
      * Data model for hypothesis   
        * Hypothesis   
        * Comments\[\]  
        * Fixes attempted  
          * What was done  
          * How to validate  
        * List of traces impacted  
          * ID  
          * notes\[\]  
    * Tools  
      * JQ for trace search  
      * manipulate hypothesis data model  
      * JQ for hypothesis data model  
    * Do it manually?  
      * Run judge for each  
      * Read 10 wrong and generate 5 hypothesis for how to fix, self critique to the one most likely to impact quality across all of them  
      * Read 10 more, repeat  
      *   
      * Determine how to determine if this hypothesis impacts   
      * runs and reads  
      * Generates hypothesis and what needs to be true to be validated   
      * Adjusts policy   
      * Run again  
      * Detmerine if the hypothesis was validated or not?  
      * Did it help the overall metric?



# How to run for a single example
tau2 run --domain telecom --agent-llm "openrouter/openai/gpt-5" --user-llm "openrouter/openai/gpt-5" --num-trials 1 --num-tasks 1


openai/gpt-5-nano

tau2 run --domain telecom --agent-llm "openrouter/openai/gpt-5-nano" --user-llm "openrouter/openai/gpt-5" --max-concurrency 10



# what

Create this data model as pydantic

* Data model for hypothesis   
* Hypothesis  str
* Comments str[]
* Fixes attempted  dict[] of
    * What was done  
    * How to validate  
* List of traces impacted  
    * ID  
    * task_id
    * notes str[]


Root cause
- description
- comments
- traces impacted
- hypothesiss []

what should be fixed
- changes to policy
- changes to system prompt
- changes to tool definitions

hypothesis
- root cause (one)
- description
- comments
- "what should be fixed"



  
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



* identify the 
* self-critique to the one most likely to impact quality across all of them by looking at all traces

* Repeat for next 10 traces until we get through all traces

* Take the 5 root causes with the most impacted traces
* Generate 5 hypothesis for each
* Self critique to the best ones by looking at traces that are impacted


* generate 
* Read 10 more, repeat  
*   
* Determine how to determine if this hypothesis impacts   
* runs and reads  
* Generates hypothesis and what needs to be true to be validated   
* Adjusts policy   
* Run again  
* Detmerine if the hypothesis was validated or not?  
* Did it help the overall metric?