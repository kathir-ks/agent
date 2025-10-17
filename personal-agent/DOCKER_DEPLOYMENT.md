# Docker Deployment Guide

This guide explains how to deploy the Personal Agent application using Docker.

## Prerequisites

- Docker (20.10 or higher)
- Docker Compose (2.0 or higher)
- GEMINI_API_KEY (Google Gemini API key)

## Quick Start

### 1. Set up environment variables

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

Edit `.env` and set your `GEMINI_API_KEY`:

```bash
GEMINI_API_KEY=your_actual_api_key_here
```

### 2. Build and run with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at `http://localhost:8000`

## Manual Docker Build

If you prefer to build and run Docker manually:

### Build the image

```bash
docker build -t personal-agent:latest .
```

### Run with Docker

```bash
# Start Redis first
docker run -d --name personal-agent-redis \
  -p 6379:6379 \
  redis:7-alpine

# Run the application
docker run -d --name personal-agent-web \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e GEMINI_API_KEY=your_api_key_here \
  -e REDIS_HOST=redis \
  --link personal-agent-redis:redis \
  personal-agent:latest
```

## Configuration

### Environment Variables

All configuration can be set via environment variables in the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (required) | Google Gemini API key |
| `DEFAULT_MODEL` | `gemini-flash-2/0` | Gemini model to use |
| `TEMPERATURE` | `0.7` | Model temperature (0.0-1.0) |
| `MAX_TOKENS` | `2048` | Maximum tokens in response |
| `WEB_HOST` | `0.0.0.0` | Web server host |
| `WEB_PORT` | `8000` | Web server port |
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database number |
| `DATABASE_URL` | `sqlite+aiosqlite:///./personal_agent.db` | Database connection string |
| `AGENT_NAME` | `Personal Agent` | Agent display name |
| `CHECK_INTERVAL_MINUTES` | `30` | Content discovery interval |

### Volumes

The Docker Compose setup includes persistent volumes:

- `./data` - User profiles and interaction history
- `./personal_agent.db` - SQLite database
- `redis_data` - Redis persistence

## Deployment Options

### Deploy to Cloud Services

#### Docker Hub

```bash
# Tag your image
docker tag personal-agent:latest yourusername/personal-agent:latest

# Push to Docker Hub
docker push yourusername/personal-agent:latest
```

#### AWS ECS

```bash
# Install AWS CLI and configure credentials
aws configure

# Create ECR repository
aws ecr create-repository --repository-name personal-agent

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag personal-agent:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/personal-agent:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/personal-agent:latest
```

#### Google Cloud Run

```bash
# Install gcloud CLI and configure
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build and push to GCR
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/personal-agent

# Deploy to Cloud Run
gcloud run deploy personal-agent \
  --image gcr.io/YOUR_PROJECT_ID/personal-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_api_key
```

#### Azure Container Instances

```bash
# Login to Azure
az login

# Create resource group
az group create --name personal-agent-rg --location eastus

# Create container registry
az acr create --resource-group personal-agent-rg \
  --name personalagentacr --sku Basic

# Push image to ACR
az acr build --registry personalagentacr \
  --image personal-agent:latest .

# Deploy to ACI
az container create \
  --resource-group personal-agent-rg \
  --name personal-agent \
  --image personalagentacr.azurecr.io/personal-agent:latest \
  --dns-name-label personal-agent-unique \
  --ports 8000 \
  --environment-variables GEMINI_API_KEY=your_api_key
```

#### Kubernetes

Create a `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: personal-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: personal-agent
  template:
    metadata:
      labels:
        app: personal-agent
    spec:
      containers:
      - name: personal-agent
        image: personal-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: personal-agent-secrets
              key: gemini-api-key
        - name: REDIS_HOST
          value: redis-service
---
apiVersion: v1
kind: Service
metadata:
  name: personal-agent-service
spec:
  type: LoadBalancer
  selector:
    app: personal-agent
  ports:
  - port: 80
    targetPort: 8000
```

Deploy:

```bash
kubectl create secret generic personal-agent-secrets \
  --from-literal=gemini-api-key=your_api_key

kubectl apply -f k8s-deployment.yaml
```

## Health Checks

The application includes health check endpoints:

- HTTP: `GET /api/status/default`
- Docker health check runs every 30 seconds

## Troubleshooting

### Check logs

```bash
# Docker Compose
docker-compose logs -f web
docker-compose logs -f redis

# Docker
docker logs personal-agent-web
```

### Access container shell

```bash
# Docker Compose
docker-compose exec web /bin/bash

# Docker
docker exec -it personal-agent-web /bin/bash
```

### Common Issues

1. **API Key Error**: Make sure `GEMINI_API_KEY` is set in `.env`
2. **Redis Connection**: Check that Redis is running and accessible
3. **Port Conflict**: Change port in `docker-compose.yml` if 8000 is in use
4. **Data Persistence**: Ensure volumes are properly mounted

## Production Recommendations

1. **Use secrets management** - Don't commit `.env` file
2. **Set up monitoring** - Use Prometheus/Grafana or cloud monitoring
3. **Enable HTTPS** - Use reverse proxy (nginx/traefik) with SSL
4. **Database backup** - Regularly backup `data/` and `personal_agent.db`
5. **Resource limits** - Set memory/CPU limits in production
6. **Logging** - Configure centralized logging (ELK, CloudWatch, etc.)
7. **Scaling** - For high traffic, consider load balancing and Redis clustering

## Security Notes

- Never commit `.env` file with real API keys
- Use Docker secrets in production
- Run containers with non-root user in production
- Keep images updated with security patches
- Use private registries for proprietary deployments

## Support

For issues or questions, please refer to the main README.md or open an issue on GitHub.
