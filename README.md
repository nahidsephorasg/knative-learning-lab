# Knative Simple-API Architecture & Request Flow

## Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL CLIENT                                     │
│                     (Browser/curl with Host header)                              │
└─────────────────────────────────┬───────────────────────────────────────────────┘
                                  │
                                  │ HTTP Request
                                  │ Host: simple-api.default.example.com
                                  │ http://192.168.18.110:32482/health
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         KUBERNETES NODE (Worker)                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │              NodePort: 32482 → Port 80 (kourier service)                  │  │
│  └───────────────────────────────┬───────────────────────────────────────────┘  │
│                                  │                                               │
│  ┌───────────────────────────────▼───────────────────────────────────────────┐  │
│  │                    KOURIER GATEWAY (Ingress)                              │  │
│  │                    Pod: 3scale-kourier-gateway                            │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │  1. Receives request on port 80                                     │  │  │
│  │  │  2. Reads Host header: simple-api.default.example.com               │  │  │
│  │  │  3. Routes to correct Knative Service based on hostname             │  │  │
│  │  │  4. Forwards to Activator or directly to Pod                        │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────┬───────────────────────────────────────────┘  │
│                                  │                                               │
│         ┌────────────────────────┼────────────────────────┐                     │
│         │                        │                        │                     │
│         │ (If scaled to zero)    │ (If pods running)      │                     │
│         ▼                        ▼                        │                     │
│  ┌──────────────────┐    ┌──────────────────┐            │                     │
│  │   ACTIVATOR      │    │  Direct to Pod   │            │                     │
│  │   (Wakes pods)   │    │                  │            │                     │
│  └────────┬─────────┘    └────────┬─────────┘            │                     │
│           │                       │                       │                     │
│           └───────────────────────┼───────────────────────┘                     │
│                                   │                                             │
│                                   ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │              KUBERNETES SERVICE: simple-api-00002                       │   │
│  │              ClusterIP: 10.106.46.31                                    │   │
│  │              (Load balances across pods)                                │   │
│  └─────────────────────────────┬───────────────────────────────────────────┘   │
│                                │                                                │
│                                │ Distributes to Pods                            │
│                                │                                                │
│         ┌──────────────────────┼──────────────────────┐                        │
│         │                      │                      │                        │
│         ▼                      ▼                      ▼                        │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐             │
│  │   POD 1         │   │   POD 2         │   │   POD 3         │             │
│  │ ┌─────────────┐ │   │ ┌─────────────┐ │   │ ┌─────────────┐ │             │
│  │ │ queue-proxy │ │   │ │ queue-proxy │ │   │ │ queue-proxy │ │             │
│  │ │  Port: 8012 │ │   │ │  Port: 8012 │ │   │ │  Port: 8012 │ │             │
│  │ │             │ │   │ │             │ │   │ │             │ │             │
│  │ │ 1. Receives │ │   │ │ 1. Receives │ │   │ │ 1. Receives │ │             │
│  │ │ 2. Metrics  │ │   │ │ 2. Metrics  │ │   │ │ 2. Metrics  │ │             │
│  │ │ 3. Forwards │ │   │ │ 3. Forwards │ │   │ │ 3. Forwards │ │             │
│  │ └──────┬──────┘ │   │ └──────┬──────┘ │   │ └──────┬──────┘ │             │
│  │        │        │   │        │        │   │        │        │             │
│  │        │ localhost:8080       │ localhost:8080       │ localhost:8080      │
│  │        ▼        │   │        ▼        │   │        ▼        │             │
│  │ ┌─────────────┐ │   │ ┌─────────────┐ │   │ ┌─────────────┐ │             │
│  │ │user-container│   │ │user-container│   │ │user-container│ │             │
│  │ │             │ │   │ │             │ │   │ │             │ │             │
│  │ │  Flask App  │ │   │ │  Flask App  │ │   │ │  Flask App  │ │             │
│  │ │  Port: 8080 │ │   │ │  Port: 8080 │ │   │ │  Port: 8080 │ │             │
│  │ │             │ │   │ │             │ │   │ │             │ │             │
│  │ │ - /         │ │   │ │ - /         │ │   │ │ - /         │ │             │
│  │ │ - /health   │ │   │ │ - /health   │ │   │ │ - /health   │ │             │
│  │ │ - /info     │ │   │ │ - /info     │ │   │ │ - /info     │ │             │
│  │ │ - /echo     │ │   │ │ - /echo     │ │   │ │ - /echo     │ │             │
│  │ └─────────────┘ │   │ └─────────────┘ │   │ └─────────────┘ │             │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                      KNATIVE CONTROL PLANE (knative-serving)                     │
│                                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐              │
│  │   CONTROLLER     │  │   AUTOSCALER     │  │   WEBHOOK        │              │
│  │                  │  │                  │  │                  │              │
│  │ - Manages        │  │ - Monitors       │  │ - Validates      │              │
│  │   Revisions      │  │   metrics        │  │   configs        │              │
│  │ - Creates        │  │ - Scales pods    │  │ - Mutates        │              │
│  │   Deployments    │  │   up/down        │  │   resources      │              │
│  │ - Updates        │  │ - Target: 5      │  │                  │              │
│  │   Routes         │  │   concurrent     │  │                  │              │
│  │                  │  │ - Min: 1 pod     │  │                  │              │
│  │                  │  │ - Max: 100 pods  │  │                  │              │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         CILIUM (CNI - Network Layer)                             │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  - Provides pod networking (10.0.x.x)                                    │   │
│  │  - Handles service routing                                               │   │
│  │  - Network policies (if enabled)                                         │   │
│  │  - Replaces kube-proxy                                                   │   │
│  │  - VXLAN tunneling for cross-node communication                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Request Flow

### Step-by-Step Request Journey

#### 1. **External Request Arrives**
```bash
curl -H "Host: simple-api.default.example.com" http://192.168.18.110:32482/health
```

**What happens:**
- Client sends HTTP request to node IP (192.168.18.110) on NodePort (32482)
- Host header contains the service hostname
- Request hits any Kubernetes node in the cluster

---

#### 2. **NodePort Routes to Kourier Service**
```
NodePort 32482 → ClusterIP Service "kourier" (port 80)
```

**What happens:**
- Kubernetes NodePort mapping forwards traffic to Kourier service
- Service type: NodePort
- External port 32482 maps to internal port 80
- Load balanced across Kourier gateway pods

---

#### 3. **Kourier Gateway (Envoy Proxy)**
**Location:** `knative-serving` namespace
**Pod:** `3scale-kourier-gateway-xxxxx`

**Responsibilities:**
1. **Host-based routing**: Reads `Host` header
2. **Service discovery**: Looks up which Knative service matches the hostname
3. **Traffic routing**: 
   - If pods exist → Route directly to service
   - If scaled to zero → Route to Activator first
4. **SSL termination** (if configured)
5. **Load balancing** across pods

**Configuration:**
```yaml
# Kourier reads from Knative Ingress resources
# Maps: simple-api.default.example.com → simple-api-00002 service
```

---

#### 4a. **Activator (When Scaled to Zero)**
**Location:** `knative-serving` namespace
**Pod:** `activator-xxxxx`

**Activated when:**
- Service has `minScale: "0"` and no pods running
- First request after idle period

**What it does:**
1. Receives request from Kourier
2. Signals autoscaler to create pods
3. Queues requests while waiting for pods
4. Forwards queued requests once pods are ready
5. Hands off to direct routing once stable

**Metrics:**
- Tracks cold start time
- Reports to autoscaler

---

#### 4b. **Direct Routing (When Pods Running)**
**When:**
- At least 1 pod is ready
- Service has `minScale: "1"` or higher

**What happens:**
- Kourier routes directly to Kubernetes Service
- Service load balances across available pods
- Faster path (no activator overhead)

---

#### 5. **Kubernetes Service (ClusterIP)**
**Service:** `simple-api-00002`
**Type:** ClusterIP
**IP:** `10.106.46.31`

**What it does:**
1. Receives traffic from Kourier or Activator
2. Load balances across healthy pods
3. Uses endpoint list to track available pods
4. Distributes requests round-robin or based on algorithm

**Endpoints:**
```bash
kubectl get endpoints simple-api-00002
# Lists all pod IPs that are Ready
```

---

#### 6. **Pod - queue-proxy Container**
**Container:** `queue-proxy` (Knative sidecar)
**Port:** 8012 (receives external traffic)

**Responsibilities:**
1. **Request handling:**
   - Receives HTTP request on port 8012
   - Forwards to user-container on localhost:8080

2. **Metrics collection:**
   - Counts concurrent requests
   - Measures request latency
   - Reports to autoscaler every few seconds

3. **Health probing:**
   - Handles readiness checks
   - Reports pod health to Kubernetes

4. **Request queuing:**
   - Queues requests if container is busy
   - Implements concurrency limits

5. **Tracing & Logging:**
   - Adds trace headers
   - Logs request metadata

**Metrics sent to autoscaler:**
```
- Current concurrency: 3 requests
- Target concurrency: 5 requests/pod
- Pod ready status: true
```

---

#### 7. **Pod - user-container (Your Flask App)**
**Container:** `user-container`
**Image:** `rudder9290/knative-serving:v2`
**Port:** 8080

**Application:**
- Flask application with Gunicorn
- 2 worker processes
- Listening on `0.0.0.0:8080`

**Request handling:**
```python
1. Gunicorn receives request on port 8080
2. Routes to Flask endpoint (e.g., /health)
3. Executes endpoint logic
4. Logs: "Health check endpoint accessed"
5. Returns JSON response: {"status": "healthy"}
6. Response flows back through queue-proxy
```

**Endpoints:**
- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /info` - App information
- `GET|POST /echo` - Echo request data

---

#### 8. **Response Flow (Reverse)**
```
Flask App → queue-proxy → K8s Service → Kourier → NodePort → Client
```

**Response headers added:**
- `server: envoy` (from Kourier)
- `x-envoy-upstream-service-time` (latency)
- Custom headers from Flask app

---

## Autoscaling Flow

### Continuous Monitoring

```
┌──────────────────────────────────────────────────────────────┐
│                    AUTOSCALING LOOP                          │
│                                                              │
│  1. queue-proxy collects metrics                            │
│     ↓                                                        │
│  2. Sends to autoscaler every 2 seconds                     │
│     ↓                                                        │
│  3. Autoscaler calculates desired pods                      │
│     Formula: desiredPods = concurrency / target             │
│     Example: 25 requests / 5 target = 5 pods                │
│     ↓                                                        │
│  4. Updates PodAutoscaler resource                          │
│     ↓                                                        │
│  5. Controller scales Deployment                            │
│     ↓                                                        │
│  6. New pods created/deleted                                │
│     ↓                                                        │
│  7. Endpoints updated                                       │
│     ↓                                                        │
│  8. Traffic distributed to new pods                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Scale Up Example
**Current state:** 1 pod, 5 target concurrency
**Incoming traffic:** 25 concurrent requests

```
1. queue-proxy reports: 25 concurrent requests to pod-1
2. Autoscaler calculates: 25 / 5 = 5 pods needed
3. Controller creates 4 more pods
4. Pods start (user-container + queue-proxy)
5. Readiness probes pass (/health returns 200)
6. Endpoints updated with new pod IPs
7. Kourier starts routing to all 5 pods
8. Load distributed: ~5 requests per pod
```

### Scale Down Example
**Current state:** 5 pods, no traffic for 60 seconds
**minScale:** 1

```
1. queue-proxy reports: 0 concurrent requests
2. Autoscaler waits for stable window (60s)
3. Calculates: 0 / 5 = 0 pods, but minScale=1
4. Controller scales down to 1 pod
5. 4 pods terminated gracefully
6. Endpoints updated
7. All traffic goes to remaining 1 pod
```

---

## Component Details

### Knative Serving Components

#### 1. **Controller**
- **Namespace:** knative-serving
- **Function:** Reconciliation loop
- **Manages:**
  - Configuration → Revision
  - Revision → Deployment
  - Route → Ingress
  - Service → Configuration + Route

#### 2. **Autoscaler**
- **Namespace:** knative-serving
- **Metrics:** Concurrency-based (default)
- **Algorithm:** KPA (Knative Pod Autoscaler)
- **Scale decisions:** Every 2 seconds
- **Panic mode:** Rapid scale-up if needed

#### 3. **Webhook**
- **Namespace:** knative-serving
- **Validates:** Service, Route, Configuration specs
- **Mutates:** Sets defaults, injects values
- **Example mutations:**
  - Adds queue-proxy sidecar
  - Sets PORT environment variable
  - Configures probes

#### 4. **Activator**
- **Namespace:** knative-serving
- **Handles:** Scale-from-zero
- **Buffers:** Requests during cold start
- **Reports:** Metrics when no pods available

---

### Network Components

#### 1. **Kourier (Ingress)**
- **Type:** Envoy-based ingress
- **Alternative to:** Istio, Contour
- **Lightweight:** Minimal overhead
- **Features:**
  - HTTP/1.1, HTTP/2, gRPC
  - Host-based routing
  - Path-based routing
  - Retries, timeouts

#### 2. **Cilium (CNI)**
- **Replaces:** kube-proxy
- **Provides:**
  - Pod-to-pod networking
  - Service load balancing
  - Network policies
  - eBPF-based datapath
- **Tunnel:** VXLAN (for multi-node)

---

## Configuration Files

### Your Knative Service
```yaml
autoscaling.knative.dev/minScale: "1"
autoscaling.knative.dev/maxScale: "100"
autoscaling.knative.dev/target: "5"
autoscaling.knative.dev/metric: "concurrency"
autoscaling.knative.dev/target-utilization-percentage: "70"
```

**Meaning:**
- Always keep at least 1 pod
- Scale up to maximum 100 pods
- Target 5 concurrent requests per pod
- Scale when 70% of target is reached (3.5 requests)

---

## Key Kubernetes Resources Created

```bash
# Knative Service (your YAML)
kubectl get ksvc simple-api

# Revision (version of your service)
kubectl get revision simple-api-00002

# Deployment (manages pods)
kubectl get deployment simple-api-00002-deployment

# Service (ClusterIP - load balancing)
kubectl get svc simple-api-00002

# PodAutoscaler (autoscaling config)
kubectl get podautoscaler simple-api-00002

# Route (traffic routing)
kubectl get route simple-api

# Ingress (Kourier routing rules)
kubectl get ingress -n knative-serving
```

---

## Summary

**Request Path:**
```
Client → NodePort:32482 → Kourier → (Activator) → K8s Service → queue-proxy → Flask App
```

**Response Path:**
```
Flask App → queue-proxy → K8s Service → Kourier → NodePort:32482 → Client
```

**Key Features:**
✅ Automatic scaling (0 to 100 pods)
✅ Blue-green deployments (revision-based)
✅ Traffic splitting (between revisions)
✅ Built-in observability (metrics, traces)
✅ Simplified developer experience
✅ Host-based routing
✅ Scale-to-zero capability
