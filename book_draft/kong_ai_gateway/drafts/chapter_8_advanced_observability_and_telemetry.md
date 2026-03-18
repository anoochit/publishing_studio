# Chapter 8: Advanced Observability and Telemetry

## Introduction

As API infrastructures grow complex, spanning microservices and multiple AI provider endpoints, blind spots become costly. Observability in an API Gateway is no longer just about HTTP status codes; it's about distributed tracing, latency profiling, and, crucially, tracking the specific costs and token consumption of generative AI models.

This chapter details recipes for achieving deep observability in Kong. We will integrate standard telemetry tools like Prometheus and OpenTelemetry, and then dive into specialized monitoring for AI traffic, ensuring you can track `ai_model_usage`, manage multi-LLM performance, and build effective dashboards.

---

## Recipe 8.1: Hooking Kong into Prometheus and Grafana for Traffic Metrics

### Problem
You need real-time visibility into the performance, throughput, and error rates of your APIs, but you want to use industry-standard tools rather than proprietary dashboards.

### Solution
Enable the `prometheus` plugin in Kong to expose a metrics endpoint, and configure a Prometheus server to scrape it.

1. Enable the Prometheus plugin globally via `decK`:
```yaml
_format_version: "3.0"
plugins:
  - name: prometheus
    config:
      per_consumer: true
      status_code_metrics: true
      latency_metrics: true
      bandwidth_metrics: true
      upstream_health_metrics: true
```

2. Expose the metrics endpoint. In your Kong configuration (e.g., via environment variables or `kong.conf`), ensure the status API is active:
```bash
KONG_STATUS_LISTEN="0.0.0.0:8100"
```

3. Configure your Prometheus `prometheus.yml` to scrape the endpoint:
```yaml
scrape_configs:
  - job_name: 'kong-gateway'
    static_configs:
      - targets: ['<KONG_IP>:8100']
```

### Discussion
The `prometheus` plugin aggregates crucial metrics in memory and exposes them at the `/metrics` endpoint. By enabling `per_consumer` and `latency_metrics`, you allow Prometheus to ingest highly granular data (e.g., tracking the 99th percentile latency of a specific API consumer). You can then import the official Kong dashboard into Grafana to instantly visualize request rates, bandwidth, and upstream health status.

---

## Recipe 8.2: Setting Up Distributed Tracing with OpenTelemetry

### Problem
Requests are traversing the API Gateway, hitting a microservice, and then fanning out to databases or third-party APIs. When a request is slow, you need to pinpoint exactly where the bottleneck occurred across this distributed system.

### Solution
Use Kong's `opentelemetry` plugin to generate and propagate W3C Trace Context headers to your backend services and export spans to an OTLP-compatible backend (like Jaeger, Honeycomb, or Datadog).

```yaml
_format_version: "3.0"
plugins:
  - name: opentelemetry
    config:
      endpoint: "http://otel-collector.internal:4318/v1/traces"
      resource_attributes:
        service.name: "kong-api-gateway"
        deployment.environment: "production"
      header_type: "w3c"
      sampling_rate: 0.1 # Sample 10% of traffic
```

### Discussion
The `opentelemetry` plugin turns Kong into an active participant in your distributed tracing architecture. Kong generates a `traceparent` header (following W3C standards) when a request enters the gateway and forwards it to the upstream service. Simultaneously, it sends a span representing its own internal processing time and the upstream latency to the configured OTLP endpoint. The `sampling_rate` of 0.1 ensures that high-volume APIs don't overwhelm your tracing backend while still providing statistically significant performance data.

---

## Recipe 8.3: Tracking AI Token Consumption and Cost Reporting

### Problem
Generative AI APIs (like OpenAI or Anthropic) charge per token. If multiple teams or applications use Kong to route to these LLMs, you need to monitor token consumption, attribute costs, and prevent budget overruns.

### Solution
Leverage Kong's AI gateway plugins alongside the `prometheus` plugin to track the `ai_model_usage` metric.

*Note: This assumes you have already configured the `ai-proxy` plugin for your routes (covered in Chapter 4).*

1. Ensure your `prometheus` plugin is enabled globally as seen in Recipe 8.1.
2. Configure the `ai-proxy` to ensure token usage is extracted from the provider's response:
```yaml
_format_version: "3.0"
services:
  - name: openai-service
    url: https://api.openai.com
    routes:
      - name: openai-chat
        paths:
          - /v1/chat/completions
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
```

### Discussion
When Kong's `ai-proxy` handles the LLM response, it parses the payload (specifically the `usage` object returned by OpenAI/Anthropic) to extract `prompt_tokens` and `completion_tokens`. The Prometheus plugin automatically captures this and exposes it via metrics like:
`kong_ai_tokens_total{provider="openai", model="gpt-4", type="prompt"}`.
You can use PromQL queries to calculate daily costs by multiplying the token counts by the provider's specific rate card, allowing for chargebacks to individual consumer IDs.

---

## Recipe 8.4: Building Customized Dashboards for Multi-LLM Performance

### Problem
You are load-balancing traffic across multiple LLM providers (e.g., Azure OpenAI and AWS Bedrock) for redundancy. You need a centralized dashboard to compare their latency, error rates, and token generation speed.

### Solution
Build a custom Grafana dashboard using PromQL queries against the metrics generated by Kong's `ai-proxy` and `prometheus` integrations.

**Key PromQL Queries for your Dashboard:**

1. **LLM Request Latency (99th Percentile by Provider):**
```promql
histogram_quantile(0.99, sum(rate(kong_latency_bucket{service=~".*ai.*"}[5m])) by (le, service))
```

2. **Total Tokens Generated per Minute by Model:**
```promql
sum(rate(kong_ai_tokens_total{type="completion"}[1m])) by (model)
```

3. **Provider Fallback/Error Rate:**
```promql
sum(rate(kong_http_status{service=~".*ai.*", code=~"5.."}[5m])) / sum(rate(kong_http_status{service=~".*ai.*"}[5m])) * 100
```

### Discussion
These queries form the backbone of an "AI Gateway Command Center." Because LLM providers frequently experience latency spikes or rate-limit clients (returning 429s or 500s), monitoring the 99th percentile latency and error rates *per provider* is crucial. If the dashboard shows AWS Bedrock consistently returning tokens faster or with fewer errors than Azure OpenAI during a specific time window, platform architects can adjust Kong's routing weights to optimize user experience and cost.
