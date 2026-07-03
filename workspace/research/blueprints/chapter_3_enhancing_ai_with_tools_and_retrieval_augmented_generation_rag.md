# Chapter 3: Enhancing AI with Tools and Retrieval-Augmented Generation (RAG)

**Target File Name:** `chapter_3_enhancing_ai_with_tools_and_retrieval_augmented_generation_rag.md`

## Section 3.1: Tool Calling Fundamentals

### Roadmap

- **The Role of Tools:** Explain why LLMs need tools to interact with real-world data and services.
- **`defineTool` in GenKit:** How to declare a function as a tool that an LLM can invoke.
- **Tool Invocation within `generate`:** Demonstrate how an LLM decides to call a tool based on the prompt.
- **Tool Parameters and Schemas:** Defining input schemas for tools to ensure type-safe data exchange.

### Required Technical Concepts/APIs

- `genkit.defineTool`
- `genkit.generate` (with tool-calling enabled models)
- Input/Output schemas for tools (e.g., Zod, Pydantic)

### Code Snippets

```typescript
// Node.js/TypeScript - Simple tool for getting current time
import { defineTool, generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

export const getCurrentTime = defineTool(
  {
    name: 'getCurrentTime',
    description: 'Gets the current time and date.',
    inputSchema: z.void(),
    outputSchema: z.string(),
  },
  async () => {
    return new Date().toLocaleString();
  }
);

export const timeInquiryFlow = defineFlow(
  {
    name: 'timeInquiryFlow',
    inputSchema: z.string(),
    outputSchema: z.string(),
  },
  async (question) => {
    const response = await generate({
      model: gemini,
      prompt: question,
      tools: [getCurrentTime],
    });
    return response.text();
  }
);
```

```python
# Python - Simple tool for getting current time
import genkit
from genkit.models import gemini
from datetime import datetime

@genkit.define_tool(name="getCurrentTime", description="Gets the current time and date.")
def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@genkit.define_flow(name="timeInquiryFlow", input_schema=str, output_schema=str)
async def time_inquiry_flow(question: str):
    response = await genkit.generate(
        model=gemini,
        prompt=question,
        tools=[get_current_time],
    )
    return response.text()
```

### Target Depth and Developer Instructions

- Provide a clear, simple example of defining and using a tool. Explain how the LLM decides to call the tool. Demonstrate with both TypeScript and Python. Emphasize the importance of `description` for effective tool selection by the LLM.

## Section 3.2: Building Custom Tools

### Roadmap

- **Practical Tool Examples:** Develop tools for common scenarios (e.g., database lookup, external API call, simple calculation).
- **Tool Input and Output Validation:** Ensuring robust data handling using schemas.
- **Asynchronous Tools:** Handling operations that take time, such as network requests.
- **Error Handling in Tools:** Gracefully managing failures within tool executions.

### Required Technical Concepts/APIs

- `genkit.defineTool`
- External API clients (e.g., `axios` in Node.js, `requests` in Python)
- `async`/`await`

### Code Snippets

```typescript
// Node.js/TypeScript - Tool for a simple calculator
import { defineTool } from '@genkit-ai/core';
import { z } from 'zod';

export const calculator = defineTool(
  {
    name: 'calculator',
    description: 'Performs basic arithmetic operations.',
    inputSchema: z.object({
      operation: z.enum(['add', 'subtract', 'multiply', 'divide']),
      num1: z.number(),
      num2: z.number(),
    }),
    outputSchema: z.number().nullable(),
  },
  async (input) => {
    switch (input.operation) {
      case 'add': return input.num1 + input.num2;
      case 'subtract': return input.num1 - input.num2;
      case 'multiply': return input.num1 * input.num2;
      case 'divide': return input.num1 / input.num2;
      default: return null;
    }
  }
);
```

```python
# Python - Tool for a simple calculator
import genkit
from pydantic import BaseModel, Field
from typing import Literal, Optional

class CalculatorInput(BaseModel):
    operation: Literal["add", "subtract", "multiply", "divide"]
    num1: float
    num2: float

@genkit.define_tool(name="calculator", description="Performs basic arithmetic operations.")
def calculator_tool(input: CalculatorInput) -> Optional[float]:
    if input.operation == "add":
        return input.num1 + input.num2
    elif input.operation == "subtract":
        return input.num1 - input.num2
    elif input.operation == "multiply":
        return input.num1 * input.num2
    elif input.operation == "divide":
        if input.num2 == 0:
            return None # Handle division by zero
        return input.num1 / input.num2
    return None
```

### Target Depth and Developer Instructions

- Provide a more complex tool example that takes structured inputs and performs a useful operation. Emphasize input validation and error handling within tools. Show how to integrate this tool into a flow and prompt the LLM to use it. Use both TypeScript and Python.

## Section 3.3: Introduction to RAG

### Roadmap

- **The Limitations of LLMs:** Discuss common issues like hallucinations and out-of-date information.
- **What is RAG?:** Explain Retrieval-Augmented Generation as a technique to ground LLM responses with external, factual data.
- **Benefits of RAG:** Improved accuracy, reduced hallucinations, access to proprietary data, source citation.
- **RAG Architecture Overview:** High-level explanation of the components: retriever, generator, data source.

### Required Technical Concepts/APIs

- Conceptual understanding of RAG.

### Code Snippets

- None, conceptual section.

### Target Depth and Developer Instructions

- Introduce RAG clearly, explaining its purpose and benefits. Avoid getting bogged down in implementation details here, focus on the 'why' and high-level 'what'.

## Section 3.4: Vector Databases and Embeddings

### Roadmap

- **Embeddings Explained:** What are embeddings and how they represent semantic meaning.
- **Vector Search:** How embeddings enable similarity search across large datasets.
- **Vector Databases:** Introduction to specialized databases for storing and querying vector embeddings (e.g., Pinecone, Chroma, Firestore for vector search).
- **Integrating GenKit with Vector Stores:** Conceptual overview of how GenKit can interact with these services.

### Required Technical Concepts/APIs

- Embedding models (e.g., `vertexai.textEmbeddingGecko`)
- Vector database concepts (conceptual interaction, no specific API calls yet).
- `genkit.defineRetriever` (conceptual at this stage).

### Code Snippets

```typescript
// Node.js/TypeScript - Conceptual embedding generation
import { generate } from '@genkit-ai/core';
import { textEmbeddingGecko } from '@genkit-ai/vertexai';

async function generateEmbedding(text: string) {
  const embedding = await textEmbeddingGecko.embed(
    { text: text },
  );
  return embedding.embedding;
}
```

```python
# Python - Conceptual embedding generation
import genkit
from genkit.models import text_embedding_gecko

async def generate_embedding(text: str):
    embedding_response = await text_embedding_gecko.embed(
        text=text
    )
    return embedding_response.embedding
```

### Target Depth and Developer Instructions

- Explain embeddings and vector databases in an accessible way. Provide a conceptual code snippet for generating an embedding. Focus on the core principles needed for the next section on RAG implementation. Use both TypeScript and Python examples.

## Section 3.5: Implementing RAG Flows

### Roadmap

- **Defining a Custom Retriever:** How to implement `genkit.defineRetriever` to fetch documents from a vector store.
- **RAG Flow Design:** Constructing a GenKit flow that first retrieves relevant information and then uses it in a `generate` call.
- **Prompt Engineering for RAG:** Crafting prompts that effectively incorporate retrieved context.
- **End-to-End Example:** Building a full RAG application (e.g., a Q&A system over a custom document set).

### Required Technical Concepts/APIs

- `genkit.defineRetriever`
- `genkit.retrieve`
- `genkit.generate`
- Integration with a chosen vector store's client library (e.g., Pinecone client, ChromaDB client, Firestore client with vector search).

### Code Snippets

```typescript
// Node.js/TypeScript - RAG flow example (conceptual with a dummy retriever)
import { defineFlow, generate, defineRetriever } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

// --- Dummy Retriever (replace with actual vector store integration) ---
const myDocumentRetriever = defineRetriever(
  {
    name: 'myDocumentRetriever',
    inputSchema: z.string(), // query string
    outputSchema: z.array(z.object({
      id: z.string(),
      content: z.string(),
    })),
  },
  async (query) => {
    // In a real scenario, this would query a vector DB
    console.log(`Simulating retrieval for: ${query}`);
    if (query.includes('GenKit')) {
      return [{ id: 'doc1', content: 'GenKit is an open-source framework for building AI-powered applications.' }];
    } else if (query.includes('RAG')) {
      return [{ id: 'doc2', content: 'Retrieval Augmented Generation combines LLMs with external knowledge bases.' }];
    }
    return [];
  }
);
// -------------------------------------------------------------------

export const ragFlow = defineFlow(
  {
    name: 'ragFlow',
    inputSchema: z.string(), // user query
    outputSchema: z.string(), // LLM response with context
  },
  async (query) => {
    const relevantDocs = await myDocumentRetriever.retrieve(query);
    const context = relevantDocs.map(doc => doc.content).join('\n');

    const prompt = `Answer the following question based on the provided context. If the answer is not in the context, state that you don't know.\n\nContext:\n${context}\n\nQuestion: ${query}`;

    const response = await generate({
      model: gemini,
      prompt: prompt,
    });
    return response.text();
  }
);
```

```python
# Python - RAG flow example (conceptual with a dummy retriever)
import genkit
from genkit.models import gemini
from genkit.core.types import RetrievalOutput
from typing import List

# --- Dummy Retriever (replace with actual vector store integration) ---
@genkit.define_retriever(name="myDocumentRetriever", input_schema=str, output_schema=List[RetrievalOutput])
async def my_document_retriever(query: str) -> List[RetrievalOutput]:
    print(f"Simulating retrieval for: {query}")
    if "GenKit" in query:
        return [RetrievalOutput(content="GenKit is an open-source framework for building AI-powered applications.")]
    elif "RAG" in query:
        return [RetrievalOutput(content="Retrieval Augmented Generation combines LLMs with external knowledge bases.")]
    return []
# -------------------------------------------------------------------

@genkit.define_flow(name="ragFlow", input_schema=str, output_schema=str)
async def rag_flow(query: str):
    relevant_docs = await my_document_retriever.retrieve(query)
    context = "\n".join([doc.content for doc in relevant_docs])

    prompt = f"Answer the following question based on the provided context. If the answer is not in the context, state that you don't know.\n\nContext:\n{context}\n\nQuestion: {query}"

    response = await genkit.generate(
        model=gemini,
        prompt=prompt,
    )
    return response.text()
```

### Target Depth and Developer Instructions

- Provide a complete, runnable RAG flow using a simplified or dummy retriever (with clear instructions to replace it with real vector store integration). Emphasize how the retrieved context is injected into the prompt. Show examples for both TypeScript and Python. Discuss prompt engineering strategies for RAG to ensure accurate and grounded responses.
