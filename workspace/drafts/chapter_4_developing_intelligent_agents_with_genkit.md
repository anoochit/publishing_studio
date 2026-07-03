# Chapter 4: Developing Intelligent Agents with GenKit

This chapter delves into the practical aspects of building intelligent agents using GenKit. We will explore how GenKit's fundamental components—flows, models, and tools—can be combined to create autonomous, decision-making systems. From simple task-specific agents to more complex multi-purpose assistants, you'll learn design patterns, memory management techniques, advanced prompting strategies, and routing mechanisms essential for effective agent development.

## Section 4.1: Defining an "Agent" in GenKit

In the context of GenKit, an "agent" isn't a single, predefined entity but rather a pattern of behavior achieved by orchestrating GenKit's core primitives: `defineFlow`, `defineTool`, and `generate`. At its heart, an agent in GenKit is often a flow that intelligently directs the interaction between Large Language Models (LLMs) and various external functionalities (tools) or internal sub-flows.

### GenKit's Agentic Primitives

*   **`defineFlow`**: Flows act as the central nervous system of your agent. They define the sequence of operations, the inputs they accept, and the outputs they produce. An agent's "brain" is essentially encapsulated within a flow's logic.
*   **`defineTool`**: Tools provide the agent with the ability to interact with the external world. These can be anything from simple data lookups to complex API calls, database interactions, or even triggering other GenKit flows.
*   **`generate`**: The `generate` function is where the LLM's intelligence comes into play. When provided with a list of available tools, an LLM (especially those with tool-calling capabilities) can analyze a user's prompt and decide which tool to invoke, if any, and with what parameters.

### Agent as an Orchestrator

Think of a GenKit agent as an orchestrator. It doesn't inherently *have* intelligence outside of the LLM, but it provides the structure and access points for the LLM to exhibit intelligent behavior. The flow dictates the overall process, while the LLM, guided by the prompt and tool descriptions, makes dynamic decisions on which actions to take.

### Decision-Making in Agents

The LLM's decision-making process is profoundly influenced by:

1.  **Prompt Engineering:** The way you craft the initial prompt and subsequent conversational turns guides the LLM on its objective and constraints.
2.  **Tool Descriptions:** The `description` parameter in `defineTool` is critical. A clear and concise description helps the LLM understand when and how to use a particular tool. Without good descriptions, the LLM may fail to invoke tools even when appropriate.
3.  **Input/Output Schemas:** Well-defined schemas for tools ensure the LLM understands the required inputs and the expected outputs, leading to more reliable tool invocations.

Let's look at a high-level example of an "agentic" flow that can leverage tools (assumed to be defined in Chapter 3) to answer a multi-faceted query involving both time and calculation.

#### Example: Agentic Math and Time Flow

This flow takes a user question and, through the LLM's tool-calling capabilities, can determine if it needs to fetch the current time or perform a calculation using previously defined tools.

**Node.js/TypeScript**

```typescript
// Node.js/TypeScript - Agent as a flow orchestrating tools
import { defineFlow, generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

// Assume 'getCurrentTime' and 'calculator' tools are defined as in Chapter 3
// For demonstration, these tools would be imported or globally available
// import { getCurrentTime, calculator } from './chapter_3_tools';

export const agenticMathAndTimeFlow = defineFlow(
  {
    name: 'agenticMathAndTimeFlow',
    inputSchema: z.string(), // e.g., "What is the time and what is 5 + 3?"
    outputSchema: z.string(),
  },
  async (question) => {
    // The LLM decides whether to call tools based on the prompt
    const response = await generate({
      model: gemini,
      prompt: question,
      tools: [/* assumed: */ getCurrentTime, calculator],
      // Ensure 'getCurrentTime' and 'calculator' are properly imported or mock for testing
    });
    return response.text();
  }
);
```

**Python**

```python
# Python - Agent as a flow orchestrating tools
import genkit
from genkit.models import gemini
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal, Optional

# Assume 'get_current_time' and 'calculator_tool' are defined as in Chapter 3
# For this example, we'll redefine them conceptually to show context,
# but in a real app, you'd import them from your tools module.

# @genkit.define_tool(name="getCurrentTime", description="Gets the current time and date.")
# def get_current_time() -> str:
#     return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# class CalculatorInput(BaseModel):
#     operation: Literal["add", "subtract", "multiply", "divide"]
#     num1: float
#     num2: float

# @genkit.define_tool(name="calculator", description="Performs basic arithmetic operations.")
# def calculator_tool(input: CalculatorInput) -> Optional[float]:
#     if input.operation == "add": return input.num1 + input.num2
#     elif input.operation == "subtract": return input.num1 - input.num2
#     elif input.operation == "multiply": return input.num1 * input.num2
#     elif input.operation == "divide": return input.num1 / input.num2 if input.num2 != 0 else None
#     return None

@genkit.define_flow(name="agenticMathAndTimeFlow", input_schema=str, output_schema=str)
async def agentic_math_and_time_flow(question: str):
    response = await genkit.generate(
        model=gemini,
        prompt=question,
        tools=[get_current_time, calculator_tool],  # assumed tools
    )
    return response.text()
```

In these examples, the `agenticMathAndTimeFlow` receives a natural language `question`. The LLM, given access to the `getCurrentTime` and `calculator` tools, will decide whether to invoke them based on the query's content. This demonstrates how GenKit enables LLMs to take actions beyond just text generation, making them behave more like intelligent agents.

## Section 4.2: Simple Agent Design Patterns

GenKit's flexible flow and tool architecture allows for the creation of various agent design patterns, each tailored for specific tasks. Here, we'll illustrate a few common ones, providing a detailed example for a summarization agent.

### Summarization Agent

A summarization agent is designed to take a block of text and condense it into a shorter, coherent summary. This is a common use case for LLMs, and GenKit flows provide a structured way to implement and manage such an agent.

**Node.js/TypeScript**

```typescript
// Node.js/TypeScript - Summarization Agent
import { defineFlow, generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

export const summarizationAgentFlow = defineFlow(
  {
    name: 'summarizationAgentFlow',
    inputSchema: z.object({
      text: z.string(),
      length: z.enum(['short', 'medium', 'long']).default('medium'),
    }),
    outputSchema: z.string(),
  },
  async (input) => {
    const prompt = `Summarize the following text to a ${input.length} length:\n\n${input.text}`;
    const summary = await generate({
      model: gemini,
      prompt: prompt,
    });
    return summary.text();
  }
);
```

**Python**

```python
# Python - Summarization Agent
import genkit
from genkit.models import gemini
from pydantic import BaseModel
from typing import Literal

class SummarizationInput(BaseModel):
    text: str
    length: Literal["short", "medium", "long"] = "medium"

@genkit.define_flow(name="summarizationAgentFlow", input_schema=SummarizationInput, output_schema=str)
async def summarization_agent_flow(input: SummarizationInput):
    prompt = f"Summarize the following text to a {input.length} length:\n\n{input.text}"
    summary = await genkit.generate(
        model=gemini,
        prompt=prompt,
    )
    return summary.text()
```

This `summarizationAgentFlow` takes `text` and a desired `length` as input, constructs a prompt, and uses the `gemini` model to generate the summary. The input schema ensures that the `length` parameter is one of the allowed values.

### Data Extraction Agent

A data extraction agent focuses on pulling structured information from unstructured text. This typically involves leveraging GenKit's structured output capabilities (covered in Chapter 2, Section 2.4).

To create a data extraction agent:

1.  **Define a `genkit.defineFlow`**: This flow will encapsulate the extraction logic.
2.  **Use `genkit.generate` with an `output` schema**: Provide a `zod` schema (TypeScript) or Pydantic model (Python) to `generate` to instruct the LLM to return data in a specific JSON format.
3.  **Craft a precise prompt**: Guide the LLM on what information to extract and from where.

### Question Answering (Q&A) Agent

A Q&A agent aims to answer user questions accurately, often by grounding its responses in specific, provided information. This pattern combines the Retrieval-Augmented Generation (RAG) techniques discussed in Chapter 3, Section 3.5, with an LLM for generation.

To create a Q&A agent:

1.  **Define a `genkit.defineFlow`**: This flow will orchestrate the retrieval and generation steps.
2.  **Integrate `genkit.defineRetriever`**: Use a custom retriever (from Chapter 3) to fetch relevant documents based on the user's query.
3.  **Use `genkit.generate` with retrieved context**: Inject the retrieved documents into the LLM's prompt to ensure its answers are based on the provided information.

## Section 4.3: Agent Memory and Context Management

One of the significant challenges in building intelligent agents with LLMs is managing memory and context. LLMs are fundamentally stateless; each `generate` call is independent unless you explicitly provide the necessary context. This section explores how to equip your GenKit agents with both short-term conversational memory and a conceptual understanding of long-term memory.

### The Challenge of Stateless LLMs

By default, an LLM treats each interaction as a new, isolated request. If you ask an LLM "What is the capital of France?", and then immediately follow up with "And what is its population?", the LLM has no inherent knowledge of the previous question. To maintain a coherent conversation or perform multi-turn tasks, agents need a mechanism to remember past interactions.

### Short-Term Memory (Conversational History)

Short-term memory typically refers to the immediate conversational history. For an LLM to understand the context of a current query, it needs access to the preceding turns of the conversation. In GenKit, this is achieved by passing an array of messages as part of the `prompt` parameter to `genkit.generate`.

The `genkit.Message` (Python) or `Message` type (TypeScript with `Role` enum) is used to represent individual turns, distinguishing between `user` and `model` (or `assistant`) roles.

#### Implementing Conversational Memory

Let's build a conversational agent flow that maintains a chat history.

**Node.js/TypeScript**

```typescript
// Node.js/TypeScript - Conversational memory
import { defineFlow, generate, Message, Role } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

export const conversationalAgentFlow = defineFlow(
  {
    name: 'conversationalAgentFlow',
    inputSchema: z.object({
      history: z.array(z.object({
        role: z.enum(['user', 'model']),
        content: z.string(),
      })).optional(),
      currentMessage: z.string(),
    }),
    outputSchema: z.string(),
  },
  async (input) => {
    const messages: Message[] = [];
    // If there's a history, add previous messages to the prompt
    if (input.history) {
      messages.push(...input.history.map(msg => ({
        role: msg.role === 'user' ? Role.USER : Role.MODEL,
        content: msg.content,
      })));
    }
    // Add the current user message
    messages.push({ role: Role.USER, content: input.currentMessage });

    const response = await generate({
      model: gemini,
      prompt: messages, // Pass the entire conversation history
    });
    return response.text();
  }
);
```

**Python**

```python
# Python - Conversational memory
import genkit
from genkit.models import gemini
from pydantic import BaseModel
from typing import List, Literal, Optional
from genkit.core.types import Message # Explicitly import Message

class ChatMessage(BaseModel):
    role: Literal["user", "model"]
    content: str

class ConversationalInput(BaseModel):
    history: Optional[List[ChatMessage]] = []
    current_message: str

@genkit.define_flow(name="conversationalAgentFlow", input_schema=ConversationalInput, output_schema=str)
async def conversational_agent_flow(input: ConversationalInput):
    messages: List[Message] = [] # Specify type for clarity
    if input.history:
        for msg in input.history:
            # Map Pydantic model to GenKit's internal Message type
            messages.append(Message(role=msg.role, content=msg.content))
    messages.append(Message(role="user", content=input.current_message))

    response = await genkit.generate(
        model=gemini,
        prompt=messages, # Pass the entire conversation history
    )
    return response.text()
```

In these flows, the `history` array (which you would manage client-side or in a backend store) is transformed into an array of `Message` objects and passed directly to the `generate` function. This allows the LLM to "remember" previous turns and generate contextually relevant responses.

### Long-Term Memory (External Storage)

For knowledge that needs to persist beyond a single conversation or requires a broader information base (e.g., product documentation, user preferences, factual knowledge), long-term memory is essential. This is where external storage solutions come into play, often integrated using Retrieval-Augmented Generation (RAG).

*   **Vector Databases:** As explored in Chapter 3, vector databases (like Pinecone, Chroma, or Firestore with vector similarity search) are ideal for storing and retrieving high-dimensional embeddings of your custom data.
*   **Traditional Databases:** For structured data like user profiles, order histories, or specific facts, traditional relational (e.g., PostgreSQL) or NoSQL (e.g., MongoDB, Firestore) databases can serve as long-term memory, which your GenKit tools can query.

GenKit's role in long-term memory management is to provide the `defineRetriever` mechanism (Chapter 3) and enable tools to interact with these external storage systems, bringing relevant information into the current prompt's context.

## Section 4.4: Advanced Prompting for Agent Behavior

Beyond basic instructions, advanced prompting techniques are crucial for shaping an agent's persona, improving its reasoning, and making its outputs more reliable and consistent. GenKit facilitates these techniques by allowing flexible construction of the `prompt` parameter.

### System Instructions/Prompts

System instructions define the overall role, tone, and constraints of your agent. They are typically provided at the beginning of the conversation to set the stage for the LLM's behavior. In GenKit, these are part of the `messages` array passed to `generate`, with the `role` set to `Role.SYSTEM`.

### Few-Shot Examples

Few-shot prompting involves providing one or more examples of input-output pairs within the prompt. This helps the LLM understand the desired format, style, or specific task without explicit rule-based programming. It's particularly useful when the task is nuanced or requires adherence to a particular structure.

### Chain-of-Thought Prompting

Chain-of-Thought (CoT) prompting encourages the LLM to articulate its reasoning steps before providing a final answer. By explicitly asking the LLM to "think step by step" or "show your work," you can often achieve more accurate and coherent responses, especially for complex reasoning tasks. While not a GenKit-specific API, CoT is a powerful prompt engineering technique you can apply within your GenKit flows.

### Self-Correction

Designing agents that can identify and correct their own errors is an advanced but powerful technique. This often involves:
1.  **Initial Generation:** The agent generates a response.
2.  **Critique/Evaluation:** A separate prompt or an external tool evaluates the response for errors (e.g., hallucinations, logical inconsistencies).
3.  **Refinement:** If errors are found, the agent uses the critique to revise its original response.

#### Example: System Instructions and Few-Shot Prompting

Let's enhance our conversational flow to include a system prompt for persona and a few-shot example to guide the LLM's response style.

**Node.js/TypeScript**

```typescript
// Node.js/TypeScript - System instructions and few-shot example
import { defineFlow, generate, Message, Role } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

export const advancedAgentPromptingFlow = defineFlow(
  {\n    name: 'advancedAgentPromptingFlow',\n    inputSchema: z.string(), // User query\n    outputSchema: z.string(),\n  },\n  async (query) => {\n    const messages: Message[] = [\n      {\n        role: Role.SYSTEM,\n        content: 'You are a polite and helpful assistant. Always respond with a positive tone.'\n      },\n      {\n        role: Role.USER,\n        content: 'What is the capital of France?'\n      },\
      {\n        role: Role.MODEL,\n        content: 'The capital of France is Paris! 😊'\n      },\
      {\n        role: Role.USER,\n        content: query\n      },\
    ];\n\n    const response = await generate({\n      model: gemini,\n      prompt: messages,\n    });\n    return response.text();\n  }\n);\n```

**Python**

```python
# Python - System instructions and few-shot example
import genkit
from genkit.models import gemini
from genkit.core.types import Message, Role
from pydantic import BaseModel
from typing import List

@genkit.define_flow(name="advancedAgentPromptingFlow", input_schema=str, output_schema=str)
async def advanced_agent_prompting_flow(query: str):\n    messages: List[Message] = [\n        Message(role=Role.SYSTEM, content='You are a polite and helpful assistant. Always respond with a positive tone.'),\n        Message(role=Role.USER, content='What is the capital of France?'),\n        Message(role=Role.MODEL, content='The capital of France is Paris! 😊'),\n        Message(role=Role.USER, content=query),\
    ]\n\n    response = await genkit.generate(\n        model=gemini,\n        prompt=messages,\n    )\n    return response.text()\
```

In these examples, the `Role.SYSTEM` message establishes the assistant's persona. The subsequent user-model exchange serves as a few-shot example, demonstrating the desired format and cheerful tone. When the actual `query` is presented, the LLM is more likely to adhere to these established patterns.

## Section 4.5: Agent Routing and Orchestration

As agents become more sophisticated, they often need to perform different actions based on the user's intent or intermediate results. Agent routing and orchestration involve directing the flow of execution to the appropriate tool, sub-flow, or LLM interaction.

### Conditional Logic in Flows

The simplest form of routing is using standard conditional logic (`if/else` or `switch` statements) within your GenKit flows. Based on the input, an LLM's initial response (e.g., classifying intent), or the output of a tool, your flow can execute different branches of logic.

### Tool-Based Routing

A powerful pattern for routing is to define a tool whose primary purpose is to classify the user's intent or determine the next best action. When the LLM calls this tool, the tool's output can then be used by the surrounding flow to route the request. This allows the LLM to implicitly "decide" the routing path.

### Multi-Turn Interactions for Routing

Sometimes, an agent may not have enough information to route a request definitively. In such cases, the agent can engage in multi-turn interactions, asking clarifying questions to the user until it gathers enough context to make an informed decision. This involves maintaining conversational memory and updating the prompt with each turn.

### Example: A Multi-Purpose Assistant

Let's create a multi-purpose assistant that can route user queries to different functionalities, such as summarization, calculation, or general Q&A, based on the identified intent. This example uses a dedicated tool for intent classification.

**Node.js/TypeScript**

```typescript
// Node.js/TypeScript - Multi-purpose assistant with routing
import { defineFlow, generate, defineTool } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

// Assume summarizationAgentFlow, calculator tool from previous sections
// import { summarizationAgentFlow } from './chapter_4_agents'; // or relevant path
// import { calculator } from './chapter_3_tools'; // or relevant path

// Define a tool for intent classification
export const classifyIntent = defineTool(
  {
    name: 'classifyIntent',
    description: 'Classifies the user\'s intent based on their query. Can identify summarize, calculate, or general question answering.',
    inputSchema: z.object({
      query: z.string(),
    }),
    outputSchema: z.object({
      intent: z.enum(['summarize', 'calculate', 'general_qa', 'unknown']),
      details: z.string().optional(), // Potentially extract details for the intent
    }),
  },
  async (input) => {
    // This could be an LLM call or rule-based logic for initial classification
    // For a robust solution, an LLM call with a structured output schema is preferred here.
    if (input.query.toLowerCase().includes('summarize')) {
      return { intent: 'summarize', details: 'text to summarize' };
    }
    if (input.query.toLowerCase().includes('calculate') || input.query.match(/(\\d+\\s*[\\+\\-\\*\\/]\\s*\\d+)/)) {
      return { intent: 'calculate', details: 'mathematical expression' };
    }
    // Fallback to LLM for more nuanced classification
    const intentLLM = await generate({
        model: gemini,
        prompt: `Classify the intent of the following query: "${input.query}". Return only 'summarize', 'calculate', 'general_qa', or 'unknown'.`,
        output: { schema: z.object({ intent: z.enum(['summarize', 'calculate', 'general_qa', 'unknown']) }) }
    });
    return intentLLM.output();
  }
);


export const multiPurposeAssistantFlow = defineFlow(
  {
    name: 'multiPurposeAssistantFlow',
    inputSchema: z.string(), // User query
    outputSchema: z.string(),
  },
  async (query) => {
    // Use the defined tool for intent classification
    const intentResult = await classifyIntent.run({ query });

    if (intentResult.intent === 'summarize') {
      // In a real application, you would parse the content to summarize from the query
      // and call the summarizationAgentFlow with appropriate input.
      return "Placeholder: Calling summarization agent..."; // await summarizationAgentFlow.run({ text: query, length: 'medium' });
    } else if (intentResult.intent === 'calculate') {
      // In a real application, you would parse numbers and operation from the query
      // and call the calculator tool.
      return "Placeholder: Calling calculator tool..."; // const calcResult = await calculator.run({ operation: 'add', num1: 5, num2: 3 }); return `Calculated: ${calcResult}`;
    } else if (intentResult.intent === 'general_qa') {
      // For general questions, we can directly use the LLM
      const response = await generate({ model: gemini, prompt: query });
      return response.text();
    } else {
      return "I'm sorry, I don't understand that request. Can you please rephrase?";
    }
  }
);
```

**Python**

```python
# Python - Multi-purpose assistant with routing
import genkit
from genkit.models import gemini
from pydantic import BaseModel
from typing import Literal, Optional
import re

# Assume summarization_agent_flow, calculator_tool from previous sections
# from .chapter_4_agents import summarization_agent_flow # or relevant path
# from .chapter_3_tools import calculator_tool # or relevant path

class IntentClassificationOutput(BaseModel):
    intent: Literal["summarize", "calculate", "general_qa", "unknown"]
    details: Optional[str] = None

@genkit.define_tool(name="classifyIntent", description="Classifies the user's intent based on their query.",
                    input_schema=BaseModel(query=str), output_schema=IntentClassificationOutput)
async def classify_intent(input: BaseModel) -> IntentClassificationOutput:
    query = input.query
    if "summarize" in query.lower():
        return IntentClassificationOutput(intent="summarize", details="text to summarize")
    # Check for simple arithmetic patterns
    if "calculate" in query.lower() or re.search(r'\d+\s*[\+\-\*\/]\s*\d+', query):
        return IntentClassificationOutput(intent="calculate", details="mathematical expression")

    # Fallback to LLM for more nuanced classification
    intent_llm_response = await genkit.generate(
        model=gemini,
        prompt=f'Classify the intent of the following query: "{query}". Return only \'summarize\', \'calculate\', \'general_qa\', or \'unknown\'.',
        output=IntentClassificationOutput # Assuming LLM can directly output this Pydantic model
    )
    return intent_llm_response.output()

@genkit.define_flow(name="multiPurposeAssistantFlow", input_schema=str, output_schema=str)
async def multi_purpose_assistant_flow(query: str):
    intent_result = await classify_intent.run(query=query)

    if intent_result.intent == "summarize":
        # In a real application, you would parse the content to summarize from the query
        # and call the summarization_agent_flow with appropriate input.
        return "Placeholder: Calling summarization agent..." # await summarization_agent_flow.run(text=query, length='medium')
    elif intent_result.intent == "calculate":
        # In a real application, you would parse numbers and operation from the query
        # and call the calculator_tool.
        return "Placeholder: Calling calculator tool..." # calc_result = await calculator_tool.run(operation='add', num1=5, num2=3); return f"Calculated: {calc_result}"
    elif intent_result.intent == "general_qa":
        # For general questions, we can directly use the LLM
        response = await genkit.generate(model=gemini, prompt=query)
        return response.text()
    else:
        return "I'm sorry, I don't understand that request. Can you please rephrase?"
```

In this `multiPurposeAssistantFlow`, the `classifyIntent` tool is used to determine the user's goal. Based on the `intent` returned by this tool, the flow then conditionally calls the appropriate sub-agent or tool. This demonstrates a powerful pattern for building flexible and modular agents in GenKit.

## Summary

This chapter provided a deep dive into developing intelligent agents with GenKit. We explored how GenKit's foundational concepts—flows, models, and tools—can be combined to create agentic behaviors. We covered various agent design patterns, including summarization, data extraction, and Q&A agents, and learned how to manage agent memory for more coherent interactions. Finally, we delved into advanced prompting techniques and demonstrated how to implement robust agent routing and orchestration to build multi-purpose assistants. With these skills, you are now equipped to design and implement more sophisticated and capable AI agents within your applications using GenKit.
