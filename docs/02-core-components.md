# 2. K8s 核心组件详解

## Pod
### 基本概念
- Pod 是 K8s 中最小的可部署单元
- 共享网络命名空间、存储卷和其他资源
- 支持一个或多个紧密耦合的容器

### Pod 配置示例
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
  labels:
    app: web
spec:
  containers:
  - name: web
    image: nginx:1.14
    ports:
    - containerPort: 80
  - name: log-collector
    image: fluentd:v1.0
    volumeMounts:
    - name: logs
      mountPath: /var/log
  volumes:
  - name: logs
    emptyDir: {}
```

### 实践操作
```bash
# 创建 Pod
kubectl apply -f pod.yaml

# 查看 Pod 中的容器
kubectl get pods multi-container-pod -o jsonpath='{.spec.containers[*].name}'

# 进入特定容器
kubectl exec -it multi-container-pod -c web -- /bin/bash

# 查看容器日志
kubectl logs multi-container-pod -c log-collector
```

## ReplicaSet
### 基本概念
- 确保指定数量的 Pod 副本在运行
- 使用标签选择器管理 Pod
- 支持水平扩展和自动替换

### ReplicaSet 配置示例
```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: web
        image: nginx:1.14
```

### 实践操作
```bash
# 创建 ReplicaSet
kubectl apply -f replicaset.yaml

# 扩展副本数
kubectl scale replicaset frontend --replicas=5

# 查看 Pod 分布
kubectl get pods -l app=frontend -o wide
```

## Deployment
### 基本概念
- 提供声明式更新
- 支持滚动更新和回滚
- 管理应用的发布过程

### Deployment 配置示例
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.14
        ports:
        - containerPort: 80
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 实践操作
```bash
# 部署应用
kubectl apply -f deployment.yaml

# 查看部署状态
kubectl rollout status deployment/nginx-deployment

# 更新镜像
kubectl set image deployment/nginx-deployment nginx=nginx:1.15

# 查看更新历史
kubectl rollout history deployment/nginx-deployment

# 回滚到上一版本
kubectl rollout undo deployment/nginx-deployment
```

## Service
### 基本概念
- 提供稳定的服务发现和负载均衡
- 支持多种类型：ClusterIP、NodePort、LoadBalancer
- 使用标签选择器关联 Pod

### Service 配置示例
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
```

### 实践操作
```bash
# 创建 Service
kubectl apply -f service.yaml

# 查看 Service 详情
kubectl describe service my-service

# 查看 Endpoints
kubectl get endpoints my-service

# 测试服务访问
curl $(minikube ip):30080
```

## 常见问题与解决方案
### Pod 相关问题
1. Pod 间通信问题
```bash
# 检查网络策略
kubectl get networkpolicies

# 测试 Pod 间连接
kubectl exec -it pod1 -- wget -qO- http://pod2-service
```

2. 存储卷问题
```bash
# 检查 PV 状态
kubectl get pv,pvc

# 查看存储卷详情
kubectl describe pv <pv-name>
```

### Deployment 相关问题
1. 更新失败
```bash
# 检查更新状态
kubectl rollout status deployment/my-deployment

# 查看失败原因
kubectl describe deployment my-deployment

# 暂停有问题的更新
kubectl rollout pause deployment/my-deployment
```

2. 扩缩容问题
```bash
# 检查资源使用情况
kubectl top nodes
kubectl top pods

# 查看 HPA 状态
kubectl get hpa
```

### Service 相关问题
1. 服务发现问题
```bash
# 验证 DNS 解析
kubectl run -it --rm debug --image=busybox -- nslookup my-service

# 检查 Service 选择器
kubectl get pods --show-labels
```

2. 负载均衡问题
```bash
# 查看 Service 分发情况
kubectl get endpoints my-service

# 测试负载均衡
for i in {1..10}; do curl $(minikube ip):30080; done
```

## 最佳实践
### 配置管理
- 使用 ConfigMap 存储配置
- 使用 Secret 存储敏感信息
- 实施资源限制和请求
- 设置合适的探针

### 高可用部署
- 使用多副本
- 配置反亲和性
- 实施滚动更新策略
- 设置 Pod 干扰预算

### 监控和日志
- 配置资源监控
- 设置日志收集
- 实施告警规则
- 定期审计