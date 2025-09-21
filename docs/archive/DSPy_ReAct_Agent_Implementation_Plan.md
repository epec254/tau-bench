# DSPy ReAct Agent Implementation Plan for tau2-bench

## Overview

This plan outlines the implementation of a DSPy ReAct agent as a drop-in replacement for `src/tau2/agent/llm_agent.py`. The current implementation (`src/tau2/agent/dspy_react_agent.py`) exists but has critical issues that prevent it from working correctly with tau2-bench's tool calling and evaluation systems.

## Current Implementation Issues

After analyzing the existing `DSPyReActAgent`, several critical problems were identified:

1. **Broken Tool Integration**: The agent sets `tool_calls=None` assuming DSPy handles tools internally, but tau2-bench's orchestrator requires explicit `ToolCall` objects to execute tools.

2. **Incompatible Tool Conversion**: The current tool conversion doesn't properly bridge tau2's `Tool` system with DSPy's requirements, leading to execution failures.

3. **Missing ReAct Capabilities**: The implementation doesn't leverage DSPy's actual ReAct reasoning loop, instead treating it as a simple text generator.

4. **Evaluation System Incompatibility**: The agent doesn't produce the structured tool calls needed for tau2's action-based evaluation criteria.

## Implementation Strategy

### Phase 1: Core Architecture Redesign

#### 1.1 ReAct Integration Pattern
- **Custom DSPy Signature**: Create a specialized signature that captures tau2's conversation context and produces structured decisions
- **Tool Decision Logic**: Implement explicit reasoning about when to call tools vs. respond to user
- **Structured Output**: Ensure outputs can be parsed into tau2's `AssistantMessage` format with proper `ToolCall` objects

#### 1.2 Tool System Bridge
- **Tool Wrapper Strategy**: Convert tau2 `Tool` objects into DSPy-compatible functions while preserving execution context
- **Result Processing**: Handle tool execution results and format them for DSPy's reasoning loop
- **Error Handling**: Implement robust error recovery for tool execution failures

#### 1.3 State Management
- **ReAct History**: Track DSPy's internal reasoning trajectory alongside tau2's message history
- **Context Preservation**: Maintain conversation context across ReAct iterations
- **Memory Management**: Handle state updates for both DSPy and tau2 systems

### Phase 2: Implementation Details

#### 2.1 Custom DSPy Components

**ReActDecision Signature**:
```python
class ReActDecision(dspy.Signature):
    """Make a decision about the next action in customer service conversation."""
    
    conversation_context = dspy.InputField(desc="Current conversation history and context")
    domain_policy = dspy.InputField(desc="Domain-specific policy guidelines")
    available_tools = dspy.InputField(desc="List of available tools and their descriptions")
    
    reasoning = dspy.OutputField(desc="Step-by-step reasoning about the situation")
    action_type = dspy.OutputField(desc="Type of action to take: 'respond' or 'tool_call'")
    response_content = dspy.OutputField(desc="Direct response to user if action_type is 'respond'")
    tool_name = dspy.OutputField(desc="Name of tool to call if action_type is 'tool_call'")
    tool_arguments = dspy.OutputField(desc="JSON arguments for tool call if action_type is 'tool_call'")
```

**Custom ReAct Module**:
```python
class Tau2ReAct(dspy.Module):
    """Custom ReAct module designed for tau2-bench tool calling patterns."""
    
    def __init__(self, tools: List[Tool], max_iters: int = 5):
        super().__init__()
        self.tools = tools
        self.max_iters = max_iters
        self.decide = dspy.ChainOfThought(ReActDecision)
        self.tool_executor = ToolExecutor(tools)
    
    def forward(self, conversation_context, domain_policy):
        # Implement iterative reasoning loop
        # Decide between tool calling and responding
        # Execute tools when needed
        # Return final structured output
```

#### 2.2 Tool Execution Strategy

**Tool Call Generation**:
- Parse DSPy's structured output to create tau2 `ToolCall` objects
- Maintain tool call IDs for proper orchestrator interaction
- Handle multiple tool calls per turn when needed

**Integration Points**:
- Override `generate_next_message()` to use DSPy ReAct for decision making
- Convert DSPy outputs to tau2 `AssistantMessage` format
- Ensure proper tool call/response alternation

#### 2.3 Evaluation Compatibility

**Action Matching**:
- Generate tool calls that match evaluation criteria format
- Preserve argument structure for action comparison
- Maintain requestor attribution for proper scoring

**Communication Tracking**:
- Track information communicated to users
- Support multi-step conversations with tool usage
- Handle communicate_info evaluation criteria

### Phase 3: Implementation Plan

#### 3.1 File Structure
```
src/tau2/agent/
├── dspy_react_agent.py          # Main agent implementation (rewrite)
├── dspy_components.py           # DSPy signatures and modules (new)
└── dspy_tool_bridge.py         # Tool conversion utilities (new)
```

#### 3.2 Implementation Steps

**Step 1: Core ReAct Engine**
- [ ] Implement `Tau2ReAct` DSPy module with proper reasoning loop
- [ ] Create `ReActDecision` signature for structured decision making
- [ ] Build tool-aware reasoning prompts

**Step 2: Tool System Integration**
- [ ] Rewrite tool conversion to properly bridge tau2 and DSPy
- [ ] Implement tool result processing and error handling
- [ ] Add support for multi-tool calls per turn

**Step 3: Agent Class Redesign**
- [ ] Completely rewrite `DSPyReActAgent.generate_next_message()`
- [ ] Implement proper state management with DSPy integration
- [ ] Add comprehensive error handling and fallback mechanisms

**Step 4: Evaluation System Compatibility**
- [ ] Ensure tool calls match expected format for action evaluation
- [ ] Implement proper message formatting for communication tracking
- [ ] Add support for all reward types (DB, ACTION, COMMUNICATE)

**Step 5: Testing and Validation**
- [ ] Test with existing tau2 evaluation suite
- [ ] Validate tool call execution and result handling
- [ ] Verify evaluation criteria compatibility

#### 3.3 Key Implementation Challenges

**Tool Execution Timing**:
- DSPy ReAct expects synchronous tool execution within its loop
- tau2 expects tool calls to be returned to orchestrator for execution
- **Solution**: Mock tool execution within DSPy for reasoning, return actual tool calls to orchestrator

**State Synchronization**:
- DSPy maintains internal reasoning state
- tau2 maintains conversation message history
- **Solution**: Dual state management with synchronization points

**Error Recovery**:
- DSPy failures should not break tau2 conversation flow
- Tool execution errors need to be handled gracefully
- **Solution**: Multi-level fallback with LLM backup for critical failures

### Phase 4: Advanced Features

#### 4.1 Reasoning Transparency
- Log DSPy reasoning steps for debugging
- Expose thought process in development mode
- Support reasoning trace analysis

#### 4.2 Performance Optimization
- Cache tool descriptions and prompts
- Optimize ReAct iteration limits
- Implement early termination for simple queries

#### 4.3 Configuration Options
- Configurable ReAct parameters (max_iters, reasoning depth)
- Tool usage policies and constraints
- Fallback strategies for different failure modes

## Success Criteria

### Functional Requirements
1. **Drop-in Replacement**: Agent can be used wherever `LLMAgent` is used
2. **Tool Call Compatibility**: Generates proper `ToolCall` objects for orchestrator execution
3. **Evaluation Compatibility**: Works with all tau2 evaluation criteria types
4. **Error Resilience**: Handles failures gracefully without breaking conversation flow

### Performance Requirements
1. **Comparable Speed**: Performance within 2x of `LLMAgent` for typical tasks
2. **Memory Efficiency**: No excessive memory usage from DSPy state management
3. **Reasoning Quality**: Demonstrates improved reasoning over simple LLM calls

### Integration Requirements
1. **Registry Compatibility**: Properly registered and configurable via CLI
2. **Configuration Support**: Supports all LLM configuration options
3. **Logging Integration**: Proper integration with tau2's logging system

## Risk Mitigation

### Technical Risks
- **DSPy Version Compatibility**: Pin DSPy version and test thoroughly
- **LLM Provider Issues**: Implement robust error handling for API failures
- **Performance Degradation**: Monitor and optimize reasoning loop overhead

### Integration Risks
- **Breaking Changes**: Maintain backward compatibility with existing interfaces
- **Evaluation Incompatibility**: Extensive testing with all evaluation types
- **Registry Issues**: Careful testing of agent registration and instantiation

## Timeline

- **Week 1**: Core DSPy component implementation and tool bridge
- **Week 2**: Agent class redesign and basic functionality
- **Week 3**: Evaluation compatibility and comprehensive testing
- **Week 4**: Performance optimization and documentation

This plan provides a comprehensive approach to creating a production-ready DSPy ReAct agent that truly serves as a drop-in replacement for the existing LLM agent while leveraging DSPy's advanced reasoning capabilities.