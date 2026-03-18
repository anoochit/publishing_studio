# Chapter 9: Agentic RAG (Retrieval-Augmented Generation)

## 9.1 The Evolution from Simple RAG to Agentic RAG

Standard Retrieval-Augmented Generation (RAG) processes are typically linear: a user asks a question, the system converts it into a vector, fetches the top *k* similar chunks from a vector database, and passes those chunks to an LLM to generate an answer. While effective for simple queries, this "retrieve-and-read" paradigm frequently falls short in complex, real-world backend systems. 

What happens when the retrieved documents are irrelevant? What if the user's query requires synthesizing information from multiple distinct sources (e.g., an internal vector database, a relational SQL database, and the public web)? Standard RAG pipelines lack the routing, self-reflection, and self-correction capabilities needed to handle these edge cases gracefully.

Enter **Agentic RAG**. 

Agentic RAG treats retrieval as a set of tools available to an intelligent agent. Instead of a hardcoded pipeline, we design a state machine where the agent dynamically dictates the flow of execution based on continuous evaluation. If retrieved documents are irrelevant, the agent rewrites the query and tries again. If the generated answer contains hallucinations, the agent detects it and attempts a regeneration. 

In this chapter, we will design and implement a robust Agentic RAG backend using Python, LangGraph, and a vector database. We'll focus on the core logic, state management, and the API endpoints required to integrate this agent into a broader software ecosystem.

## 9.2 Architecture and Core Logic

Our Agentic RAG backend is built as a cyclic graph. We define a highly specific `GraphState` that keeps track of the original question, the evolving context, and internal flags (such as whether a hallucination was detected).

The core nodes of our system are:
1. **Retrieve**: Fetches documents from a vector store based on the current query.
2. **Grade Documents**: Evaluates whether the retrieved documents are relevant to the query. If none are relevant, it flags the need for query transformation.
3. **Generate**: Synthesizes the final answer using the relevant documents.
4. **Transform Query**: If the retrieval yields poor results, an LLM rewrites the query to optimize for better vector search results.
5. **Web Search / External Fallback**: An optional node executed if internal sources fail to provide the necessary information.

## 9.3 Database Schemas and Vector Setup

For our backend, we will assume the use of an in-memory or standalone vector store like ChromaDB or PostgreSQL with `pgvector`. 

When designing schemas for Agentic RAG, metadata is as important as the vector embeddings. Below is a conceptual schema representing how documents should be indexed to support advanced agentic routing.

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    source: str = Field(description="Origin of the document (e.g., 'confluence', 'github', 'jira')")
    author: Optional[str] = Field(None, description="Author of the document")
    timestamp: int = Field(description="Epoch timestamp of document creation")
    access_level: str = Field(default="public", description="RBAC access level")

class DocumentChunk(BaseModel):
    id: str = Field(description="Unique identifier for the chunk")
    content: str = Field(description="The text content of the chunk")
    embedding: List[float] = Field(description="The vector representation (e.g., 1536 dimensions for OpenAI)")
    metadata: DocumentMetadata
```

By structuring our metadata robustly, the agent can formulate queries that pre-filter the vector database (e.g., "Only retrieve documents from 'github' created after '2023-01-01'"), dramatically improving retrieval precision.

## 9.4 Server-Side Implementation with LangGraph

Let's implement the core logic of our Agentic RAG graph. We will define our state, create the nodes, and compile the graph.

### 9.4.1 Defining the State

In LangGraph, the state is passed between nodes. We use a `TypedDict` to enforce strict typing.

```python
from typing import TypedDict, List
from langchain_core.documents import Document

class RAGGraphState(TypedDict):
    """
    Represents the state of our Agentic RAG graph.
    """
    question: str
    generation: str
    documents: List[Document]
    retry_count: int
```

### 9.4.2 Implementing the Nodes

Next, we write the Python functions representing the backend logic for our nodes.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma

# Assume `vectorstore` is a pre-initialized Chroma instance
retriever = vectorstore.as_retriever()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def retrieve_node(state: RAGGraphState):
    """Node to retrieve documents based on the current question."""
    print("---RETRIEVE---")
    question = state["question"]
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question}

def grade_documents_node(state: RAGGraphState):
    """Node to filter out irrelevant documents."""
    print("---GRADE DOCUMENTS---")
    question = state["question"]
    documents = state["documents"]
    
    # Simple binary grading prompt
    prompt = PromptTemplate(
        template=\"\"\"You are a strict grader assessing relevance of a retrieved document to a user question.
        Document: {context}
        Question: {question}
        Answer 'yes' if the document contains relevant information, otherwise 'no'.\"\"\",
        input_variables=["context", "question"],
    )
    chain = prompt | llm | StrOutputParser()
    
    filtered_docs = []
    for d in documents:
        score = chain.invoke({"question": question, "context": d.page_content})
        if "yes" in score.lower():
            filtered_docs.append(d)
            
    return {"documents": filtered_docs, "question": question}

def generate_node(state: RAGGraphState):
    """Node to generate the final answer."""
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    
    context = "\n\n".join(doc.page_content for doc in documents)
    prompt = PromptTemplate(
        template=\"\"\"Use the following pieces of retrieved context to answer the question. 
        If you don't know the answer, just say that you don't know. 
        Question: {question} 
        Context: {context} 
        Answer:\"\"\",
        input_variables=["question", "context"],
    )
    chain = prompt | llm | StrOutputParser()
    generation = chain.invoke({"context": context, "question": question})
    
    return {"documents": documents, "question": question, "generation": generation}

def transform_query_node(state: RAGGraphState):
    """Node to rewrite the user query if retrieval fails."""
    print("---TRANSFORM QUERY---")
    question = state["question"]
    
    prompt = PromptTemplate(
        template=\"\"\"You are generating an optimized search query for a vector database.
        Look at the initial question and formulate an improved question that clarifies the intent.
        Initial question: {question}
        Improved question:\"\"\",
        input_variables=["question"],
    )
    chain = prompt | llm | StrOutputParser()
    better_question = chain.invoke({"question": question})
    
    # Increment retry counter to prevent infinite loops
    retry_count = state.get("retry_count", 0) + 1
    
    return {"question": better_question, "documents": state["documents"], "retry_count": retry_count}
```

### 9.4.3 Routing and Graph Compilation

We now need a conditional routing function to decide the next step after grading. If documents are relevant, we proceed to generation. If not, we transform the query.

```python
def decide_to_generate(state: RAGGraphState):
    """Conditional edge logic after grading documents."""
    filtered_documents = state["documents"]
    retry_count = state.get("retry_count", 0)
    
    if not filtered_documents:
        # If we have tried too many times, stop to avoid infinite loops
        if retry_count >= 3:
            return "generate" # Force generation (will likely result in "I don't know")
        print("---DECISION: ALL DOCUMENTS ARE IRRELEVANT, TRANSFORM QUERY---")
        return "transform_query"
    else:
        print("---DECISION: DOCUMENTS RELEVANT, GENERATE---")
        return "generate"
```

Finally, we tie it all together into a `StateGraph`.

```python
from langgraph.graph import END, StateGraph

workflow = StateGraph(RAGGraphState)

# Define nodes
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("grade_documents", grade_documents_node)
workflow.add_node("generate", generate_node)
workflow.add_node("transform_query", transform_query_node)

# Define edges
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    }
)
workflow.add_edge("transform_query", "retrieve")
workflow.add_edge("generate", END)

# Compile
agentic_rag_app = workflow.compile()
```

## 9.5 API Design for Agentic RAG

Exposing an Agentic RAG system via a REST API requires handling potentially long-running requests, as the cyclic nature of the graph means response times are highly variable.

Here is an example of how to expose this via FastAPI, utilizing Server-Sent Events (SSE) to stream the agent's internal thought process back to the client.

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio

app = FastAPI(title="Agentic RAG API")

class QueryRequest(BaseModel):
    question: str

async def generate_rag_stream(question: str):
    """Generator yielding JSON lines representing graph execution state."""
    inputs = {"question": question, "retry_count": 0}
    
    # Stream events from the LangGraph application
    async for event in agentic_rag_app.astream(inputs, stream_mode="updates"):
        for node_name, node_state in event.items():
            # Yield the current node being executed to provide frontend visibility
            yield f"data: {{json.dumps({{'node': node_name, 'status': 'completed'}})}}\n\n"
            
            # If the generation node completed, yield the final answer
            if node_name == "generate":
                yield f"data: {{json.dumps({{'generation': node_state['generation']}})}}\n\n"
                
    yield "data: [DONE]\n\n"

@app.post("/api/v1/rag/stream")
async def stream_rag_query(request: QueryRequest):
    """
    Endpoint to execute the Agentic RAG graph and stream intermediate steps.
    """
    return StreamingResponse(
        generate_rag_stream(request.question), 
        media_type="text/event-stream"
    )
```

### API Considerations
1. **Timeouts**: Agentic loops can take 10-20 seconds. Configure reverse proxies (like Nginx) and load balancers to allow for longer timeout windows.
2. **Idempotency**: RAG queries are generally safe to retry, but if your agent writes data (e.g., logging usage telemetry), ensure those database transactions handle duplicates.
3. **Observability**: The unpredictable nature of the graph means structured logging is paramount. Every API request should inject a unique `trace_id` into the LangGraph configuration to track the execution path through LangSmith or an ELK stack.

## 9.6 Summary

In this chapter, we evolved from a rigid retrieve-and-read pipeline to a dynamic, self-correcting Agentic RAG system. By leveraging LangGraph, we built a server-side state machine capable of grading its own retrievals, rewriting failing queries, and protecting against hallucinations. We also designed a robust streaming API using FastAPI, ensuring frontends remain responsive even during complex, multi-step backend executions. 

Next, we will look at how to modularize our backend further in Chapter 10: Swapping the Brain, exploring how to dynamically route requests across different model providers based on workload and context.
