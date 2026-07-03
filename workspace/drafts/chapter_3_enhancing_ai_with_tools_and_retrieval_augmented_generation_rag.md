# Chapter 3: Enhancing AI with Tools and Retrieval-Augmented Generation (RAG)

Intelligent applications often require more than just generating text based on a prompt. They need to interact with the real world—fetching up-to-date information, performing calculations, or executing actions. This chapter delves into two critical techniques GenKit offers to achieve this: **Tool Calling** for external interactions and **Retrieval-Augmented Generation (RAG)** for grounding LLM responses with proprietary or up-to-date data.

## Section 3.1: Tool Calling Fundamentals

Large Language Models (LLMs) are powerful pattern matchers and text generators, but they are limited by their training data and lack the ability to perform actions in the real world or access information beyond what they were trained on. This is where **tools** come in. Tools enable LLMs to extend their capabilities by interacting with external services and APIs, making them truly "agentic."

### The Role of Tools

Tools bridge the gap between an LLM's language understanding and the ability to perform concrete actions or retrieve specific information. Imagine an AI assistant that needs to check the weather, book a flight, or query a company's internal database. These tasks require interaction with external systems, which LLMs cannot do natively. By providing an LLM with a set of well-defined tools, we empower it to:

*   **Access Real-time Data:** Fetch current weather, stock prices, news, etc.
*   **Perform Calculations:** Use a calculator tool for precise arithmetic.
*   **Interact with APIs:** Integrate with CRM systems, e-commerce platforms, booking services, and more.
*   **Query Databases:** Retrieve specific information from structured data stores.

### `defineTool` in GenKit

GenKit simplifies the process of making external functionalities available to your LLM. The `defineTool` function allows you to wrap any asynchronous function as a tool. When defining a tool, you provide:

*   **`name`**: A unique identifier for the tool.
*   **`description`**: A human-readable description of what the tool does. This is **crucial** because the LLM uses this description (along with the input schema) to understand when and how to invoke the tool. A clear, concise description helps the LLM make informed decisions.
*   **`inputSchema`**: A schema (using Zod for TypeScript/Node.js or Pydantic for Python) that defines the expected input parameters for the tool. This ensures type-safe data exchange between the LLM and your tool.
*   **`outputSchema`**: A schema defining the type of data the tool will return.

When an LLM (configured with `tools`) processes a prompt, it evaluates whether any of the provided tools are relevant to fulfilling the user's request. If it decides to use a tool, it generates a "tool call" with the necessary arguments, which GenKit then executes. The result of the tool's execution is then returned to the LLM, which can use it to formulate its final response.

```typescript
// Node.js/TypeScript - Simple tool for getting current time
import { defineTool, defineFlow, generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai'; // Assuming gemini is configured
import { z } from 'zod';

// 1. Define the getCurrentTime tool
export const getCurrentTime = defineTool(
  {
    name: 'getCurrentTime',
    description: 'Gets the current local time and date in a readable format.',
    inputSchema: z.void(), // This tool takes no input
    outputSchema: z.string(),
  },
  async () => {
    return new Date().toLocaleString();
  }
);

// 2. Define a flow that uses the tool
export const timeInquiryFlow = defineFlow(
  {
    name: 'timeInquiryFlow',
    inputSchema: z.string().describe('A question about the current time.'),
    outputSchema: z.string(),
  },
  async (question) => {
    // The LLM decides if 'getCurrentTime' is relevant to the question
    const response = await generate({
      model: gemini,
      prompt: question,
      tools: [getCurrentTime], // Make the tool available to the LLM
    });
    return response.text();
  }
);
```

```python
# Python - Simple tool for getting current time
import genkit
from genkit.models import gemini # Assuming gemini is configured
from datetime import datetime
from pydantic import BaseModel

# 1. Define the get_current_time tool
@genkit.define_tool(
    name="getCurrentTime",
    description="Gets the current local time and date in a readable format."
)
def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 2. Define a flow that uses the tool
@genkit.define_flow(name="timeInquiryFlow", input_schema=str, output_schema=str)
async def time_inquiry_flow(question: str):
    # The LLM decides if 'get_current_time' is relevant to the question
    response = await genkit.generate(
        model=gemini,
        prompt=question,
        tools=[get_current_time], # Make the tool available to the LLM
    )
    return response.text()
```

In the `timeInquiryFlow` example, when a user asks "What time is it?", the LLM, recognizing the `description` of `getCurrentTime`, will intelligently decide to invoke it. GenKit handles the serialization of the tool call, execution of the tool function, and feeding the result back to the LLM for a natural language response.

## Section 3.2: Building Custom Tools

The real power of GenKit's tool calling lies in your ability to build custom tools tailored to your application's specific needs. These tools can range from simple data lookups to complex integrations with external APIs.

### Practical Tool Examples

Let's explore building a more functional tool: a simple calculator. This tool will take structured input, perform an operation, and return a structured output.

#### Tool Input and Output Validation

Defining `inputSchema` and `outputSchema` for your tools is paramount for ensuring robustness. It guarantees that the LLM provides inputs in the expected format and that your tool returns data that can be reliably consumed by the LLM or subsequent flow steps. Zod (TypeScript) and Pydantic (Python) provide powerful, declarative ways to define these schemas, including validation rules (e.g., `min`, `max`, `enum`).

#### Asynchronous Tools

Many real-world tools involve operations that take time, such as network requests to external APIs or database queries. GenKit's `defineTool` expects an `async` function, allowing you to seamlessly integrate asynchronous operations without blocking your main application thread.

#### Error Handling in Tools

Robust error handling within your tools is critical for stable AI applications. If an external API call fails, or if there's an issue with tool logic (e.g., division by zero), your tool should gracefully handle these exceptions. Returning `null` or a specific error object (if defined in the `outputSchema`) can signal to the LLM that the tool operation was not entirely successful, allowing the LLM to potentially try an alternative approach or inform the user.

```typescript
// Node.js/TypeScript - Tool for a simple calculator
import { defineTool, defineFlow, generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

export const calculator = defineTool(
  {
    name: 'calculator',
    description: 'Performs basic arithmetic operations like addition, subtraction, multiplication, and division.',
    inputSchema: z.object({
      operation: z.enum(['add', 'subtract', 'multiply', 'divide']).describe('The arithmetic operation to perform.'),
      num1: z.number().describe('The first number.'),
      num2: z.number().describe('The second number.'),
    }),
    outputSchema: z.number().nullable().describe('The result of the operation, or null if division by zero occurred.'),
  },
  async (input) => {
    switch (input.operation) {
      case 'add': return input.num1 + input.num2;
      case 'subtract': return input.num1 - input.num2;
      case 'multiply': return input.num1 * input.num2;
      case 'divide':
        if (input.num2 === 0) {
          console.error('Error: Division by zero attempted.');
          return null; // Handle division by zero
        }
        return input.num1 / input.num2;
      default: return null;
    }
  }
);

export const calculatorFlow = defineFlow(
  {
    name: 'calculatorFlow',
    inputSchema: z.string().describe('A mathematical question or calculation request.'),
    outputSchema: z.string(),
  },
  async (question) => {
    const response = await generate({
      model: gemini,
      prompt: `Use the calculator tool to answer the following question: ${question}`,
      tools: [calculator], // Make the calculator tool available
    });
    return response.text();
  }
);
```

```python
# Python - Tool for a simple calculator
import genkit
from genkit.models import gemini
from pydantic import BaseModel, Field
from typing import Literal, Optional

class CalculatorInput(BaseModel):
    operation: Literal["add", "subtract", "multiply", "divide"] = Field(description="The arithmetic operation to perform.")
    num1: float = Field(description="The first number.")
    num2: float = Field(description="The second number.")

@genkit.define_tool(
    name="calculator",
    description="Performs basic arithmetic operations like addition, subtraction, multiplication, and division."
)
def calculator_tool(input: CalculatorInput) -> Optional[float]:
    if input.operation == "add":
        return input.num1 + input.num2
    elif input.operation == "subtract":
        return input.num1 - input.num2
    elif input.operation == "multiply":
        return input.num1 * input.num2
    elif input.operation == "divide":
        if input.num2 == 0:
            print("Error: Division by zero attempted.")
            return None # Handle division by zero
        return input.num1 / input.num2
    return None

@genkit.define_flow(name="calculatorFlow", input_schema=str, output_schema=str)
async def calculator_flow(question: str):
    response = await genkit.generate(
        model=gemini,
        prompt=f"Use the calculator tool to answer the following question: {question}",
        tools=[calculator_tool], # Make the calculator tool available
    )
    return response.text()
```

When you query `calculatorFlow` with "What is 120 divided by 5?", the LLM will parse the request, identify `calculator_tool` as relevant, extract `operation: 'divide'`, `num1: 120`, and `num2: 5`, call the tool, and then incorporate the tool's result (24.0) into its final answer.

## Section 3.3: Introduction to RAG

While tool calling allows LLMs to *act* and get *real-time* information, there's another crucial aspect for intelligent applications: grounding responses in a specific, often proprietary, knowledge base. This is where **Retrieval-Augmented Generation (RAG)** comes into play.

### The Limitations of LLMs

Despite their vast knowledge, LLMs have inherent limitations:

*   **Hallucinations:** LLMs can sometimes generate plausible-sounding but factually incorrect information.
*   **Out-of-date Information:** Their knowledge is limited to their training data, which has a cutoff date. They cannot access recent events or constantly evolving data.
*   **Lack of Domain-Specific Knowledge:** LLMs are generalists. They don't inherently know about your company's internal policies, product details, or specific customer data.

### What is RAG?

RAG is a technique that enhances LLM capabilities by retrieving relevant information from an external knowledge base *before* generating a response. Instead of solely relying on its internal knowledge, the LLM is provided with factual, up-to-date, or proprietary context to inform its answer.

The process typically involves:

1.  **Query:** A user submits a query.
2.  **Retrieval:** A retriever component searches a dedicated knowledge base (e.g., a vector database containing your documents) for information relevant to the query.
3.  **Augmentation:** The retrieved documents (or snippets from them) are appended to the user's query, creating an augmented prompt.
4.  **Generation:** The LLM receives this augmented prompt and generates a response based on both its general knowledge and the provided context.

### Benefits of RAG

Implementing RAG offers significant advantages:

*   **Improved Accuracy:** By providing factual context, RAG significantly reduces hallucinations.
*   **Reduced Out-of-Date Information:** Agents can access the most current information available in your knowledge base.
*   **Access to Proprietary Data:** Ground LLM responses in your organization's specific documents, manuals, or databases.
*   **Source Citation:** Responses can include references to the retrieved documents, allowing users to verify information.
*   **Reduced Model Re-training:** You don't need to re-train or fine-tune LLMs with new data; simply update your external knowledge base.

### RAG Architecture Overview

A typical RAG system involves these high-level components:

*   **Data Source:** Your raw documents (e.g., PDFs, web pages, internal wikis, database records).
*   **Chunking/Indexing Pipeline:** Processes the data source, breaking documents into smaller, manageable "chunks" and generating numerical representations (embeddings) for each chunk. These embeddings are then stored in a vector database.
*   **Vector Database:** A specialized database optimized for storing and querying high-dimensional vectors (embeddings). It allows for efficient "similarity search," finding chunks whose embeddings are most semantically similar to a given query embedding.
*   **Retriever:** The component responsible for taking a user query, converting it into an embedding, querying the vector database, and returning the most relevant document chunks.
*   **Generator (LLM):** The Large Language Model that receives the original query *and* the retrieved context to formulate its final answer.

## Section 3.4: Vector Databases and Embeddings

The heart of an efficient RAG system lies in how it finds relevant information. This is powered by **embeddings** and **vector databases**.

### Embeddings Explained

An embedding is a numerical representation (a vector of numbers) of a piece of text (or image, audio, etc.) that captures its semantic meaning. Texts with similar meanings will have embeddings that are "closer" to each other in a multi-dimensional space.

*   **How they work:** Large neural networks, known as embedding models, are trained to convert human-readable text into these dense vectors.
*   **Semantic Meaning:** The key insight is that the *distance* or *similarity* between these vectors corresponds to the semantic similarity between the original texts.

### Vector Search

Once your documents are converted into embeddings and stored, you can perform **vector search**. When a user submits a query:

1.  The query is also converted into an embedding using the same embedding model.
2.  This query embedding is then compared to all document embeddings in the vector database.
3.  The database returns the document chunks whose embeddings are most similar to the query embedding. These are the "most relevant" pieces of information.

### Vector Databases

Vector databases are purpose-built to efficiently store, index, and query vector embeddings at scale. Popular options include:

*   **Pinecone**
*   **Chroma**
*   **Weaviate**
*   **Qdrant**
*   **Google Cloud Firestore** (can be used for vector similarity search when integrated with embedding models and custom indexing).

GenKit doesn't impose a specific vector database, allowing you to integrate with your preferred solution. It provides an abstraction through `defineRetriever` to connect to these services.

### Integrating GenKit with Vector Stores

GenKit allows you to define a `retriever` that encapsulates the logic for interacting with your chosen vector store. This `retriever` will take a query, perform the vector search, and return the relevant documents.

```typescript
// Node.js/TypeScript - Conceptual embedding generation
import { generate } from '@genkit-ai/core';
import { textEmbeddingGecko } from '@genkit-ai/vertexai'; // Example embedding model
import { z } from 'zod';

// Configure GenKit to use the embedding model (if not already done)
// configureGenkit({
//   plugins: [
//     vertexai(),
//   ],
// });

async function generateEmbedding(text: string) {
  const embeddingResponse = await textEmbeddingGecko.embed(
    { text: text },
  );
  // The 'embedding' field contains the numerical vector
  return embeddingResponse.embedding;
}
```

```python
# Python - Conceptual embedding generation
import genkit
from genkit.models import text_embedding_gecko # Example embedding model

# Configure GenKit to use the embedding model (if not already done)
# genkit.configure(plugins=[vertexai.vertexai_plugins()])

async def generate_embedding(text: str):
    embedding_response = await text_embedding_gecko.embed(
        text=text
    )
    # The 'embedding' field contains the numerical vector
    return embedding_response.embedding
```

The code snippets above demonstrate how to generate an embedding for a given text using a GenKit-supported embedding model. This is the first step in preparing your data for a vector database and, subsequently, for a RAG flow.

## Section 3.5: Implementing RAG Flows

With an understanding of tools, embeddings, and vector databases, we can now combine these concepts to build a complete RAG flow in GenKit. The goal is to first retrieve relevant information and then augment the LLM's prompt with that context.

### Defining a Custom Retriever

GenKit's `defineRetriever` function is used to create a custom retrieval mechanism. This function takes a query, interacts with your vector store (or any data source), and returns a list of relevant document chunks.

*   **`name`**: A unique identifier for the retriever.
*   **`inputSchema`**: The schema for the query string.
*   **`outputSchema`**: The schema for the retrieved documents, typically an array of objects containing `id` and `content`.

```typescript
// Node.js/TypeScript - RAG flow example (conceptual with a dummy retriever)
import { defineFlow, generate, defineRetriever } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai'; // Assuming gemini is configured
import { z } from 'zod';

// --- Dummy Retriever (replace with actual vector store integration) ---
// In a real application, this would interact with a Pinecone, Chroma, etc., client
const myDocumentRetriever = defineRetriever(
  {
    name: 'myDocumentRetriever',
    inputSchema: z.string().describe('The query string for document retrieval.'),
    outputSchema: z.array(z.object({
      id: z.string().describe('Unique ID of the document chunk.'),
      content: z.string().describe('The content of the retrieved document chunk.'),
    })),
  },
  async (query) => {
    // Simulate querying a vector DB
    console.log(`Simulating document retrieval for query: "${query}"`);
    if (query.toLowerCase().includes('genkit')) {
      return [{ id: 'gk-doc-1', content: 'GenKit is an open-source framework developed by Google for building AI-powered applications, especially those featuring AI agents. It emphasizes observability, testing, and deployment.' }];
    } else if (query.toLowerCase().includes('rag')) {
      return [{ id: 'rag-doc-1', content: 'Retrieval Augmented Generation (RAG) improves LLM responses by fetching relevant data from an external knowledge base and including it in the prompt, reducing hallucinations.' }];
    } else if (query.toLowerCase().includes('google')) {
        return [{ id: 'google-doc-1', content: 'Google is a multinational technology company focusing on online advertising, search engine technology, cloud computing, computer software, quantum computing, e-commerce, artificial intelligence, and consumer electronics.' }];
    }
    return []; // No relevant documents found
  }
);
// -------------------------------------------------------------------

export const ragFlow = defineFlow(
  {
    name: 'ragFlow',
    inputSchema: z.string().describe('User query to be answered using RAG.'), // user query
    outputSchema: z.string().describe('LLM response grounded in retrieved context.'), // LLM response with context
  },
  async (query) => {
    // Step 1: Retrieve relevant documents using the custom retriever
    const relevantDocs = await myDocumentRetriever.retrieve(query);

    // Concatenate the content of retrieved documents to form the context
    const context = relevantDocs.map(doc => doc.content).join('\n\n');

    // Step 2: Construct an augmented prompt for the LLM
    const prompt = `Answer the following question based *only* on the provided context. If the answer is not explicitly present in the context, state that you don't know. Do not make up information.

Context:
${context}

Question: ${query}

Answer:`;

    // Step 3: Generate the response using the LLM with the augmented prompt
    const response = await generate({
      model: gemini,
      prompt: prompt,
      config: { temperature: 0.1 }, // Low temperature for factual, grounded responses
    });
    return response.text();
  }
);
```

```python
# Python - RAG flow example (conceptual with a dummy retriever)
import genkit
from genkit.models import gemini # Assuming gemini is configured
from genkit.core.types import RetrievalOutput
from typing import List

# --- Dummy Retriever (replace with actual vector store integration) ---
# In a real application, this would interact with a Pinecone, Chroma, etc., client
@genkit.define_retriever(name="myDocumentRetriever", input_schema=str, output_schema=List[RetrievalOutput])
async def my_document_retriever(query: str) -> List[RetrievalOutput]:
    # Simulate querying a vector DB
    print(f"Simulating document retrieval for query: '{query}'")
    if "genkit" in query.lower():
        return [RetrievalOutput(content="GenKit is an open-source framework developed by Google for building AI-powered applications, especially those featuring AI agents. It emphasizes observability, testing, and deployment.")]
    elif "rag" in query.lower():
        return [RetrievalOutput(content="Retrieval Augmented Generation (RAG) improves LLM responses by fetching relevant data from an external knowledge base and including it in the prompt, reducing hallucinations.")]
    elif "google" in query.lower():
        return [RetrievalOutput(content="Google is a multinational technology company focusing on online advertising, search engine technology, cloud computing, computer software, quantum computing, e-commerce, artificial intelligence, and consumer electronics.")]
    return [] # No relevant documents found

# -------------------------------------------------------------------

@genkit.define_flow(name="ragFlow", input_schema=str, output_schema=str)
async def rag_flow(query: str):
    # Step 1: Retrieve relevant documents using the custom retriever
    relevant_docs = await my_document_retriever.retrieve(query)

    # Concatenate the content of retrieved documents to form the context
    context = "\n\n".join([doc.content for doc in relevant_docs])

    # Step 2: Construct an augmented prompt for the LLM
    prompt = f"""Answer the following question based *only* on the provided context. If the answer is not explicitly present in the context, state that you don't know. Do not make up information.

Context:
{context}

Question: {query}

Answer:"""

    # Step 3: Generate the response using the LLM with the augmented prompt
    response = await genkit.generate(
        model=gemini,
        prompt=prompt,
        config=genkit.GenerationConfig(temperature=0.1), # Low temperature for factual, grounded responses
    )
    return response.text()
```

### RAG Flow Design

The `ragFlow` demonstrates a common RAG pattern:

1.  **Retrieve:** It first calls `myDocumentRetriever.retrieve(query)` to get a list of semantically relevant document chunks.
2.  **Context Construction:** The content of these retrieved documents is then concatenated to form a `context` string.
3.  **Prompt Augmentation:** The `context` is embedded directly into the `prompt` sent to the LLM. Notice the crucial instruction: "*only* on the provided context. If the answer is not explicitly present in the context, state that you don't know." This is a key prompt engineering technique for RAG.

### Prompt Engineering for RAG

Effective prompt engineering is vital for successful RAG:

*   **Explicit Instructions:** Clearly instruct the LLM to use *only* the provided context and to state if the answer isn't found. This mitigates hallucination.
*   **Context Delimiters:** Use clear delimiters (like `Context:` and `Question:`) to separate the retrieved context from the actual user query in the prompt, helping the LLM distinguish between the two.
*   **Temperature Settings:** For RAG tasks that demand factual accuracy, a lower `temperature` setting in the `generate` call is often preferred, encouraging the LLM to be less creative and more focused on the provided information.

This end-to-end example showcases how GenKit empowers you to build robust, factual, and context-aware AI applications by seamlessly integrating tool-calling and retrieval-augmented generation. You can now build AI agents that not only understand language but also act upon it and ground their responses in reliable data sources.
