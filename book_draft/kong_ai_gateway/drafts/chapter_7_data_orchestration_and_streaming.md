# Chapter 7: Data Orchestration and Streaming

## Introduction

APIs are no longer limited to synchronous HTTP REST calls. Modern architectures rely heavily on event-driven models, data streaming, and asynchronous processing to achieve high throughput and decouple services. 

Kong Gateway excels as a bridge between synchronous web traffic and asynchronous message brokers. This chapter provides practical recipes for integrating Kong with Kafka and Solace, validating streaming schemas on the fly, and transforming traditional HTTP requests into event-driven workflows.

---

## Recipe 7.1: Producing Kafka Messages Securely Through Kong

### Problem
You have IoT devices, mobile apps, or web frontends that need to publish telemetry data or events directly to a Kafka cluster. Exposing Kafka brokers directly to the public internet is a massive security risk.

### Solution
Use Kong's `kafka-upstream` plugin to expose a secure HTTP REST endpoint that automatically translates inbound POST requests into Kafka messages.

```yaml
_format_version: "3.0"
services:
  - name: telemetry-service
    # The URL is a dummy; the plugin intercepts the request.
    url: http://localhost:8080 
    routes:
      - name: iot-ingest-route
        paths:
          - /ingest/telemetry
        plugins:
          - name: key-auth # Secure the endpoint
          - name: kafka-upstream
            config:
              bootstrap_servers:
                - name: kafka-broker-1.internal
                  port: 9092
                - name: kafka-broker-2.internal
                  port: 9092
              topic: "iot-telemetry-events"
              producer_request_acks: 1
              producer_request_timeout: 2000
              keepalive: 60000
```

### Discussion
By placing Kong in front of Kafka, you abstract the complex Kafka protocol (TCP/custom binary) from your client applications. IoT devices simply execute an authenticated HTTP POST request containing a JSON payload to `/ingest/telemetry`. Kong instantly publishes that payload to the `iot-telemetry-events` topic. This allows you to leverage Kong's robust security features (rate limiting, API keys, mTLS, IP restriction) to protect your message brokers from malicious traffic or DDoS attacks.

---

## Recipe 7.2: Enforcing and Validating Kafka Schemas on the Fly

### Problem
When clients push JSON data via HTTP to Kafka, bad or malformed payloads can poison downstream consumers, causing data pipelines to crash. You need to validate the structure of the incoming data *before* it hits the Kafka topic.

### Solution
Combine the `request-validator` plugin with the `kafka-upstream` plugin to ensure payloads match a predefined JSON schema.

```yaml
_format_version: "3.0"
services:
  - name: structured-events-service
    url: http://localhost:8080
    routes:
      - name: user-clickstream-route
        paths:
          - /events/clicks
        plugins:
          - name: request-validator
            config:
              body_schema: >
                {
                  "type": "object",
                  "properties": {
                    "user_id": {"type": "string"},
                    "button_clicked": {"type": "string"},
                    "timestamp": {"type": "integer"}
                  },
                  "required": ["user_id", "button_clicked", "timestamp"]
                }
              version: "draft4"
          - name: kafka-upstream
            config:
              bootstrap_servers:
                - name: kafka.internal:9092
              topic: "validated-clickstream"
```

### Discussion
The `request-validator` plugin executes *before* the request is handed over to the Kafka plugin. If an incoming POST request is missing the `timestamp` field or if `user_id` is an integer instead of a string, Kong rejects the request with a `400 Bad Request` and detailed error message. Only perfectly formed data is published to Kafka. This pattern enforces "Schema on Write," guaranteeing data hygiene for your downstream analytics and data warehousing systems.

---

## Recipe 7.3: Transforming Synchronous HTTP Calls into Asynchronous Events

### Problem
You have an intensive backend process (e.g., generating a massive PDF report or processing a video file). When a client requests this via a synchronous REST call, the connection times out waiting for the response.

### Solution
Transform the architecture. Have Kong accept the HTTP request, immediately return a `202 Accepted` to the client, and place the request payload onto a Solace or Kafka message queue for background processing.

*Using Kong's serverless functions to manipulate the response after queueing:*

```yaml
_format_version: "3.0"
services:
  - name: video-processing-service
    url: http://localhost
    routes:
      - name: video-upload-route
        paths:
          - /process/video
        plugins:
          - name: kafka-upstream
            config:
              bootstrap_servers:
                - name: kafka.internal:9092
              topic: "video-processing-queue"
          - name: post-function
            config:
              header_filter:
                - |
                  -- Override the Kafka plugin's default response
                  kong.response.set_status(202)
                  kong.response.set_header("Content-Type", "application/json")
              body_filter:
                - |
                  -- Provide a tracking response to the client
                  local tracking_id = kong.request.get_header("X-Request-ID") or "unknown"
                  local response = '{"status": "queued", "tracking_id": "' .. tracking_id .. '"}'
                  ngx.arg[1] = response
                  ngx.arg[2] = true
```

### Discussion
This recipe leverages Kong to facilitate an Event-Driven Architecture (EDA). The client posts the heavy payload. The `kafka-upstream` plugin places the job in the queue. Before the response returns to the client, the `post-function` plugin intercepts it, forces a `202 Accepted` status code, and injects a custom JSON body containing a `tracking_id`. The client application can now poll a separate status endpoint (or subscribe to a WebSocket) using that tracking ID, completely decoupling the web layer from the heavy backend workers.
