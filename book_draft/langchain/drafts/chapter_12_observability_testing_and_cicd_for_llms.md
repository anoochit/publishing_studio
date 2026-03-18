# Chapter 12: Observability, Testing, and CI/CD for LLMs

The transition from a prototype to a production-ready agentic system requires abandoning "vibes-based" testing—the practice of casually chatting with your agent and feeling out whether it works. In 2026, enterprise Generative AI demands the same rigor as traditional software engineering: unit testing, continuous integration, and deep observability.

## Why "Vibes-Based" Testing is Dead

When dealing with stateful LangGraph workflows, a single agent interaction can span multiple tool calls, routing decisions, and context retrievals. Manual testing simply cannot cover the combinatorial explosion of potential edge cases. Worse, LLMs are non-deterministic; what works today might fail tomorrow due to subtle model drift or a prompt tweak. We need automated, systematic evaluations.

## Unit Testing Agents: Mocking with `pytest`

Just like you would mock a database in standard backend testing, you must mock LLM responses to test the routing and logic of your LangGraph nodes. This ensures your graph structure is robust, even if the LLM hallucinates.

```python
import pytest
from unittest.mock import patch
from langchain_core.messages import AIMessage, HumanMessage

# Assume we have a routing node defined in our graph
from my_agent.graph import route_based_on_intent

def test_routing_to_escalation():
    # Mocking the LLM's tool call output
    mock_llm_response = AIMessage(
        content="", 
        tool_calls=[{"name": "escalate_to_human", "args": {"reason": "angry customer"}}]
    )
    
    state = {"messages": [HumanMessage(content="I want to speak to a manager!")], "llm_output": mock_llm_response}
    
    # Test the pure logic of the routing node
    next_node = route_based_on_intent(state)
    
    assert next_node == "human_escalation_node", "Graph failed to route to the human in the loop."
```
By isolating the deterministic parts of your LangGraph application from the non-deterministic LLM outputs, you can write rapid, highly reliable CI tests.

## Tracing and Telemetry with LangSmith

While unit tests verify the code paths, you need observability into the LLM's reasoning process in production. LangSmith has become the de facto standard for this.

With LangSmith enabled via environment variables (`LANGCHAIN_TRACING_V2=true`), every execution of your LangGraph is logged as a complete trace.

### Key Metrics to Track
1.  **Latency:** Agents are slow. Tracking latency per node helps identify bottlenecks (e.g., a slow vector DB query vs. slow LLM generation).
2.  **Cost:** Complex multi-agent workflows burn through tokens rapidly. LangSmith aggregates token usage per run, allowing you to monitor unit economics.
3.  **Tool Error Rates:** How often does the LLM provide malformed JSON to your tools? Tracking this highlights areas where prompts need refinement.

## Building CI/CD Evaluation Pipelines (LLM-as-a-Judge)

In your CI/CD pipeline (e.g., GitHub Actions), pure Python unit tests are only step one. Step two is **Evaluation**.

When a developer alters a core prompt, you must evaluate the new agent behavior against a golden dataset. We use an "LLM-as-a-judge" approach to score the output.

```python
from langsmith import Client
from langsmith.evaluation import evaluate, LangChainStringEvaluator

client = Client()

# Define the evaluator
qa_evaluator = LangChainStringEvaluator("qa")

# Define the target agent execution function
def predict_agent(inputs: dict):
    response = my_langgraph_app.invoke({"messages": [inputs["question"]]})
    return {"answer": response["messages"][-1].content}

# Run the evaluation in CI
def test_agent_accuracy():
    results = evaluate(
        predict_agent,
        data="enterprise-golden-dataset-v1",
        evaluators=[qa_evaluator],
        experiment_prefix="pr-evaluation-",
    )
    
    # Assert passing grade
    assert results.score >= 0.85, "Agent performance dropped below 85% threshold."
```
Integrating this into your CI/CD pipeline ensures that no prompt change or framework update is merged into the `main` branch unless it empirically matches or beats the baseline performance.
