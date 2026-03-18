# Chapter 4: The AI Gateway: Multi-LLM Routing & Optimization

## Introduction

As AI agents and generative features embed themselves into enterprise applications, managing traffic to Large Language Models (LLMs) becomes a primary operational challenge. Direct integrations between backend services and LLM providers lead to duplicated code, fragile fallback mechanisms, and skyrocketing, unmonitored costs.

The modern API Gateway must serve as an "AI Connectivity Layer." This chapter focuses on configuring Kong as an AI Gateway. We will explore recipes for unified routing to multiple LLM providers (OpenAI, Anthropic, AWS Bedrock), implementing cross-provider failover, enforcing token-based rate limits, and caching semantic responses to optimize latency and cost.

---

## Recipe 4.1: Setting up Routing to Multiple LLM Providers

### Problem
You want to expose a standardized, internal API endpoint for LLM consumption so developers don't have to manage different SDKs and authentication methods for OpenAI, Anthropic, or GCP Gemini.

### Solution
Use Kong’s `ai-proxy` plugin to intercept requests on a unified route and translate them into the specific format required by the target LLM provider.

```yaml
_format_version: "3.0"
services:
  - name: internal-llm-service
    url: http://localhost # The actual upstream URL is dynamically overridden by the plugin
    routes:
      - name: openai-chat-route
        paths:
          - /llm/openai
        plugins:
          - name: ai-proxy
            config:
              route_type: "llm/v1/chat"
              auth:
                header_name: "Authorization"
                header_value: "Bearer <OPENAI_API_KEY>"
              model:
                provider: "openai"
                name: "gpt-4"

      - name: anthropic-chat-route
        paths:
          - /llm/anthropic
        plugins:
          - name: ai-proxy
            config:
              route_type: "llm/v1/chat"
              auth:
                header_name: "x-api-key"
                header_value: "<ANTHROPIC_API_KEY>"
              model:
                provider: "anthropic"
                name: "claude-3-opus"
```

### Discussion
The `ai-proxy` plugin abstracts the provider's specific API contract. Internal developers send a standardized JSON request (following Kong's generic `llm/v1/chat` format) to your gateway. Kong injects the securely stored API keys and translates the payload into the native format for OpenAI or Anthropic. This prevents credential leakage into the codebase and centralizes all LLM traffic management.

---

## Recipe 4.2: Configuring Cross-Provider LLM Fallback Routing

### Problem
LLM providers frequently experience outages, rate limiting (HTTP 429), or severe latency spikes. If your primary provider fails, you need to seamlessly route the prompt to a secondary provider to maintain high availability.

### Solution
Combine the `ai-proxy` plugin with Kong's `upstreams` and `ai-proxy-advanced` (or fallback configurations) to create a resilient routing chain.

```yaml
_format_version: "3.0"
services:
  - name: resilient-llm-service
    url: http://localhost
    routes:
      - name: high-availability-chat
        paths:
          - /llm/chat
        plugins:
          - name: ai-proxy
            config:
              route_type: "llm/v1/chat"
              model:
                provider: "openai"
                name: "gpt-4"
              auth:
                header_name: "Authorization"
                header_value: "Bearer <OPENAI_API_KEY>"
              fallbacks:
                - model:
                    provider: "anthropic"
                    name: "claude-3-sonnet"
                  auth:
                    header_name: "x-api-key"
                    header_value: "<ANTHROPIC_API_KEY>"
                  trigger_on_status: [429, 500, 502, 503, 504]
```

### Discussion
In this recipe, developers send requests to `/llm/chat`. Kong attempts to proxy the request to OpenAI. If OpenAI responds with a rate limit (429) or a server error (500-level), Kong intercepts the failure, reformats the original request for Anthropic, and automatically retries. The client application remains completely unaware of the failure, receiving a successful response from the fallback model, ensuring zero downtime for your AI features.

---

## Recipe 4.3: Enforcing LLM Token Budgets and Rate Limits

### Problem
Standard HTTP rate limits (e.g., 10 requests per minute) are inadequate for AI APIs, where a single request could consume 10 tokens or 100,000 tokens. You need to enforce quotas based on actual computational cost (tokens).

### Solution
Implement the `ai-rate-limiting-advanced` plugin to govern traffic based on LLM token consumption.

```yaml
_format_version: "3.0"
services:
  - name: openai-service
    routes:
      - name: openai-chat
        paths:
          - /llm/openai
        plugins:
          - name: ai-proxy
            config: ... # Proxy config omitted for brevity
          - name: ai-rate-limiting-advanced
            config:
              limit_by: consumer
              strategy: redis
              redis:
                host: redis.internal
              tokens:
                prompt: 50000     # Max 50k prompt tokens per window
                completion: 10000 # Max 10k completion tokens per window
              window_size: 3600   # 1 hour window
```

### Discussion
This recipe calculates usage by parsing the token count returned in the LLM provider's response payload. It maintains an active counter in a centralized Redis cluster. By setting `limit_by: consumer`, Kong tracks usage per authenticated internal application or team. Once a consumer exceeds their token budget for the hour, Kong preemptively blocks further requests with a `429 Too Many Requests` status, protecting your enterprise from massive API bills.

---

## Recipe 4.4: Implementing Semantic Caching to Reduce LLM Calls

### Problem
Users frequently ask the same or semantically identical questions (e.g., "How do I reset my password?" vs. "What is the password reset process?"). Forwarding every request to the LLM is slow and expensive.

### Solution
Use the `ai-semantic-cache` plugin in conjunction with a vector database (like Redis Stack or Pinecone) to cache and retrieve responses based on the *meaning* of the prompt, not just exact string matches.

```yaml
_format_version: "3.0"
plugins:
  - name: ai-semantic-cache
    config:
      embeddings:
        provider: "openai"
        model: "text-embedding-ada-002"
        auth:
          header_name: "Authorization"
          header_value: "Bearer <OPENAI_API_KEY>"
      vectordb:
        provider: "redis"
        redis:
          host: redis-stack.internal
          port: 6379
      similarity_threshold: 0.92
      ttl: 86400 # Cache for 24 hours
```

### Discussion
Semantic caching drastically alters the performance profile of AI applications. When a prompt hits the gateway, Kong first calls the embeddings API to generate a vector representation of the prompt. It then queries the vector database. If a previously cached response exists with a similarity score higher than the `similarity_threshold` (e.g., 92% similar), Kong immediately returns the cached response. This reduces latency from seconds to milliseconds and completely eliminates the cost of the expensive LLM completion call.
