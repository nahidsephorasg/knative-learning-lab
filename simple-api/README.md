# Simple API - Knative Service

A simple Flask-based REST API for deploying to Knative Serving.

## Endpoints

- `GET /` - Welcome message with available endpoints
- `GET /health` - Health check endpoint
- `GET /info` - Application information
- `GET|POST /echo` - Echo request data back

## Build and Deploy

### 1. Build Docker Image

```bash
# Build the image
docker build -t simple-api:v1 .

# Tag for your registry (replace with your registry)
docker tag simple-api:v1 your-registry/simple-api:v1

# Push to registry
docker push your-registry/simple-api:v1
```

### 2. Update Knative Service YAML

Edit `knative-service.yaml` and replace `your-registry/simple-api:v1` with your actual image registry path.

### 3. Deploy to Knative

```bash
kubectl apply -f knative-service.yaml
```

### 4. Verify Deployment

```bash
# Check the Knative service
kubectl get ksvc simple-api

# Get the service URL
kubectl get ksvc simple-api -o jsonpath='{.status.url}'
```

### 5. Test the API

```bash
# Get the URL
URL=$(kubectl get ksvc simple-api -o jsonpath='{.status.url}')

# Test endpoints
curl $URL/
curl $URL/health
curl $URL/info
curl -X POST $URL/echo -H "Content-Type: application/json" -d '{"message": "Hello Knative!"}'
```

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# Test locally
curl http://localhost:8080/
curl http://localhost:8080/health
```

## Auto-scaling

The service is configured to:
- Scale to zero when idle (minScale: 0)
- Scale up to 10 replicas (maxScale: 10)
- Target 100 concurrent requests per pod

Watch the pods scale:
```bash
kubectl get pods -w
```

Send traffic and observe scaling behavior.
