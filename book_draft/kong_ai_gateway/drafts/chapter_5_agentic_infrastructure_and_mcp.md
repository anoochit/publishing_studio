# Chapter 5: Agentic Infrastructure and MCP

## Introduction

As the tech industry transitions from isolated Large Language Models (LLMs) to autonomous AI agents, the infrastructure requirements change dramatically. AI agents do not just consume data; they interact with enterprise systems, execute workflows, and call APIs on behalf of users. To do this safely, they rely on the Model Context Protocol (MCP).

Kong serves as a critical bridge in this new architecture. By acting as an MCP registry and gateway, Kong can securely expose internal enterprise tools to local or cloud-based AI agents, ensuring that autonomous traffic is authenticated, governed, and observed.

---

## Recipe 5.1: Configuring Kong as an MCP Gateway

### Problem
You have internal enterprise APIs (like a Jira ticket creator or a Customer CRM lookup) that you want to expose as "tools" to an AI agent (e.g., an agent running locally via an IDE or a cloud-based assistant). You need a standardized way to proxy Model Context Protocol (MCP) requests to these endpoints.

### Solution
Configure Kong to act as the intermediary for MCP traffic. While MCP is often transported via WebSockets or Server-Sent Events (SSE) for local agents, enterprise deployments typically utilize HTTP/REST-based MCP servers.

```yaml
_format_version: "3.0"
services:
  - name: mcp-jira-tool
    url: http://jira-mcp-server.internal:8080
    routes:
      - name: mcp-jira-route
        paths:
          - /mcp/tools/jira
        protocols:
          - http
          - https
```

### Discussion
This recipe establishes the foundational routing for MCP. By routing `/mcp/tools/*` through Kong, you centralize the access point for AI agents. The AI agent connects to Kong's endpoint, thinking it is communicating directly with the MCP server. Kong handles the proxying, allowing you to decouple the agent's connection string from the actual internal network topology.

---

## Recipe 5.2: Applying Distinct Security Policies to Autonomous Agent Traffic

### Problem
AI agents can act unpredictably. A runaway loop or hallucination might cause an agent to spam an internal tool with thousands of API calls, taking down internal infrastructure. You must treat agent traffic differently from human user traffic.

### Solution
Create a dedicated "Consumer" group for AI agents and apply aggressive rate limiting and quota policies specifically to them, independent of human traffic limits.

1. Create a Consumer and Group:
```yaml
_format_version: "3.0"
consumers:
  - username: ai-support-agent
    custom_id: "agent-001"
    groups:
      - name: autonomous-agents

plugins:
  # Apply strict rate limiting only to the agent group
  - name: rate-limiting
    consumer_group: autonomous-agents
    config:
      second: 2      # Prevent aggressive looping
      minute: 20
      policy: local
```

2. Enforce Authentication (e.g., API Keys):
```yaml
_format_version: "3.0"
services:
  - name: mcp-crm-tool
    url: http://crm-mcp.internal:8080
    plugins:
      - name: key-auth
    routes:
      - name: mcp-crm-route
        paths:
          - /mcp/tools/crm
```

### Discussion
Because agents operate at compute speeds, standard human rate limits (e.g., 60 requests per minute) might be exhausted in less than a second during an agent loop, leading to cascading failures. By explicitly identifying traffic via the `ai-support-agent` consumer, you can clamp down on their request rate (e.g., max 2 per second). This ensures the agent is forced to "pause" and wait, protecting your internal CRM or databases from DDoS-like behavior caused by hallucinating code.

---

## Recipe 5.3: Registering and Managing Internal MCP Integrations

### Problem
As you deploy dozens of internal tools (Slack search, GitHub PR reviewers, Database query tools) formatted as MCP servers, managing which agents have access to which tools becomes chaotic. 

### Solution
Use Kong's Request Transformer and ACL (Access Control List) plugins to restrict tool execution based on the agent's identity.

```yaml
_format_version: "3.0"
services:
  - name: mcp-database-tool
    url: http://db-mcp.internal:8080
    plugins:
      - name: acl
        config:
          allow:
            - "data-science-agents" # Only this group can access the DB tool
          hide_groups_header: true
    routes:
      - name: mcp-db-route
        paths:
          - /mcp/tools/db
```

### Discussion
The `acl` plugin acts as an MCP registry governance layer. By defining allowed groups (e.g., `data-science-agents`), you ensure that a general-purpose customer service agent cannot accidentally execute tools that query sensitive production databases. This achieves a principle of least privilege for autonomous entities.

---

## Recipe 5.4: Securing Local AI Agent Connections to Enterprise APIs

### Problem
Developers run AI agents locally (e.g., in VS Code or via Claude Desktop) that need to securely reach into the enterprise network to access MCP servers. 

### Solution
Enforce strict mTLS and IP whitelisting at the Kong Gateway for the specific `/mcp/` routes, ensuring only corporately managed developer machines can connect.

```yaml
_format_version: "3.0"
services:
  - name: mcp-dev-tools
    url: http://internal-tools.internal:8080
    routes:
      - name: mcp-dev-route
        paths:
          - /mcp/tools/dev
        plugins:
          - name: mtls-auth
            config:
              ca_certificates: ["corp-ca-cert"]
              skip_consumer_lookup: false
          - name: ip-restriction
            config:
              allow:
                - "10.0.0.0/8" # Only allow Corporate VPN IP ranges
```

### Discussion
Local agents pose a massive security risk if they act as a conduit for exfiltrating data or exposing internal tools. By requiring mTLS, Kong guarantees that the connection is originating from a machine possessing a valid corporate certificate. Adding the IP restriction ensures that even if a certificate is compromised, the tool cannot be accessed from outside the corporate VPN. This securely bridges the gap between local AI development environments and sensitive enterprise MCP integrations.
