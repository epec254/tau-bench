# tau2-bench Registry Functions Guide

This document explains what `register_domain` and `register_tasks` functions do in the tau2-bench registry system, and how they enable the framework's modular domain architecture.

## Table of Contents
1. [Registry Overview](#registry-overview)
2. [register_domain Function](#register_domain-function)
3. [register_tasks Function](#register_tasks-function)
4. [Domain Structure](#domain-structure)
5. [Task Structure](#task-structure)
6. [Registration Examples](#registration-examples)
7. [Creating New Domains](#creating-new-domains)

## Registry Overview

The tau2-bench registry (`src/tau2/registry.py`) serves as a central component catalog that maps string identifiers to constructor functions. It maintains four main registries:

```python
class Registry:
    def __init__(self):
        self._users: Dict[str, Type[BaseUser]] = {}
        self._agents: Dict[str, Type[BaseAgent]] = {}
        self._domains: Dict[str, Callable[[], Environment]] = {}  # ← Domain constructors
        self._tasks: Dict[str, Callable[[], list[Task]]] = {}     # ← Task loaders
```

This design enables:
- **Dynamic domain loading** based on CLI arguments
- **Modular architecture** where domains are self-contained
- **Easy extensibility** for adding new business domains
- **Separation of concerns** between domain logic and framework

## register_domain Function

### Function Signature
```python
def register_domain(
    self,
    get_environment: Callable[[], Environment],
    name: str,
):
```

### What It Does

`register_domain` maps a domain name (string) to a factory function that creates `Environment` objects for that domain.

#### Parameters:
- **`get_environment`**: A callable that returns an `Environment` instance
- **`name`**: String identifier for the domain (e.g., "airline", "mock", "retail")

#### Process:
1. **Validates uniqueness**: Checks if domain name is already registered
2. **Stores mapping**: Associates the name with the constructor function
3. **Error handling**: Logs and re-raises any registration errors

### Domain Constructor Pattern

Each domain implements a `get_environment()` function following this pattern:

```python
def get_environment(
    db: Optional[DomainDB] = None,
    solo_mode: bool = False,
) -> Environment:
    # Load domain database
    if db is None:
        db = DomainDB.load(DOMAIN_DB_PATH)
    
    # Create domain-specific tools
    tools = DomainTools(db)
    
    # Load domain policy
    with open(DOMAIN_POLICY_PATH, "r") as fp:
        policy = fp.read()
    
    # Create and return Environment
    return Environment(
        domain_name="domain_name",
        policy=policy,
        tools=tools,
        user_tools=user_tools_if_applicable,  # Optional
    )
```

### Environment Object Structure

The returned `Environment` contains:

```python
class Environment:
    domain_name: str           # Domain identifier
    policy: str               # Text-based policy rules
    tools: ToolKitBase        # Assistant tools
    user_tools: Optional[ToolKitBase] = None  # User tools (telecom only)
```

**Key Components:**
- **Domain Name**: Identifies the business domain
- **Policy**: Text rules that agents must follow (loaded from policy files)
- **Tools**: Domain-specific functions available to assistants
- **User Tools**: Optional tools available to users (currently only telecom)

### Example Registration

```python
# In registry initialization
from tau2.domains.airline.environment import get_environment as airline_get_environment

registry.register_domain(airline_get_environment, "airline")
```

This allows the framework to later retrieve the airline environment with:
```python
env_constructor = registry.get_env_constructor("airline")
environment = env_constructor()
```

## register_tasks Function

### Function Signature
```python
def register_tasks(
    self,
    get_tasks: Callable[[], list[Task]],
    name: str,
):
```

### What It Does

`register_tasks` maps a task set name to a loader function that returns a list of `Task` objects for evaluation scenarios.

#### Parameters:
- **`get_tasks`**: A callable that returns a list of `Task` instances
- **`name`**: String identifier for the task set (e.g., "airline", "telecom_full", "mock")

#### Process:
1. **Validates uniqueness**: Checks if task set name is already registered
2. **Stores mapping**: Associates the name with the task loader function
3. **Error handling**: Logs and re-raises any registration errors

### Task Loader Pattern

Each domain implements `get_tasks()` functions following this pattern:

```python
def get_tasks() -> list[Task]:
    # Load tasks from JSON file
    with open(DOMAIN_TASK_SET_PATH, "r") as fp:
        tasks_data = json.load(fp)
    
    # Validate and convert to Task objects
    return [Task.model_validate(task) for task in tasks_data]
```

### Task Object Structure

Each `Task` is a comprehensive Pydantic model:

```python
class Task(BaseModel):
    id: str                                    # Unique identifier
    description: Optional[Description]         # Purpose, policies, notes
    user_scenario: UserScenario               # User simulator instructions
    ticket: Optional[str]                     # Solo mode description
    initial_state: Optional[InitialState]    # Environment setup
    evaluation_criteria: Optional[EvaluationCriteria]  # Success metrics
```

**Key Sub-Components:**

#### Description
```python
class Description(BaseModel):
    purpose: str                    # What the task tests
    relevant_policies: list[str]    # Applicable policy sections
    notes: Optional[str]           # Additional context
```

#### UserScenario
```python
class UserScenario(BaseModel):
    persona: str        # User's role and background
    instructions: str   # What the user should do
```

#### EvaluationCriteria
```python
class EvaluationCriteria(BaseModel):
    actions: Optional[list[Action]]              # Expected tool calls
    nl_assertions: Optional[list[NLAssertion]]   # Natural language checks
    reward_basis: Optional[RewardBasis]          # Scoring methodology
```

#### InitialState
```python
class InitialState(BaseModel):
    initialization_data: Optional[dict]         # Database setup
    initialization_actions: Optional[list[Action]]  # Pre-actions
    message_history: Optional[list[Message]]    # Conversation context
```

### Task Set Variations

Different domains have different task set strategies:

- **airline**: Single task set (`get_tasks()`)
- **mock**: Single task set (`get_tasks()`)
- **retail**: Single task set (`get_tasks()`)
- **telecom**: Multiple task sets:
  - `get_tasks()` - Standard set
  - `get_tasks_full()` - Complete test suite
  - `get_tasks_small()` - Subset for quick testing

### Example Registration

```python
# In registry initialization
from tau2.domains.airline.environment import get_tasks as airline_get_tasks

registry.register_tasks(airline_get_tasks, "airline")
```

This allows the framework to later load airline tasks with:
```python
task_loader = registry.get_tasks_loader("airline")
tasks = task_loader()
```

## Domain Structure

### Required Files

Each domain must implement:

```
src/tau2/domains/domain_name/
├── __init__.py
├── data_model.py        # Database schema and models
├── environment.py       # get_environment() and get_tasks() functions
├── tools.py            # Assistant tools implementation
├── user_tools.py       # User tools (optional, telecom only)
└── utils.py            # Domain-specific utilities
```

### Data Directory

Each domain has corresponding data:

```
data/tau2/domains/domain_name/
├── db.json             # Domain database
├── policy.txt          # Domain policy rules
├── tasks.json          # Task definitions
└── task_sets/          # Multiple task sets (telecom only)
    ├── full.json
    └── small.json
```

## Registration Examples

### Current Registry Initialization

From `src/tau2/registry.py` lines 173-199:

```python
try:
    registry = Registry()
    logger.debug("Registering default components...")
    
    # User simulators
    registry.register_user(UserSimulator, "user_simulator")
    registry.register_user(DummyUser, "dummy_user")
    
    # Agents
    registry.register_agent(LLMAgent, "llm_agent")
    registry.register_agent(LLMGTAgent, "llm_agent_gt")
    registry.register_agent(LLMSoloAgent, "llm_agent_solo")
    registry.register_agent(DSPyReActAgent, "dspy_react")
    
    # Domains and their tasks
    registry.register_domain(mock_domain_get_environment, "mock")
    registry.register_tasks(mock_domain_get_tasks, "mock")
    
    registry.register_domain(airline_domain_get_environment, "airline")
    registry.register_tasks(airline_domain_get_tasks, "airline")
    
    registry.register_domain(retail_domain_get_environment, "retail")
    registry.register_tasks(retail_domain_get_tasks, "retail")
    
    # Telecom with multiple configurations
    registry.register_domain(telecom_domain_get_environment_manual_policy, "telecom")
    registry.register_domain(telecom_domain_get_environment_workflow_policy, "telecom-workflow")
    
    # Telecom task sets
    registry.register_tasks(telecom_domain_get_tasks_full, "telecom_full")
    registry.register_tasks(telecom_domain_get_tasks_small, "telecom_small")
    registry.register_tasks(telecom_domain_get_tasks, "telecom")
    registry.register_tasks(telecom_domain_get_tasks, "telecom-workflow")
    
except Exception as e:
    logger.error(f"Error initializing registry: {str(e)}")
```

### Domain-Task Relationships

| Domain | Task Sets | Description |
|--------|-----------|-------------|
| `"mock"` | `"mock"` | Simple testing domain |
| `"airline"` | `"airline"` | Flight booking and management |
| `"retail"` | `"retail"` | E-commerce and inventory |
| `"telecom"` | `"telecom"`, `"telecom_full"`, `"telecom_small"` | Telecommunications with multiple test sets |
| `"telecom-workflow"` | `"telecom-workflow"` | Telecom with workflow-based policy |

## Creating New Domains

### Step 1: Implement Domain Structure

Create the required files:

```python
# src/tau2/domains/my_domain/environment.py
def get_environment(db: Optional[MyDB] = None, solo_mode: bool = False) -> Environment:
    if db is None:
        db = MyDB.load(MY_DOMAIN_DB_PATH)
    tools = MyDomainTools(db)
    
    with open(MY_DOMAIN_POLICY_PATH, "r") as fp:
        policy = fp.read()
    
    return Environment(
        domain_name="my_domain",
        policy=policy,
        tools=tools,
    )

def get_tasks() -> list[Task]:
    with open(MY_DOMAIN_TASK_SET_PATH, "r") as fp:
        tasks = json.load(fp)
    return [Task.model_validate(task) for task in tasks]
```

### Step 2: Register Domain

```python
# In src/tau2/registry.py
from tau2.domains.my_domain.environment import (
    get_environment as my_domain_get_environment,
    get_tasks as my_domain_get_tasks
)

# Add to registry initialization
registry.register_domain(my_domain_get_environment, "my_domain")
registry.register_tasks(my_domain_get_tasks, "my_domain")
```

### Step 3: Use Your Domain

```bash
tau2 run --domain my_domain --agent llm_agent --agent-llm gpt-4 --user-llm gpt-4
```

## Key Benefits

### 1. Modularity
- Each domain is self-contained
- Easy to add/remove domains
- No cross-domain dependencies

### 2. Flexibility
- Multiple task sets per domain
- Different policy formats
- Optional user tools

### 3. Consistency
- Standardized interfaces
- Common evaluation framework
- Unified CLI access

### 4. Extensibility
- Simple registration process
- Clear implementation patterns
- Comprehensive validation

The registry functions provide the foundation for tau2-bench's modular architecture, enabling researchers to easily create new business domains while maintaining compatibility with the evaluation framework.