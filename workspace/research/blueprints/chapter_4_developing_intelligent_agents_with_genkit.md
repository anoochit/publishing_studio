# Chapter 4: Developing Intelligent Agents with GenKit
**Target File Name:** `chapter_4_developing_intelligent_agents_with_genkit.md`

## Section 4.1: Defining an "Agent" in GenKit
### Roadmap:
- **GenKit\'s Agentic Primitives:** How `defineFlow`, `defineTool`, and `generate` combine to create agent-like behaviors.
- **Agent as an Orchestrator:** Emphasize that in GenKit, an agent is often a flow that orchestrates calls to models and tools.
- **Decision-Making in Agents:** How prompt engineering and tool descriptions guide the LLM\'s choices.

### Required Technical Concepts/APIs:
- `genkit.defineFlow`
- `genkit.defineTool`
- `genkit.generate` (with `tools` parameter)

### Code Snippets:
```typescript
// Node.js/TypeScript - Agent as a flow orchestrating tools
import { defineFlow, generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

// Assume 'getCurrentTime' and 'calculator' tools are defined as in Chapter 3
// import { getCurrentTime } from './chapter_3_tools';
// import { calculator } from './chapter_3_tools';

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
      // For demonstration, these tools are assumed to be available globally or imported
    });
    return response.text();
  }
);
```
```python
# Python - Agent as a flow orchestrating tools
import genkit
from genkit.models import gemini
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal, Optional

# Assume 'get_current_time' and 'calculator_tool' are defined as in Chapter 3
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
        tools=[/* assumed: */ get_current_time, calculator_tool],
    )
    return response.text()
```

### Target Depth and Developer Instructions:
- Clarify that GenKit facilitates agentic behavior through its core constructs. Provide a high-level flow demonstrating an LLM using tools to respond to a multi-faceted query, explicitly noting the tools are assumed from Chapter 3 to avoid redundancy. Use both TypeScript and Python.

## Section 4.2: Simple Agent Design Patterns
### Roadmap:
- **Summarization Agent:** A flow that takes text and summarizes it using an LLM.
- **Data Extraction Agent:** A flow that extracts structured information from unstructured text using schema-driven generation.
- **Question Answering Agent:** A flow combining RAG (from Chapter 3) with an LLM for informed responses.

### Required Technical Concepts/APIs:
- `genkit.defineFlow`
- `genkit.generate` (with input/output schemas, RAG context)
- `genkit.retrieve` (from Chapter 3 RAG)

### Code Snippets:
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

### Target Depth and Developer Instructions:
- Illustrate several simple, task-specific agents. Use the summarization agent as a primary example, providing full code for both TypeScript and Python. Briefly explain how data extraction (using structured outputs from Chapter 2) and Q&A (using RAG from Chapter 3) can be similarly structured as agents.

## Section 4.3: Agent Memory and Context Management
### Roadmap:
- **The Challenge of Stateless LLMs:** Explain why LLMs forget previous interactions.
- **Short-Term Memory (Conversational History):** Maintaining recent turns in a conversation to provide context.
- **Implementing Conversational Memory:** Passing chat history as part of the prompt in GenKit.
- **Long-Term Memory (External Storage):** Using vector stores or databases for persistent agent memory.
- **GenKit\'s Role in Context Management:** How GenKit helps structure and manage the flow of context.

### Required Technical Concepts/APIs:
- `genkit.generate` with array of `Part` objects for chat history.
- `genkit.Message` (for Python) or `genkit.Part` (`@genkit-ai/core`)
- Conceptual integration with external storage (e.g., Firestore, custom database).

### Code Snippets:
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
    if (input.history) {
      messages.push(...input.history.map(msg => ({
        role: msg.role === 'user' ? Role.USER : Role.MODEL,
        content: msg.content,
      })));
    }
    messages.push({ role: Role.USER, content: input.currentMessage });

    const response = await generate({
      model: gemini,
      prompt: messages,
    });
    return response.text();
  }
);
```
```python
# Python - Conversational memory
import genkit
from genkit.models import gemini
from pydantic import BaseModel
from typing import List, Literal, Optional

class ChatMessage(BaseModel):
    role: Literal["user", "model"]
    content: str

class ConversationalInput(BaseModel):
    history: Optional[List[ChatMessage]] = []
    current_message: str

@genkit.define_flow(name="conversationalAgentFlow", input_schema=ConversationalInput, output_schema=str)
async def conversational_agent_flow(input: ConversationalInput):
    messages = []
    if input.history:
        for msg in input.history:
            messages.append(genkit.Message(role=msg.role, content=msg.content))
    messages.append(genkit.Message(role="user", content=input.current_message))

    response = await genkit.generate(
        model=gemini,
        prompt=messages,
    )
    return response.text()
```

### Target Depth and Developer Instructions:
- Provide a clear example of how to implement short-term conversational memory by passing message history to `genkit.generate`. Explain `genkit.Message` (or `Role` and `Part` in TS) and how to structure the input. Briefly discuss the concept of long-term memory and point to Chapter 3 (RAG) for its foundational concepts. Use both TypeScript and Python.

## Section 4.4: Advanced Prompting for Agent Behavior
### Roadmap:
- **System Instructions/Prompts:** Guiding the overall behavior and persona of the agent.
- **Few-Shot Examples:** Providing concrete examples within the prompt to demonstrate desired input/output patterns.
- **Chain-of-Thought Prompting:** Encouraging the LLM to "think step-by-step" to improve reasoning.
- **Self-Correction:** Designing prompts that allow agents to identify and fix their own errors.

### Required Technical Concepts/APIs:
- `genkit.generate` `prompt` parameter (complex string construction).
- `genkit.Message` / `Role` for system prompts.

### Code Snippets:
```typescript
// Node.js/TypeScript - System instructions and few-shot example
import { defineFlow, generate, Message, Role } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

export const advancedAgentPromptingFlow = defineFlow(
  {
    name: 'advancedAgentPromptingFlow',
    inputSchema: z.string(), // User query
    outputSchema: z.string(),
  },
  async (query) => {
    const messages: Message[] = [
      {
        role: Role.SYSTEM,
        content: 'You are a polite and helpful assistant. Always respond with a positive tone.'
      },
      {
        role: Role.USER,
        content: 'What is the capital of France?'
      },
      {
        role: Role.MODEL,
        content: 'The capital of France is Paris! 😊'
      },
      {
        role: Role.USER,
        content: query
      },
    ];

    const response = await generate({
      model: gemini,
      prompt: messages,
    });
    return response.text();
  }
);
```
```python
# Python - System instructions and few-shot example
import genkit
from genkit.models import gemini
from genkit.core.types import Message, Role
from pydantic import BaseModel
from typing import List

@genkit.define_flow(name="advancedAgentPromptingFlow", input_schema=str, output_schema=str)
async def advanced_agent_prompting_flow(query: str):
    messages: List[Message] = [
        Message(role=Role.SYSTEM, content='You are a polite and helpful assistant. Always respond with a positive tone.'),
        Message(role=Role.USER, content='What is the capital of France?'),
        Message(role=Role.MODEL, content='The capital of France is Paris! 😊'),
        Message(role=Role.USER, content=query),
    ]

    response = await genkit.generate(
        model=gemini,
        prompt=messages,
    )
    return response.text()
```

### Target Depth and Developer Instructions:
- Provide clear examples of using system instructions for persona setting and few-shot examples for format guidance. Explain how `Role.SYSTEM` messages are used. Briefly introduce Chain-of-Thought and self-correction as advanced concepts without requiring extensive code. Use both TypeScript and Python.

## Section 4.5: Agent Routing and Orchestration
### Roadmap:
- **Conditional Logic in Flows:** Using `if/else` or `switch` statements to direct agent behavior based on input or intermediate results.
- **Tool-Based Routing:** Designing tools that, when called by the LLM, effectively route the request to a specific sub-agent or data source.
- **Multi-Turn Interactions for Routing:** Allowing the agent to ask clarifying questions to determine the correct path.
- **Example: A Multi-Purpose Assistant:** A flow that routes user queries to a summarizer, a calculator tool, or a RAG system based on intent.

### Required Technical Concepts/APIs:
- `genkit.defineFlow` (orchestration logic)
- `genkit.generate` (with `tools` for intent recognition)
- `genkit.run` (for calling sub-flows or tools)
- Input/output schemas for clear decision points.

### Code Snippets:
```typescript
// Node.js/TypeScript - Multi-purpose assistant with routing
import { defineFlow, generate, defineTool } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

// Assume summarizationAgentFlow, calculator tool from previous sections
// import { summarizationAgentFlow } from './chapter_4_agents';
// import { calculator } from './chapter_3_tools';

// Define a tool for intent classification
export const classifyIntent = defineTool(
  {
    name: 'classifyIntent',
    description: 'Classifies the user\'s intent based on their query.',
    inputSchema: z.object({
      query: z.string(),
    }),
    outputSchema: z.object({
      intent: z.enum(['summarize', 'calculate', 'general_qa', 'unknown']),
      details: z.string().optional(),
    }),
  },
  async (input) => {
    // This could be an LLM call or rule-based logic
    if (input.query.toLowerCase().includes('summarize')) {
      return { intent: 'summarize', details: 'text to summarize' };
    }
    if (input.query.toLowerCase().includes('calculate') || input.query.match(/(\d+\s*[\+\-\*\/]\s*\d+)/)) {
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
    const intentResult = await classifyIntent.run({ query }); // Use the defined tool for intent

    if (intentResult.intent === 'summarize') {
      // Dummy content for summarization, in real app would parse 'details' from query
      return "Placeholder: Calling summarization agent..."; // await summarizationAgentFlow.run({ text: query, length: 'medium' });
    } else if (intentResult.intent === 'calculate') {
      // Dummy calculation for now, in real app would parse numbers from query
      return "Placeholder: Calling calculator tool..."; // const calcResult = await calculator.run({ operation: 'add', num1: 5, num2: 3 }); return `Calculated: ${calcResult}`;
    } else if (intentResult.intent === 'general_qa') {
      // Placeholder for RAG or general LLM response
      const response = await generate({ model: gemini, prompt: query });
      return response.text();
    } else {
      return "I'm sorry, I don't understand that request.";
    }
  }
);
```
```python
# Python - Multi-purpose assistant with routing
import genkit
from genkit.models import gemini
from pydantic import BaseModel
from typing import Literal, Optional

# Assume summarization_agent_flow, calculator_tool from previous sections

class IntentClassificationOutput(BaseModel):
    intent: Literal["summarize", "calculate", "general_qa", "unknown"]
    details: Optional[str] = None

@genkit.define_tool(name="classifyIntent", description="Classifies the user's intent based on their query.",
                    input_schema=BaseModel(query=str), output_schema=IntentClassificationOutput)
async def classify_intent(input: BaseModel):
    query = input.query
    if "summarize" in query.lower():
        return IntentClassificationOutput(intent="summarize", details="text to summarize")
    if "calculate" in query.lower() or any(op in query for op in ["+", "-", "*", "/"]):
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
        return "Placeholder: Calling summarization agent..." # await summarization_agent_flow.run(text=query, length='medium')
    elif intent_result.intent == "calculate":
        return "Placeholder: Calling calculator tool..." # calc_result = await calculator_tool.run(operation='add', num1=5, num2=3); return f"Calculated: {calc_result}"
    elif intent_result.intent == "general_qa":
        response = await genkit.generate(model=gemini, prompt=query)
        return response.text()
    else:
        return "I'm sorry, I don't understand that request."
```

### Target Depth and Developer Instructions:
- Provide a clear example of an agent that routes user requests using conditional logic and potentially an intent classification tool. Emphasize how `defineTool` and `defineFlow` work together for orchestration. Use placeholder calls for sub-agents/tools from previous sections to keep the example focused on routing. Use both TypeScript and Python.
