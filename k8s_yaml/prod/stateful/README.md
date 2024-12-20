# Kubernetes Demo Project

This project demonstrates a simple web application deployment on Kubernetes (Minikube), featuring Redis for hit counting and MySQL for user management.

## Prerequisites

- Minikube
- kubectl
- Docker
- Local Docker registry (for development)

## Development Setup

1. Start Minikube and enable required addons:
```bash
minikube start
minikube addons enable ingress
minikube addons enable registry
```

2. Point shell to Minikube's Docker daemon:
```bash
eval $(minikube docker-env)
```

## Building and Deploying Changes

### When you modify backend code:

1. Build and deploy new backend image:
```bash
cd apps/backend
eval $(minikube docker-env)  # Make sure we're using Minikube's Docker
docker build -t backend:v3 .  # No need for localhost:5000 prefix

# Update deployment
kubectl set image deployment/backend backend=backend:v3 -n dev
```

### When you modify frontend code:

1. Build and deploy new frontend image:
```bash
cd apps/frontend
eval $(minikube docker-env)  # Make sure we're using Minikube's Docker
docker build -t frontend:v3 .  # No need for localhost:5000 prefix

# Update deployment
kubectl set image deployment/frontend frontend=frontend:v3 -n dev
```

### Quick Development Tips:

1. Watch pod status during update:
```bash
kubectl get pods -n dev -w
```

2. Check deployment rollout status:
```bash
# For backend
kubectl rollout status deployment/backend -n dev

# For frontend
kubectl rollout status deployment/frontend -n dev
```

3. Rollback if needed:
```bash
# For backend
kubectl rollout undo deployment/backend -n dev

# For frontend
kubectl rollout undo deployment/frontend -n dev
```

## Initial Deployment

Deploy all components:
```bash
# Create namespace
kubectl create namespace dev

# Apply all configurations
kubectl apply -f k8s_yaml/configmap/
kubectl apply -f k8s_yaml/stateful/
kubectl apply -f k8s_yaml/deploy/
kubectl apply -f k8s_yaml/service/
kubectl apply -f k8s_yaml/ingress/
```

## Accessing the Application

1. Get Minikube IP:
```bash
minikube ip
```

2. Add to /etc/hosts:
```bash
# Add this line to /etc/hosts
<minikube-ip> k8s-demo.info
```

3. Access the application:
- Frontend: http://k8s-demo.info
- Backend API: http://k8s-demo.info/api

## Monitoring

Access monitoring tools:
- Prometheus: http://k8s-demo.info/prometheus
- Grafana: http://k8s-demo.info/grafana

## Useful Commands

```bash
# View pods status
kubectl get pods -n dev

# View logs
kubectl logs -n dev <pod-name>

# Shell into pod
kubectl exec -it -n dev <pod-name> -- /bin/sh

# Restart deployment
kubectl rollout restart -n dev deployment/<deployment-name>

# View ingress status
kubectl get ingress -n dev
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace dev

# Stop Minikube
minikube stop
```

## Project Structure

```
.
├── apps/
│   ├── backend/         # FastAPI backend application
│   └── frontend/        # HTML/JS frontend application
├── k8s_yaml/
│   ├── configmap/       # ConfigMaps (e.g., Prometheus config)
│   ├── deploy/          # Deployment configurations
│   ├── ingress/        # Ingress rules
│   ├── service/        # Service configurations
│   └── stateful/       # StatefulSet configurations (MySQL)
└── docs/               # Documentation
```

## Troubleshooting

1. If images are not pulling:
   - Ensure you're using the correct registry address
   - Check if you're connected to Minikube's Docker daemon
   - Verify image tags in deployment files

2. If services are not accessible:
   - Verify ingress is enabled: `minikube addons list`
   - Check ingress status: `kubectl get ingress -n dev`
   - Ensure /etc/hosts is configured correctly

3. If pods are crashing:
   - Check logs: `kubectl logs -n dev <pod-name>`
   - Describe pod: `kubectl describe pod -n dev <pod-name>`
```
