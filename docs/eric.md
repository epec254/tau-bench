


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


# Other info 

Tools - self.tools which are in OpenAI format
Domain policy - self.domain_policy prompt with instructions on how to respond to queries - contains all the domain knowledge 

Challenges
* The messages are all custom and defined in src/tau2/data_model/message.py - must translate to the format you expect


messages on line 16404 shows you the example 
