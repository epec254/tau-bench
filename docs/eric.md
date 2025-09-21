


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