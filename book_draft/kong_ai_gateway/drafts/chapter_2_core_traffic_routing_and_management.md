# Chapter 2: Core Traffic Routing and Management

## Introduction

At its heart, an API Gateway must efficiently direct inbound client requests to the correct backend services while protecting those services from being overwhelmed. In an era of polyglot microservices, legacy monoliths, and specialized AI backends, traffic routing and management are more critical than ever.

This chapter provides practical recipes for setting up precise routing rules, managing upstream load balancing, controlling traffic flow via rate limits, and building resilient systems using health checks and circuit breakers.

---

## Recipe 2.1: Creating Precise Path-Based and Header-Based Routes

### Problem
You need to route incoming traffic to different upstream services based not just on the URL path, but also on specific HTTP headers (like a tenant ID or client version).

### Solution
Configure a Kong Service and attach a Route that evaluates multiple conditions, such as `paths` and `headers`.

Using `decK` declarative YAML:

```yaml
_format_version: "3.0"
services:
  - name: billing-api-v1
    url: http://billing.internal.v1:8080
    routes:
      - name: billing-route-v1
        paths:
          - /api/billing
        headers:
          x-api-version:
            - "1.0"
        strip_path: true

  - name: billing-api-v2
    url: http://billing.internal.v2:8080
    routes:
      - name: billing-route-v2
        paths:
          - /api/billing
        headers:
          x-api-version:
            - "2.0"
        strip_path: true
```

### Discussion
Kong evaluates routes based on a specific priority sequence. By specifying both `paths` and `headers`, you create a logical `AND` condition. In this recipe, a request to `/api/billing` will be routed to the `v1` backend only if it includes the header `x-api-version: 1.0`. The `strip_path: true` directive ensures that `/api/billing` is removed from the URI before the request is forwarded to the upstream service.

---

## Recipe 2.2: Load Balancing Upstream Services

### Problem
You need to distribute inbound API traffic across multiple instances of a backend service to ensure high availability and prevent any single instance from becoming a bottleneck.

### Solution
Use Kong's `Upstream` and `Target` entities to configure internal load balancing.

```yaml
_format_version: "3.0"
upstreams:
  - name: user-service-upstream
    algorithm: round-robin

targets:
  - upstream: user-service-upstream
    target: 10.0.1.10:8000
    weight: 100
  - upstream: user-service-upstream
    target: 10.0.1.11:8000
    weight: 100
  - upstream: user-service-upstream
    target: 10.0.1.12:8000
    weight: 50

services:
  - name: user-service
    host: user-service-upstream # Points to the upstream name
    path: /
    routes:
      - name: user-route
        paths:
          - /users
```

### Discussion
By setting the `host` field of the Service to the name of the `Upstream`, Kong bypasses external DNS resolution and utilizes its internal ring-balancer. In this configuration, traffic is distributed using a `round-robin` algorithm. The `weight` parameter allows for proportional distribution; here, `10.0.1.12` will receive half as much traffic as the other two nodes. You can also utilize `least-connections` or `consistent-hashing` algorithms based on your use case.

---

## Recipe 2.3: Configuring Traditional Rate Limiting and Quotas

### Problem
You need to protect your backend APIs from brute-force attacks, abusive clients, and general traffic spikes by enforcing usage limits.

### Solution
Apply the `rate-limiting` plugin to a specific service or route.

```yaml
_format_version: "3.0"
services:
  - name: search-api
    url: http://search.internal:8080
    plugins:
      - name: rate-limiting
        config:
          minute: 60
          hour: 1000
          policy: local # Use 'redis' for multi-node DB-less clusters
          limit_by: ip
    routes:
      - name: search-route
        paths:
          - /search
```

### Discussion
This recipe restricts a single IP address to 60 requests per minute and 1,000 requests per hour. The `policy` defines where Kong stores the counter data. `local` stores it in the memory of the individual Kong node (good for single nodes or sticky-session setups). In a robust production environment with multiple Kong nodes, you should change `policy` to `redis` and provide your Redis host details so that limits are tracked cluster-wide.

---

## Recipe 2.4: Setting Up Active and Passive Health Checks & Circuit Breakers

### Problem
If an upstream server crashes or starts throwing 500 errors, you want Kong to automatically stop sending traffic to it (circuit breaking) and periodically check when it recovers (active health checking).

### Solution
Configure Health Checks on the `Upstream` object.

```yaml
_format_version: "3.0"
upstreams:
  - name: payment-upstream
    healthchecks:
      active:
        type: http
        http_path: /healthz
        timeout: 1
        concurrency: 10
        healthy:
          interval: 5
          successes: 2
          http_statuses: [200, 302]
        unhealthy:
          interval: 5
          tcp_failures: 2
          timeouts: 2
          http_failures: 2
          http_statuses: [429, 404, 500, 501, 502, 503, 504, 505]
      passive:
        healthy:
          successes: 3
        unhealthy:
          tcp_failures: 2
          timeouts: 2
          http_failures: 5
          http_statuses: [500, 502, 503, 504]

targets:
  - upstream: payment-upstream
    target: payment1.internal:80
  - upstream: payment-upstream
    target: payment2.internal:80
```

### Discussion
This recipe combines both passive and active health checks. 
* **Passive Checks (Circuit Breaker):** Kong monitors live proxy traffic. If `payment1.internal` returns five `500` errors in a row, Kong immediately marks the target as unhealthy and routes all traffic to `payment2.internal`.
* **Active Checks:** Kong proactively sends an HTTP GET request to the `/healthz` endpoint every 5 seconds. Once the failing node returns two consecutive `200 OK` responses, Kong automatically marks it as healthy and reinstates it in the load balancer ring.

---

## Recipe 2.5: Implementing Caching Strategies for Legacy REST APIs

### Problem
You have a slow, read-heavy legacy REST API that struggles under load. You need to cache responses at the Gateway level to reduce latency and backend utilization.

### Solution
Use the `proxy-cache` plugin to cache GET and HEAD responses based on the request URI.

```yaml
_format_version: "3.0"
services:
  - name: legacy-inventory-api
    url: http://inventory.legacy.internal:8080
    plugins:
      - name: proxy-cache
        config:
          strategy: memory # Or 'redis' for distributed caching
          request_method: ["GET", "HEAD"]
          response_code: [200, 301, 404]
          content_type: ["application/json"]
          cache_ttl: 300 # Cache for 5 minutes
          cache_control: false # Ignore upstream cache headers if necessary
    routes:
      - name: inventory-route
        paths:
          - /inventory
```

### Discussion
The `proxy-cache` plugin provides a massive performance boost by storing the responses of upstream requests. In this configuration, successful JSON responses are cached in memory for 5 minutes (300 seconds). Any subsequent request to the identical URI within that window will be served directly by Kong, dropping response times from hundreds of milliseconds to under 2 milliseconds, effectively shielding the legacy system from heavy read traffic.
