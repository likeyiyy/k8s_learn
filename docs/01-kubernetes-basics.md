# 1. Kubernetes 基础概念

## 什么是 Kubernetes
### 定义与核心特征
- Kubernetes 是一个可移植、可扩展的开源平台，用于管理容器化的工作负载和服务
- 它遵循声明式配置和自动化理念
- 拥有庞大的生态系统，服务、支持和工具广泛可用

### 发展历史
- 源自 Google 内部的 Borg 系统
- 2014 年开源，由 CNCF 托管
- 目前已成为容器编排的事实标准

### 应用场景示例
- 大规模电商平台的弹性伸缩
- 微服务架构的服务治理
- 持续集成/持续部署（CI/CD）流水线
- 多云和混合云部署

## K8s 的优势和特性
### 核心优势
1. 自动化部署和扩展
   - 自动化容器部署和复制
   - 根据需求自动扩缩容
   
2. 自愈能力
   - 自动替换失败的容器
   - 自动重启不响应健康检查的容器
   
3. 服务发现和负载均衡
   - 自动分配 IP 地址和 DNS 名称
   - 自动分发网络流量

### 实际应用示例
- 场景一：应用升级
  ```yaml
  # 部署示例
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: nginx-deployment
  spec:
    replicas: 3
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
          image: nginx:1.14.2
  ```

- 场景二：自动扩缩容
  ```yaml
  # HPA示例
  apiVersion: autoscaling/v1
  kind: HorizontalPodAutoscaler
  metadata:
    name: nginx-hpa
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: nginx-deployment
    minReplicas: 1
    maxReplicas: 10
    targetCPUUtilizationPercentage: 50
  ```

## K8s 架构概述
### 控制平面组件（Control Plane）
1. kube-apiserver
   - 集群的统一入口
   - REST API 的核心服务
   - 所有组件间通信的中枢

2. etcd
   - 分布式键值存储系统
   - 存储集群所有配置和状态
   - 保证数据一致性和可用性

3. kube-scheduler
   - 监控新创建的 Pod
   - 选择最佳节点进行分配
   - 考虑资源需求、硬件限制等因素

4. kube-controller-manager
   - 运行各种控制器进程
   - 确保期望状态的实现
   - 处理集群常规任务

### Node 组件
1. kubelet
   - 确保容器运行在 Pod 中
   - 维护容器生命周期
   - 执行控制平面下发的任务

2. kube-proxy
   - 维护节点网络规则
   - 实现 Service 概念
   - 处理集群内外网络通信

3. 容器运行时
   - 如 Docker、containerd
   - 负责容器的实际运行
   - 管理容器镜像和资源

### 架构示意
```ascii
    +-------------------+
    |   Control Plane   |
    |  +-----------+   |
    |  | API Server|   |
    |  +-----------+   |
    |  +-----------+   |
    |  |   etcd    |   |
    |  +-----------+   |
    +-------------------+
            |
    +-------v-----------+
    |      Nodes        |
    | +--------------+  |
    | |   kubelet    |  |
    | +--------------+  |
    | | kube-proxy   |  |
    | +--------------+  |
    +-------------------+
```

## 核心概念实践
### 基础概念
1. Pod
   - 定义：K8s 中最小的可部署单元
   - 特点：可包含一个或多个容器
   - 示例：Web应用 + 日志收集容器

2. Node
   - 定义：工作负载节点
   - 职责：运行 Pod
   - 管理：计算资源和容器运行时

3. Namespace
   - 定义：资源隔离单元
   - 用途：多租户资源隔离
   - 默认值：default、kube-system等

### 实践练习
1. 创建第一个 Pod
```bash
kubectl run nginx --image=nginx
```

2. 查看 Pod 状态
```bash
kubectl get pods
kubectl describe pod nginx
```

3. 访问应用
```bash
kubectl port-forward pod/nginx 8080:80
```

## 小结与实践
### 关键要点
- Kubernetes 的基本概念和架构
- 核心组件的功能和关系
- 基础资源对象的使用

### 动手练习
1. 安装 minikube
```bash
# MacOS 安装
brew install minikube

# Linux 安装
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 启动集群
minikube start --driver=docker

# 验证安装
minikube status
kubectl cluster-info
```

2. 部署示例应用
```bash
# 创建 Deployment
kubectl create deployment hello-node --image=k8s.gcr.io/echoserver:1.4

# 查看 Deployment
kubectl get deployments

# 创建 Service
kubectl expose deployment hello-node --type=LoadBalancer --port=8080

# 查看 Service
kubectl get services

# 在 minikube 中访问服务
minikube service hello-node
```

3. 实践基本操作命令
```bash
# 查看 Pod 详情
kubectl get pods -o wide

# 查看 Pod 日志
kubectl logs <pod-name>

# 进入 Pod 容器
kubectl exec -it <pod-name> -- /bin/bash

# 扩展副本数
kubectl scale deployment hello-node --replicas=3

# 更新镜像
kubectl set image deployment/hello-node hello-node=k8s.gcr.io/echoserver:1.5
```

4. 观察组件间的交互
```bash
# 查看事件
kubectl get events --sort-by=.metadata.creationTimestamp

# 查看组件状态
kubectl get componentstatuses

# 查看节点信息
kubectl describe node minikube
```

### 常见问题解答
#### Pod 启动失败的排查步骤
1. 检查 Pod 状态
```bash
kubectl get pod <pod-name> -o wide
kubectl describe pod <pod-name>
```

2. 常见问题及解决方案
- ImagePullBackOff
  - 原因：镜像拉取失败
  - 解决：检查镜像名称、仓库权限、网络连接
  ```bash
  # 查看详细错误信息
  kubectl describe pod <pod-name> | grep -A 10 Events
  ```

- CrashLoopBackOff
  - 原因：容器启动失败或持续崩溃
  - 解决：检查容器日志、应用配置
  ```bash
  # 查看容器日志
  kubectl logs <pod-name> --previous
  ```

- Pending 状态
  - 原因：资源不足或调度失败
  - 解决：检查节点资源、调度策略
  ```bash
  # 查看节点资源使用情况
  kubectl describe nodes
  ```

#### 服务访问的常见问题
1. Service 无法访问
```bash
# 检查 Service 配置
kubectl describe service <service-name>

# 检查 Endpoints
kubectl get endpoints <service-name>

# 验证 Service DNS
kubectl run -it --rm debug --image=busybox -- nslookup <service-name>
```

2. 网络连接问题
```bash
# 检查网络策略
kubectl get networkpolicies

# 测试网络连接
kubectl run -it --rm debug --image=nicolaka/netshoot -- bash
```

#### 配置更新的最佳实践
1. 使用声明式配置
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

2. 配置变更管理
```bash
# 应用配置更新
kubectl apply -f deployment.yaml

# 查看更新历史
kubectl rollout history deployment/my-app

# 回滚到上一版本
kubectl rollout undo deployment/my-app
```

3. 配置最佳实践
- 使用 ConfigMap 和 Secret 管理配置
- 实施资源限制和请求
- 设置健康检查和就绪探针
- 使用标签和注解进行资源管理
