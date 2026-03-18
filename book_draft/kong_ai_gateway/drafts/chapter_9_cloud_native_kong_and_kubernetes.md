# Chapter 9: Cloud-Native Kong and Kubernetes

## Introduction

Modern applications are overwhelmingly deployed in containerized environments, with Kubernetes serving as the defacto orchestration standard. Managing an API Gateway within Kubernetes requires a paradigm shift: configurations must align with Kubernetes native constructs (like Ingress or Gateway API), and the gateway itself must scale dynamically with cluster traffic.

This chapter explores deploying and managing Kong natively in Kubernetes using the Kong Ingress Controller (KIC). We will cover practical recipes for installation, declarative configuration via Custom Resource Definitions (CRDs), and strategies for auto-scaling your edge deployments.

---

## Recipe 9.1: Deploying Kong as a Kubernetes Ingress Controller (KIC)

### Problem
You want to expose multiple microservices running inside a Kubernetes cluster to external traffic using a single load balancer, while managing the routing rules via Kubernetes-native manifests.

### Solution
Deploy the Kong Ingress Controller (KIC) using Helm. KIC runs alongside the Kong Gateway, watching for Kubernetes Ingress resources and automatically translating them into Kong configuration.

1. Add the Kong Helm repository:
```bash
helm repo add kong https://charts.konghq.com
helm repo update
```

2. Install KIC in DB-less mode in the `kong` namespace:
```bash
helm install kong kong/ingress -n kong --create-namespace \
  --set ingressController.installCRDs=false \
  --set gateway.proxy.type=LoadBalancer
```

*(Note: CRDs are often installed separately or pre-packaged; verify chart instructions for your specific environment).*

3. Create a standard Kubernetes Ingress resource:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
  namespace: default
  annotations:
    kubernetes.io/ingress.class: kong
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /billing
        pathType: Prefix
        backend:
          service:
            name: billing-service
            port:
              number: 80
```

### Discussion
By setting `kubernetes.io/ingress.class: kong`, KIC intercepts this standard Ingress resource and configures the underlying Kong Gateway to route traffic matching `api.example.com/billing` to the internal `billing-service`. This allows developers to define external routing alongside their application deployments, tightly coupling API exposure to the application lifecycle. DB-less mode is highly recommended here, as KIC acts as the control plane, holding the state in memory.

---

## Recipe 9.2: Managing Kong Configurations via Kubernetes CRDs

### Problem
Standard Kubernetes Ingress resources are too limited. They don't support Kong's advanced features, like attaching rate-limiting plugins, configuring advanced load-balancing algorithms, or defining intricate routing rules based on headers.

### Solution
Use Kong's Custom Resource Definitions (CRDs) specifically the `KongPlugin` and `KongIngress` resources.

1. Define a `KongPlugin` resource for rate limiting:
```yaml
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: rate-limit-by-ip
  namespace: default
config:
  minute: 100
  limit_by: ip
  policy: local
plugin: rate-limiting
```

2. Attach the plugin to an Ingress or Service via annotations:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: secure-api-ingress
  namespace: default
  annotations:
    kubernetes.io/ingress.class: kong
    konghq.com/plugins: rate-limit-by-ip
spec:
  rules:
  - host: secure.example.com
    http:
      paths:
      - path: /data
        pathType: Prefix
        backend:
          service:
            name: data-service
            port:
              number: 8080
```

### Discussion
CRDs bridge the gap between basic Kubernetes networking and enterprise API management. By defining `KongPlugin` objects, you treat API policies as Kubernetes-native objects that can be managed via `kubectl`, GitOps tools like ArgoCD, or Helm. Annotating the Ingress tells KIC to apply the rate-limiting configuration specifically to the `/data` route, ensuring high customization without leaving the Kubernetes ecosystem.

---

## Recipe 9.3: Managing Shared vs. Dedicated Gateway Deployments

### Problem
In a large cluster, a single "shared" API Gateway might become a noisy neighbor bottleneck, or present security risks if different teams require distinct Gateway policies (e.g., internal APIs vs. public-facing APIs).

### Solution
Deploy multiple instances of the Kong Ingress Controller, isolating them using distinct Ingress Classes.

1. Deploy the "Public" KIC (Helm values):
```yaml
ingressController:
  ingressClass: kong-public
gateway:
  proxy:
    type: LoadBalancer
```

2. Deploy the "Internal" KIC (Helm values):
```yaml
ingressController:
  ingressClass: kong-internal
gateway:
  proxy:
    type: ClusterIP # Only accessible within the cluster or via VPN
```

### Discussion
Using dedicated deployments based on `ingressClass` provides strict isolation. Public services use `kubernetes.io/ingress.class: kong-public`, traversing a gateway tuned with stringent WAF, rate limits, and bot protection. Internal microservices use `kong-internal`, traversing a gateway optimized for low latency, internal mTLS, and high throughput. This architectural pattern reduces blast radius and simplifies compliance auditing.

---

## Recipe 9.4: Auto-Scaling Kong Deployments Based on Traffic

### Problem
API traffic is highly unpredictable. A static number of Kong Gateway replicas will either be over-provisioned (wasting money) or under-provisioned (dropping traffic during spikes).

### Solution
Configure a Horizontal Pod Autoscaler (HPA) attached to the Kong deployment, scaling based on CPU or custom metrics.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: kong-gateway-hpa
  namespace: kong
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: kong-gateway
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Discussion
Because Kong runs on Nginx and OpenResty, it is highly CPU-bound rather than memory-bound. Scaling on CPU utilization (e.g., triggering a scale-out when average utilization hits 70%) is highly effective. As KIC provisions new Pods, they instantly fetch their configuration from the Kubernetes API server (or their attached database) and register with the cloud provider's Load Balancer, seamlessly handling the traffic surge.
