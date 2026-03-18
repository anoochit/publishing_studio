# Chapter 2: Deconstructing the Magic: Building a Raw Python Agent

One of the most common complaints from developers adopting modern AI orchestration frameworks is that they feel too "magical." When a framework hides the underlying mechanics of prompt generation, tool calling, and state management behind deeply nested abstractions, it becomes incredibly difficult to debug when things go wrong.

To truly master LangChain and LangGraph, you first need to understand exactly what they are doing under the hood. In this chapter, we are going to build a fully functional ReAct (Reason + Act) agent from scratch using nothing but the official OpenAI Python SDK, `pydantic` for schema validation, and plain Python `while` loops. 

By feeling the pain of manual state management, brittle string parsing, and complex loop orchestration, you will gain a deep appreciation for the problems that modern frameworks solve.

---

## 2.1 The Core Loop: Building a Reasoning Engine

At its heart, an AI agent is a `while` loop that continuously queries a Large Language Model (LLM) until a specific stop condition is met. The LLM acts as the "brain," analyzing the conversation history (state) to decide whether it needs to take an action (call a tool) or return a final answer to the user.

Let's build a minimalist version of this loop. We will start by defining the system prompt that forces the model to think in the ReAct format we discussed in Chapter 1.

```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

system_prompt = """
You are a logical AI agent. You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop, you output an Answer.

Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Available Actions:
- calculate:
    e.g. Action: calculate: 4 * 7
    Returns the result of a math expression.
- get_weather:
    e.g. Action: get_weather: London
    Returns the current weather in a given city.

Example Session:
Question: What is the weather in Paris?
Thought: I should check the weather in Paris.
Action: get_weather: Paris
PAUSE

You will be called again with this:
Observation: The weather in Paris is 22 degrees Celsius and sunny.

Thought: I have the information I need.
Answer: The weather in Paris is 22 degrees and sunny.
"""
```

Notice how much heavy lifting is being done by raw text manipulation. We are explicitly instructing the model to output a specific syntax (`Action: <tool_name>: <input>`). Before the widespread adoption of native JSON-based tool calling APIs, this was exactly how early LangChain `AgentExecutor` implementations worked.

Next, let's implement the Python loop that drives this behavior.

```python
import re

class Agent:
    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        # This list represents our conversational memory (state)
        self.messages = [
            {"role": "system", "content": system_prompt}
        ]

    def __call__(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        result = self.execute_loop()
        return result

    def execute_loop(self):
        # The ReAct Loop
        for i in range(5):  # Hardcoded limit to prevent infinite loops
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=self.messages,
                temperature=0.0
            )
            
            message = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": message})
            
            print(f"\\n--- Turn {i+1} ---\\n{message}")

            # If the model gives a final Answer, break the loop
            if "Answer:" in message:
                return message.split("Answer:")[1].strip()

            # Otherwise, look for an Action to execute
            action_match = re.search(r"Action: ([a-z_]+): (.+)", message)
            if action_match:
                tool_name = action_match.group(1)
                tool_input = action_match.group(2)
                
                # Execute the tool
                if tool_name not in known_tools:
                    observation = f"Error: Tool {tool_name} not found."
                else:
                    observation = known_tools[tool_name](tool_input)
                
                print(f"Observation: {observation}")
                
                # Feed the observation back into the LLM's memory
                self.messages.append({"role": "user", "content": f"Observation: {observation}"})
                
        return "Error: Agent reached maximum iterations."
```

In just 40 lines of code, we have created an autonomous entity. It manages its own state (`self.messages`), iterates over sub-tasks, and dynamically decides what to do next based on the environment (`Observation`). 

However, we are relying on a brittle regular expression (`re.search`) to extract the tool calls. If the LLM outputs `Action: get_weather(London)` instead of `Action: get_weather: London`, our entire application crashes. This is a severe vulnerability in production environments.

---

## 2.2 Defining Tools and Schemas with Pydantic

To fix the brittleness of regex parsing, modern LLMs provide native function-calling capabilities. Instead of begging the LLM to output a specific text format, we provide it with a strict JSON schema defining the exact parameters a tool expects. 

In Python, the industry standard for defining these schemas is `pydantic`. `pydantic` allows us to define data models using native Python type hints, automatically validating inputs and generating the necessary JSON schemas.

Let's define a tool using `pydantic`:

```python
from pydantic import BaseModel, Field
import json

# 1. Define the schema
class WeatherToolInput(BaseModel):
    city: str = Field(description="The name of the city, e.g., 'San Francisco'")
    country: str = Field(description="The 2-letter country code, e.g., 'US'")

# 2. Implement the actual Python function
def get_weather(city: str, country: str) -> str:
    # Imagine this queries a real weather API
    return f"The weather in {city}, {country} is 72F and sunny."

# 3. Generate the OpenAI-compatible JSON Schema
weather_tool_schema = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather in a given city.",
        "parameters": WeatherToolInput.model_json_schema()
    }
}
```

By leveraging `pydantic`'s `model_json_schema()`, we guarantee that the LLM understands exactly what arguments the function requires. If the LLM tries to call `get_weather` with an integer instead of a string, or forgets the `country` parameter, the API will (ideally) correct it or we can catch the validation error securely using `pydantic`'s `model_validate_json()` before running arbitrary code.

> **Engineer’s Note: The Security Perimeter**
> When you map LLM outputs to Python function executions, `pydantic` acts as your first line of defense. Never execute a tool directly using a raw JSON string from an LLM. Always marshal the data through a `pydantic` model to ensure type safety, enforce required fields, and strip out injected parameters. 

---

## 2.3 Managing State and Conversational Memory Manually

In our `Agent` class, we managed state by simply appending dictionaries to a `self.messages` list. This is naive conversational memory. 

In a production environment where you have thousands of concurrent users, this approach falls apart quickly. You cannot store `self.messages` in raw Python RAM. It must be serialized and persisted to a database (like PostgreSQL or Redis) between HTTP requests.

Furthermore, context windows are finite. If the agent enters a long loop, the `self.messages` list will eventually exceed the token limit of the model (e.g., 128k tokens). Managing this manually requires complex logic:

1.  **Token Counting:** You must use a library like `tiktoken` to estimate the exact number of tokens in your `messages` array before every API call.
2.  **Windowing/Summarization:** If you exceed the limit, you have to dynamically prune old messages or ask the LLM to write a summary of the older context, swapping out 50 messages for a single "Summary" message.
3.  **Thread Concurrency:** You need a concept of `thread_id` so that User A's `self.messages` don't overwrite User B's `self.messages` in your database.

Writing this state management code from scratch for every single application is tedious, error-prone, and a massive waste of engineering resources. 

---

## 2.4 Identifying the Breaking Point: Why We Need Frameworks

Let's review the technical debt we have accumulated in our small custom agent:

1.  **Brittle Orchestration:** Our `for` loop is hardcoded. If we want to implement "Human-in-the-Loop" (pausing the loop to ask a human to approve an action before executing it), we would have to rewrite the entire execution engine to handle asynchronous state suspension.
2.  **Lack of Telemetry:** If our model starts hallucinating, we have no way to trace the execution steps visually. We are relying on `print()` statements in standard output.
3.  **Vendor Lock-in:** Our code is tightly coupled to the `openai` Python SDK. Switching to Anthropic's Claude 3.5 Sonnet or a local Llama 3 instance via `vLLM` would require rewriting the core loop and schema generation logic, as different APIs have slightly different function-calling implementations.
4.  **Complex Memory:** We have no easy way to persist this agent's state to a database or gracefully handle token limits.

### The Transition to LangChain and LangGraph

This is exactly where the raw Python approach hits its breaking point. You *can* build an enterprise agent from scratch, but you will spend 80% of your time maintaining boilerplate orchestration code and only 20% of your time optimizing your prompt and tools.

The LangChain ecosystem exists to abstract away this exact boilerplate. 
*   **LangChain** provides the standardized wrappers: it normalizes tool schemas, standardizes LLM interfaces (so swapping OpenAI for Anthropic is a one-line change), and handles token counting.
*   **LangGraph** provides the orchestration engine: it replaces our brittle `for` loop with a robust, mathematically sound State Machine (a directed graph). It handles checkpointing (saving memory to a database automatically), loops, conditional routing, and Human-in-the-Loop interruptions out of the box.

Now that you have built an agent from scratch and felt the friction of raw Python orchestration, you are ready to wield these frameworks properly. In Chapter 3, we will dive into the LangChain ecosystem and map everything we just built manually to its modern, scalable counterparts.