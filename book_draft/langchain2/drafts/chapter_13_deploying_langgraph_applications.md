# Chapter 13: Deploying LangGraph Applications

After designing, securing, and testing your LangGraph application, the final hurdle is deployment. Deploying stateful multi-agent systems presents unique challenges compared to standard web APIs, primarily due to long execution times, WebSocket requirements for streaming, and complex environment variable management.

## Packaging Python AI Applications

The era of massive, unmanageable `requirements.txt` files is ending. For enterprise AI deployments, utilize modern package managers like `Poetry` or `uv` to ensure deterministic builds. 

Locking your dependencies is critical because the AI ecosystem (especially LangChain and LangGraph) moves fast. An unpinned version update can break complex graph orchestrations instantly.

## Dockerizing the LangGraph Application

Containerization is mandatory for reliable AI deployment. A well-constructed `Dockerfile` ensures that your agent runs identically in your local environment, your CI pipeline, and production.

```dockerfile
# Use a slim, secure base image
FROM python:3.11-slim as builder

# Set up working directory
WORKDIR /app

# Install uv for rapid dependency resolution
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies into the system environment securely
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY ./my_agent ./my_agent

# Expose the API port
EXPOSE 8000

# Run the application securely
CMD ["uvicorn", "my_agent.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Managing Secrets
Never bake API keys (OpenAI, Anthropic, LangSmith) into the Docker image. Inject them at runtime using environment variables or a secret manager (like AWS Secrets Manager or HashiCorp Vault) to prevent accidental credential leakage in your container registry.

## Deploying via FastAPI and LangServe

To expose your LangGraph application, wrap it in an API. While you can build raw FastAPI routes, **LangServe** provides built-in endpoints for streaming tokens, handling tool calls, and managing state out of the box.

```python
from fastapi import FastAPI
from langserve import add_routes
from my_agent.graph import compiled_graph

app = FastAPI(
    title="Enterprise AI Agent API",
    version="1.0",
    description="A multi-agent system powered by LangGraph"
)

# LangServe automatically creates /invoke, /stream, and /batch endpoints
add_routes(
    app,
    compiled_graph,
    path="/agent"
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Serverless vs. Containerized Deployment

When choosing a deployment architecture, consider the nature of your agents:

*   **Serverless (Google Cloud Run, AWS App Runner):** Ideal for stateless or short-lived agents. They scale to zero to save costs. However, serverless platforms have strict timeout limits (e.g., 5-15 minutes). If your LangGraph workflow involves a Human-in-the-Loop or extensive multi-step reasoning, it will likely time out.
*   **Containerized (AWS ECS, Kubernetes):** The recommended approach for complex, stateful LangGraph applications. Deploying on ECS or Kubernetes allows for long-running processes, background workers for asynchronous agent execution, and robust handling of checkpointers (e.g., connecting a persistent volume to a PostgreSQL state database).

## The Production Readiness Checklist

Before switching traffic to your new agent, verify the following:
- [ ] **State Persistence Configured:** Checkpointers (like PostgreSQL) are implemented to handle graph state, ensuring data isn't lost if the container restarts.
- [ ] **Observability Enabled:** LangSmith tracing is active, with specific tags for environment (`prod`, `staging`).
- [ ] **Rate Limiting Implemented:** API endpoints are rate-limited to prevent malicious users from draining your LLM token budget.
- [ ] **Sandboxed Tools Verified:** Any tool executing external code operates in a strict, isolated environment.
- [ ] **Fallback Models Configured:** The LangChain LLM instantiation includes fallback routing (e.g., falling back to Anthropic if OpenAI is down).
