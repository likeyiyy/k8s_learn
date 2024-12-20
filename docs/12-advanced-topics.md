# 12. 高级主题

## Helm 包管理
### 什么是 Helm？
Helm 是 Kubernetes 的包管理工具，类似于 Linux 中的 apt 或 yum。它可以：
- 简化应用部署
- 管理应用版本
- 共享应用配置
- 简化应用更新

### Helm 基本概念
1. Chart：应用打包格式
2. Repository：Chart 仓库
3. Release：Chart 的运行实例
4. Values：配置值

### Chart 结构示例
```bash
mychart/
  Chart.yaml          # Chart 的元数据
  values.yaml         # 默认配置值
  charts/             # 依赖的子 charts
  templates/          # 模板文件
    deployment.yaml
    service.yaml
    _helpers.tpl      # 通用模板定义
  .helmignore         # 类似 .gitignore
```

### 常用操作
```bash
# 添加仓库
helm repo add stable https://charts.helm.sh/stable

# 搜索 Chart
helm search repo nginx

# 安装 Chart
helm install my-release stable/nginx

# 查看安装状态
helm list

# 升级 Release
helm upgrade my-release stable/nginx --values new-values.yaml

# 回滚 Release
helm rollback my-release 1
```

## 自动扩缩容（HPA）
### 高级配置
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: advanced-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  - type: Resource
    resource:
      name: memory
      target:
        type: AverageValue
        averageValue: 500Mi
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

### 自定义指标
```yaml
apiVersion: custom.metrics.k8s.io/v1beta1
kind: MetricDefinition
metadata:
  name: queue-length
spec:
  query: "sum(rabbitmq_queue_messages)"
```

## 调度器进阶
### 自定义调度器
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-scheduler-pod
spec:
  schedulerName: my-scheduler
  containers:
  - name: container
    image: nginx
```

### 优先级和抢占
```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
description: "This priority class should be used for critical service pods only."
```

### 污点和容忍
```yaml
# 添加污点
kubectl taint nodes node1 key=value:NoSchedule

# Pod 容忍配置
apiVersion: v1
kind: Pod
metadata:
  name: tolerant-pod
spec:
  tolerations:
  - key: "key"
    operator: "Equal"
    value: "value"
    effect: "NoSchedule"
```

## 高级存储配置
### 动态卷配置
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp2
  fsType: ext4
reclaimPolicy: Delete
allowVolumeExpansion: true
```

### 卷快照
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: data-snapshot
spec:
  volumeSnapshotClassName: csi-hostpath-snapclass
  source:
    persistentVolumeClaimName: data-pvc
```

## 高级网络配置
### 服务网格集成
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews-route
spec:
  hosts:
  - reviews
  http:
  - match:
    - headers:
        end-user:
          exact: jason
    route:
    - destination:
        host: reviews
        subset: v2
  - route:
    - destination:
        host: reviews
        subset: v1
```

### 高级网络策略
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: advanced-policy
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          purpose: production
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 80
  egress:
  - to:
    - ipBlock:
        cidr: 10.0.0.0/24
```

## 故障排查进阶
### 调试技巧
```bash
# 使用临时调试容器
kubectl debug -it pod/mypod --image=busybox

# 网络调试
kubectl run test-${RANDOM} -it --rm --image=nicolaka/netshoot -- /bin/bash

# 查看事件流
kubectl get events --watch

# 查看审计日志
kubectl logs kube-apiserver-minikube -n kube-system | grep audit
```

### 性能分析
```bash
# 使用 perf 工具
kubectl exec pod/mypod -- perf record -F 99 -p 1 -g -- sleep 30

# 资源使用分析
kubectl top pod --containers=true

# 查看 etcd 性能
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 endpoint status
```

## 最佳实践
### 1. 资源管理
- 使用资源配额和限制
- 实施优先级和抢占策略
- 合理规划存储
- 监控资源使用

### 2. 高可用配置
- 使用多副本部署
- 配置 Pod 反亲和性
- 实施存储备份
- 配置服务网格

### 3. 安全加固
- 实施网络策略
- 配置 Pod 安全策略
- 使用服务账号
- 加密敏感数据

### 4. 性能优化
- 优化调度策略
- 配置资源限制
- 使用本地存储
- 优化网络配置 