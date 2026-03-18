# Chapter 11: Security, Guardrails, and Sandboxed Execution

Security in the era of Generative AI has fundamentally shifted. When building predictive ML models, the primary security concerns were data poisoning and model inversion. However, when building Agentic systems—which can execute code, query databases, and interact with APIs autonomously—the threat surface expands exponentially. This chapter delves into securing LangGraph agents for enterprise deployment.

## The New Threat Landscape

Agents are not just passive data processors; they are active system participants. This introduces two major threat vectors unique to LLM-driven applications:

### 1. Prompt Injection and Jailbreaking
Unlike traditional SQL injection where payloads are rigid, prompt injections are fluid and contextual. An attacker can append instructions to a seemingly benign input, tricking the LLM into executing unintended actions. In a multi-agent system, an injected prompt might be passed from a low-privilege node to a high-privilege node, resulting in a **Privilege Escalation** attack.

### 2. Malicious Code Execution
Agents frequently use tools like Python REPLs or bash shells to perform data analysis or system interactions. If an attacker tricks the agent into running malicious code, the host environment can be compromised.

## Implementing Guardrails

To mitigate these risks, we cannot rely solely on the LLM's internal alignment. We need deterministic guardrails.

### NeMo Guardrails Integration
Nvidia's NeMo Guardrails provides a programmatic way to enforce semantic checks on inputs and outputs. Within LangGraph, NeMo Guardrails can be integrated as a pre-processing and post-processing node.

```python
from nemoguardrails import RailsConfig, LLMRails
from langchain_core.runnables import RunnableLambda

config = RailsConfig.from_path("./config/guardrails")
rails = LLMRails(config)

def guardrail_node(state: dict):
    user_input = state["messages"][-1].content
    # Apply guardrails
    safe_response = rails.generate(messages=[{"role": "user", "content": user_input}])
    
    # If the response was blocked by the guardrail, return the canned refusal
    if "I cannot answer that" in safe_response:
        return {"messages": [AIMessage(content=safe_response)], "status": "blocked"}
    
    return {"status": "safe"}
```

## Sandboxing Tool Execution

When providing agents with tools capable of code execution, you must assume the LLM will eventually generate harmful code—either by hallucination or via adversarial injection.

### The Docker-in-Docker Approach
Never run an agent's Python REPL tool directly on your host or main application container. Instead, use an ephemeral, sandboxed environment. The industry standard is utilizing a sidecar container or a dynamic Docker-in-Docker (DinD) setup for tool execution.

```python
import docker
from langchain_core.tools import tool

client = docker.from_env()

@tool
def execute_python_code(code: str) -> str:
    """Executes Python code in a secure, isolated sandbox."""
    try:
        # Run a highly restricted, ephemeral container
        container = client.containers.run(
            "python:3.10-slim",
            command=["python", "-c", code],
            remove=True, # Auto-destroy after execution
            mem_limit="128m",
            network_disabled=True, # Prevent external API calls from the malicious code
            user="nobody" # Non-root user
        )
        return container.decode("utf-8")
    except docker.errors.ContainerError as e:
        return f"Execution failed: {e.stderr}"
```
By enforcing memory limits, disabling networking, and using a non-root user, the blast radius of any malicious script is severely contained.

## Role-Based Access Control (RBAC) in Graph States

Agents should only access tools and data required for their specific user. In LangGraph, RBAC should be mapped directly to the `StateGraph`'s schema.

When defining your state, include a `user_context` field. Tools should explicitly check this context before execution.

```python
from typing import Annotated, TypedDict
from pydantic import BaseModel

class AgentState(TypedDict):
    messages: list
    user_role: str
    allowed_tools: list[str]

def execute_tool_node(state: AgentState):
    tool_name = state["pending_tool"]
    
    if tool_name not in state["allowed_tools"]:
        return {"messages": [SystemMessage(content=f"Access Denied: Tool {tool_name} requires elevated privileges.")]}
    
    # Execute tool logic...
```
By explicitly managing the `allowed_tools` list based on the user's authenticated session, you prevent an injected prompt from forcing the agent to call an unauthorized administrative tool.
