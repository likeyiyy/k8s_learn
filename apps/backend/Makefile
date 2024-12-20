# Variables
IMAGE_NAME = localhost:5000/backend
VERSION ?= latest
NAMESPACE = dev

# Get the current git commit hash
COMMIT_HASH = $(shell git rev-parse --short HEAD 2>/dev/null || echo 'dev')

.PHONY: build push patch deploy test clean

# Default target
all: build push deploy

# Build the Docker image
build:
	eval $$(minikube docker-env) && \
	docker build -t $(IMAGE_NAME):$(VERSION) .

# Push to Minikube's registry
push:
	eval $$(minikube docker-env) && \
	docker push $(IMAGE_NAME):$(VERSION)

# Patch the deployment with new image
patch:
	kubectl set image deployment/backend backend=$(IMAGE_NAME):$(VERSION) -n $(NAMESPACE)
	kubectl rollout status deployment/backend -n $(NAMESPACE)

# Quick patch: build and update deployment
quick-patch: build push patch

# Deploy all k8s resources
deploy:
	kubectl apply -f ../../k8s_yaml/deploy/backend-deployment.yaml -n $(NAMESPACE)

# Run tests (if you have any)
test:
	python -m pytest

# Clean up
clean:
	docker rmi $(IMAGE_NAME):$(VERSION) || true

# Watch pod logs
logs:
	kubectl logs -f -l app=$(IMAGE_NAME) -n $(NAMESPACE)

# Get pod status
status:
	kubectl get pods -l app=$(IMAGE_NAME) -n $(NAMESPACE)

# Restart deployment
restart:
	kubectl rollout restart deployment/backend -n $(NAMESPACE)

# Version with current timestamp
patch-timestamp:
	$(eval VERSION := $(shell date +%Y%m%d-%H%M%S))
	@make quick-patch

# Version with commit hash
patch-commit:
	$(eval VERSION := $(COMMIT_HASH))
	@make quick-patch
