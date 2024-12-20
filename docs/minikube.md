让我解释一下 minikube registry 的工作原理：

1. **当你启用 minikube registry 时**：
   ```bash
   minikube addons enable registry
   ```
   这会在 minikube 集群中创建一个运行在端口 5000 的 registry 服务。

2. **`localhost:5000` 是必要的**，因为：
   - 这是 Docker registry 的标准端口
   - 这个前缀告诉 Kubernetes 从本地 registry 拉取镜像，而不是从 Docker Hub
   - 在 minikube 环境中，`localhost:5000` 会被正确解析到集群内的 registry 服务

验证和使用步骤：

```bash
# 1. 确保在 minikube 的 docker 环境中
eval $(minikube docker-env)

# 2. 构建你的镜像
docker build -t localhost:5000/backend:latest .

# 3. 推送到 minikube registry
docker push localhost:5000/backend:latest

# 4. 在 Deployment 中使用这个地址
spec:
  containers:
  - name: backend
    image: localhost:5000/backend:latest
```

如果不使用 `localhost:5000/`：
- Kubernetes 会默认尝试从 Docker Hub 拉取镜像
- 即使镜像在本地存在，也可能会尝试从远程拉取

这就是为什么需要这个前缀 - 它明确告诉 Kubernetes 从哪里获取镜像。这是 Docker registry 的标准做法，不管是使用私有 registry 还是 minikube 的内置 registry。
