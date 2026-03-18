# Chapter 1: Kong Gateway Fundamentals & GitOps

## Introduction

As enterprises move from monolithic architectures to microservices and, more recently, agentic AI ecosystems, the API Gateway has evolved from a simple reverse proxy to a critical infrastructure control plane. Managing this control plane manually is no longer viable. 

This chapter introduces the fundamental deployment strategies for Kong Gateway and demonstrates how to treat your API infrastructure as code using GitOps principles and `decK` (Declarative Configuration for Kong). We will explore recipes for both DB-less and database-backed deployments, followed by building robust, zero-downtime CI/CD pipelines.

---

## Recipe 1.1: Running Kong in DB-less Mode using Docker

### Problem
You need a lightweight, fast, and immutable API gateway deployment for testing, edge nodes, or a simplified production environment without the operational overhead of managing a database.

### Solution
Deploy Kong in DB-less mode using Docker. In this mode, Kong stores its configuration entirely in memory, loaded from a declarative YAML file.

1. Create a declarative configuration file named `kong.yml`:
```yaml
_format_version: "3.0"
services:
  - name: example-service
    url: http://httpbin.org
    routes:
      - name: example-route
        paths:
          - /mock
```

2. Start the Kong Docker container, mounting the configuration file:
```bash
docker run -d --name kong-dbless \
  --network=host \
  -e "KONG_DATABASE=off" \
  -e "KONG_DECLARATIVE_CONFIG=/kong/declarative/kong.yml" \
  -e "KONG_PROXY_ACCESS_LOG=/dev/stdout" \
  -e "KONG_ADMIN_ACCESS_LOG=/dev/stdout" \
  -e "KONG_PROXY_ERROR_LOG=/dev/stderr" \
  -e "KONG_ADMIN_ERROR_LOG=/dev/stderr" \
  -e "KONG_ADMIN_LISTEN=0.0.0.0:8001, 0.0.0.0:8444 ssl" \
  -v $(pwd)/kong.yml:/kong/declarative/kong.yml \
  kong:3.10-ubuntu
```

### Discussion
DB-less mode is an ideal match for GitOps and CI/CD workflows. Because the gateway state is entirely defined by `kong.yml`, you eliminate configuration drift. If the container restarts, it simply reloads the YAML file. However, keep in mind that certain plugins requiring centralized state (like standard rate-limiting without Redis) behave differently in DB-less mode, as counters are kept locally in the node's memory.

---

## Recipe 1.2: Bootstrapping a Kong Database (PostgreSQL)

### Problem
You need to deploy Kong with a centralized configuration store to support dynamic clustering, API creation via the Admin API without restarting nodes, or plugins that require central coordination (like complex rate limiting or OAuth2).

### Solution
Deploy Kong using a PostgreSQL database to store its configuration.

1. Start a PostgreSQL container:
```bash
docker run -d --name kong-database \
  --network=kong-net \
  -p 5432:5432 \
  -e "POSTGRES_USER=kong" \
  -e "POSTGRES_DB=kong" \
  -e "POSTGRES_PASSWORD=kongpass" \
  postgres:13
```

2. Run the Kong database migration (bootstrap) command:
```bash
docker run --rm \
  --network=kong-net \
  -e "KONG_DATABASE=postgres" \
  -e "KONG_PG_HOST=kong-database" \
  -e "KONG_PG_PASSWORD=kongpass" \
  kong:3.10-ubuntu kong migrations bootstrap
```

3. Start the Kong Gateway node:
```bash
docker run -d --name kong-gateway \
  --network=kong-net \
  -e "KONG_DATABASE=postgres" \
  -e "KONG_PG_HOST=kong-database" \
  -e "KONG_PG_PASSWORD=kongpass" \
  -e "KONG_PROXY_ACCESS_LOG=/dev/stdout" \
  -e "KONG_ADMIN_ACCESS_LOG=/dev/stdout" \
  -e "KONG_PROXY_ERROR_LOG=/dev/stderr" \
  -e "KONG_ADMIN_ERROR_LOG=/dev/stderr" \
  -e "KONG_ADMIN_LISTEN=0.0.0.0:8001, 0.0.0.0:8444 ssl" \
  -p 8000:8000 \
  -p 8443:8443 \
  -p 8001:8001 \
  -p 8444:8444 \
  kong:3.10-ubuntu
```

### Discussion
Using a database enables a traditional multi-node deployment pattern. You can spin up multiple Kong containers pointing to the same PostgreSQL instance. When a configuration change is made via the Admin API on one node, Kong's caching mechanism ensures the other nodes invalidate their local cache and fetch the new configuration.

---

## Recipe 1.3: Configuration as Code with decK

### Problem
Manually configuring Kong via the Admin API or Kong Manager leads to untracked changes, configuration drift, and makes disaster recovery difficult. 

### Solution
Use `decK` (Declarative Configuration for Kong) to manage Kong's state declaratively, allowing you to version control your API infrastructure.

1. **Dump** the current state of your Kong gateway into a YAML file:
```bash
deck gateway dump --kong-addr http://localhost:8001 -o kong_state.yaml
```

2. Edit the `kong_state.yaml` to add a new service or route.

3. **Diff** the configuration to see what changes will be applied:
```bash
deck gateway diff -s kong_state.yaml --kong-addr http://localhost:8001
```

4. **Sync** the changes to the gateway:
```bash
deck gateway sync -s kong_state.yaml --kong-addr http://localhost:8001
```

### Discussion
`decK` is the bridge between traditional DB-backed Kong instances and the GitOps methodology. The `sync` command ensures that the gateway precisely matches the state defined in your YAML file—meaning it will create new entities, update changed ones, and **delete** entities that exist in the gateway but not in the YAML. This strictly enforces the YAML file as the single source of truth.

---

## Recipe 1.4: Implementing Declarative Configurations in a CI/CD Pipeline

### Problem
You want to automate the process of applying Kong configurations across different environments (dev, staging, prod) using GitHub Actions (or another CI tool).

### Solution
Create a CI/CD pipeline that validates the `decK` file on pull requests and syncs it on merges to the main branch.

*Example GitHub Actions Workflow (`.github/workflows/kong-deploy.yml`):*

```yaml
name: Kong GitOps Pipeline
on:
  push:
    branches:
      - main
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install decK
        run: |
          curl -sL https://github.com/Kong/deck/releases/download/v1.38.0/deck_1.38.0_linux_amd64.tar.gz -o deck.tar.gz
          tar -xf deck.tar.gz -C /tmp
          sudo cp /tmp/deck /usr/local/bin/
      - name: Validate decK YAML
        run: deck gateway validate -s kong/config.yaml

  deploy-prod:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install decK
        run: |
          curl -sL https://github.com/Kong/deck/releases/download/v1.38.0/deck_1.38.0_linux_amd64.tar.gz -o deck.tar.gz
          tar -xf deck.tar.gz -C /tmp
          sudo cp /tmp/deck /usr/local/bin/
      - name: decK Sync to Production
        env:
          KONG_ADDR: ${{ secrets.KONG_PROD_URL }}
          KONG_HEADERS: "Kong-Admin-Token:${{ secrets.KONG_ADMIN_TOKEN }}"
        run: |
          deck gateway sync -s kong/config.yaml --kong-addr $KONG_ADDR
```

### Discussion
This pipeline ensures that your Kong configuration is rigorously tested and validated before hitting production. Developers submit Pull Requests changing `kong/config.yaml`. The `validate` job ensures the YAML is syntactically correct. Once merged, the `deploy-prod` job automatically syncs the configuration to the live gateway, enforcing strict access controls via secrets.

---

## Recipe 1.5: Achieving Automated Zero-Downtime Deployments

### Problem
When applying massive configuration changes to Kong under heavy traffic, you want to guarantee zero dropped requests or latency spikes.

### Solution
Combine `decK` with Kong's native configuration reloading architecture, or use a Blue/Green deployment strategy at the infrastructure level.

**Approach 1: Using decK's native behavior**
When you run `deck gateway sync`, Kong does *not* restart the underlying Nginx worker processes immediately in a disruptive way. Instead, it leverages OpenResty and shared memory zones to update routing tables dynamically. For standard updates, simple syncing is already virtually zero-downtime.

**Approach 2: Canary/Blue-Green at the Gateway Layer (for major architectural changes)**
1. Spin up a new cluster of Kong nodes (Green) pointing to a new database or utilizing a new DB-less config.
2. Run your CI/CD pipeline to deploy the new configuration to the Green cluster.
3. Update your external Load Balancer (e.g., AWS ALB or HAProxy) to route a small percentage of traffic (e.g., 5%) to the Green cluster.
4. Monitor Error Rates and Latency.
5. If stable, shift 100% of traffic to the Green cluster and decommission the Blue cluster.

### Discussion
While Kong is designed to handle live configuration updates seamlessly, major version upgrades or foundational changes to core security plugins should be handled via Blue/Green deployments. Treating your API Gateway nodes as ephemeral infrastructure ensures that rollback is as simple as flipping the Load Balancer routing rule back to the old cluster.
