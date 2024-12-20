# 4. Pod 详解

## Pod 的生命周期
### Pod 阶段（Phase）
- Pending：Pod 已创建但尚未完全运行
  - 正在下载镜像
  - 等待调度
  - 资源不足

- Running：Pod 已经绑定到节点，所有容器都已创建
  - 至少有一个容器正在运行
  - 或者正在重启
  - 或者正在启动

- Succeeded：所有容器都已成功终止
  - Pod 中的所有容器都已经成功执行
  - 不会重启

- Failed：所有容器都已终止，至少有一个容器失败
  - 容器以非零状态退出
  - 被系统终止

- Unknown：无法获取 Pod 状态
  - 通常是节点通信问题

### 容器状态
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: lifecycle-demo
spec:
  containers:
  - name: lifecycle-demo-container
    image: nginx
    lifecycle:
      postStart:
        exec:
          command: ["/bin/sh", "-c", "echo Hello from postStart handler > /usr/share/message"]
      preStop:
        exec:
          command: ["/bin/sh","-c","nginx -s quit; while killall -0 nginx; do sleep 1; done"]
```

### 重启策略
- Always：默认策略，总是重启
- OnFailure：只���失败时重启
- Never：从不重启

## 容器设计模式

### 为什么需要容器设计模式？
在 Kubernetes 中，Pod 是最小的部署单元，可以包含多个容器。通过合理使用容器设计模式，我们可以：
- 保持应用程序容器的简单性和单一职责
- 解耦应用程序的不同功能
- 提高系统的可维护性和可扩展性
- 重用通用的功能组件

### Sidecar 模式
#### 概念
Sidecar 模式是在应用容器旁边运行一个辅助容器，以提供额外的功能支持。就像摩托车旁边的边车一样，搭载着支持性功能。

#### 使用场景
- 日志收集：主容器专注于业务逻辑，Sidecar 负责日志收集和转发
- 代理容器：处理与主应用通信的代理请求
- 监控采集：收集应用指标和监控数据

#### 示例配置
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-pod
spec:
  containers:
  - name: main-container
    image: nginx
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  - name: sidecar-container
    image: busybox
    command: ["sh", "-c", "tail -f /var/log/nginx/access.log"]
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx
  volumes:
  - name: shared-logs
    emptyDir: {}
```

### Ambassador 模式
#### 概念
Ambassador 模式��在应用容器旁边运行一个代理容器，该代理容器处理网络连接的代理。就像外交大使一样，处理与外界的所有通信。

#### 使用场景
- 数据库代理：简化应用程序的数据库连接
- 服务分片：处理分布式服务的路由
- 连接池管理：管理和优化连接池

#### 示例配置
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ambassador-pod
spec:
  containers:
  - name: main-app
    image: my-app
    env:
    - name: REDIS_HOST
      value: localhost    # 应用连接本地代理
  - name: redis-ambassador
    image: redis-proxy    # 代理容器处理实际的 Redis 连接
    ports:
    - containerPort: 6379
```

### Adapter 模式
#### 概念
Adapter 模式是在应用容器旁边运行一个转换容器，用于统一数据格式或接口。就像电源适配器一样，将一种格式转换为另一种格式。

#### 使用场景
- 日志标准化：统一不同应用的日志格式
- 监控适配：转换应用指标为统一的监控格式
- 接口转换：适配不同的 API 版本或协议

#### 示例配置
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: adapter-pod
spec:
  containers:
  - name: app-container
    image: app
    volumeMounts:
    - name: app-logs
      mountPath: /var/log/app
  - name: log-adapter
    image: log-adapter    # 转换日志格式
    volumeMounts:
    - name: app-logs
      mountPath: /var/log/app
  volumes:
  - name: app-logs
    emptyDir: {}
```

### 设计模式的选择建议
1. 使用 Sidecar 模式当：
   - 需要扩展主应用功能
   - 主应用和辅助功能有明确的责任划分
   - 需要解耦辅助功能的维护和更新

2. 使用 Ambassador 模式当：
   - 需要简化应用的网络访问
   - 需要在应用和外部服务之间添加额外的功能
   - 需要统一管理服务连接

3. 使用 Adapter 模式当：
   - 需要标准化输出格式
   - 需要适配不同的接口规范
   - 需要转换数据格式

### 最佳实践
- 保持容器职责单一
- 合理使用共享卷进行容器间通信
- 注意容器间的依赖关系
- 考虑资源分配和性能影响

## 健康检查

### 为什么需要健康检查？
在分布式系统中，应用程序可能会因为各种原因出现问题：
- 应用程序可能会陷入死锁或无限循环
- 服务可能无法响应请求
- 应用可能需要预热时间
- 临时故障或异常状态

Kubernetes 提供了健康检查机制来检测这些问题并自动处理，确保应用程序的可用性和可靠性。

### 探针类型
#### 1. Liveness Probe（存活探针）
**作用**：检测容器是否正在运行
- 如果探针失败，kubelet 会杀死容器并根据重启策略处理
- 用于发现和处理应用程序锁或异常状态

**使用场景**：
- Web 应用的健康检查端点
- 数据库连接检查
- 关键进程存活检查

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

#### 2. Readiness Probe（就绪探针）
**作用**：检测容器是否准备好接收流量
- 如果探测失败，会从服务的负载均衡中移除该 Pod
- 用于确保应用程序完全启动和准备就绪

**使用场景**：
- 应用程序需要加载大量数据
- 依赖外部服务的启动检查
- 需要预热的应用

```yaml
readinessProbe:
  tcpSocket:
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```

#### 3. Startup Probe（启动探针）
**作用**：检测容器中的应用程序是否已经启动
- 启动探针失败时，会重启容器
- 用于处理需要较长启动时间的应用程序

**使用场景**：
- 遗留应用程序启动慢
- 不确定启动时间的应用
- 需要初始化的应用

```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
```

### 探测方式
#### HTTP GET
- 向容器发送 HTTP GET 请求
- 响应码在 200-399 范围内表示成功
- 适用于 HTTP 服务健康检查

#### TCP Socket
- 尝试建立 TCP 连接到容器的指定端口
- 连接建立成功表示探测成功
- 适用于 TCP 服务检查

#### Exec
- 在容器内执行指定命令
- 命令返回状态码为 0 表示成功
- 适用于自定义检查逻辑

### 配置建议
1. 探针参数设置
   - initialDelaySeconds：容器启动后首次探测等待时间
   - periodSeconds：执行探测的时间间隔
   - timeoutSeconds：探测超时时间
   - successThreshold：探测成功的最小连续次数
   - failureThreshold：探测失败的重试次数

2. 最佳实践
   - 根据应用特点选择合适的探针类型
   - 设置合理的超时时间和重试次数
   - 确保健康检查端点的轻量级和可靠性
   - 避免探测逻辑中的副作用

## 资源限制

### 什么是资源限制？
资源限制是 Kubernetes 中用于控制容器可以使用的计算资源（CPU、内存等）的机制。包括两个重要概念：
- requests：容器需要的最小资源量
- limits：容器可以使用的最大资源量

### 为什么需要资源限制？
1. 资源保障
   - 确保应用程序有足够的资源运行
   - 防止某个容器消耗过多资源影响其他容器
   - 提供可预测的性能表现

2. 成本优化
   - 提高资源利用率
   - 合理分配集群资源
   - 便于容量规划

3. 问���隔离
   - 防止异常容器影响整个节点
   - 隔离不同优先级的工作负载
   - 保护关键业务应用

### 如何设置资源限制？
#### CPU 资源
CPU 资源以核心数为单位，可以是小数：
```yaml
spec:
  containers:
  - name: app
    resources:
      requests:
        cpu: "250m"    # 0.25 CPU，即 1/4 核心
      limits:
        cpu: "500m"    # 0.5 CPU，即 1/2 核心
```

#### 内存资源
内存资源可以使用 Mi（兆字节）或 Gi（吉字节）为单位：
```yaml
spec:
  containers:
  - name: app
    resources:
      requests:
        memory: "64Mi"  # 64 兆字节
      limits:
        memory: "128Mi" # 128 兆字节
```

### 服务质量等级（QoS Classes）
Kubernetes 根据资源限制的设置将 Pod 分为三个 QoS 等级：

#### 1. Guaranteed（最高优先级）
- 特点：requests 等于 limits
- 适用场景：关键业务应用
- 优势：最不可能被驱逐
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "500m"
  limits:
    memory: "128Mi"
    cpu: "500m"
```

#### 2. Burstable（中等优先级）
- 特点：requests 小于 limits
- 适用场景：一般业务应用
- 优势：可以使用额外资源
```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "250m"
  limits:
    memory: "128Mi"
    cpu: "500m"
```

#### 3. BestEffort（最低优先级）
- 特点：没有设置 requests 和 limits
- 适用场景：非关键任务
- 特性：最先被驱逐
```yaml
resources: {}
```

### 最佳实践
1. 资源设置建议
   - 基于实际观察设置 requests
   - 为突发负载预留适当 limits
   - 避免设置过大的 limits

2. 监控和调整
   - 定期检查资源使用情况
   - 根据监控数据调整限制
   - 注意内存泄漏问题

3. 常见陷阱
   - CPU 限制过严可能导致性能问题
   - 内存限制过严可能导致 OOM
   - 资源预留不足可能影响调度

### 故障排查
```bash
# 查看 Pod 资源使用情况
kubectl top pod <pod-name>

# 查看节点资源使用情况
kubectl top node

# 查看资源请求和限制
kubectl describe pod <pod-name>
```

## 调度策略

### 什么是调度策略？
调度策略是 Kubernetes 用来决定 Pod 应该被调度到哪个节点的规则集合。它通过多种机制来确保 Pod 被放置在最合适的节点上，包括：
- 节点选择器（NodeSelector）
- 节点亲和性（Node Affinity）
- Pod 亲和性与反亲和性（Pod Affinity/Anti-affinity）
- 污点和容忍（Taints and Tolerations）

### 为什么需要调度策略？
1. 资源优化
   - 合理分配计算资源
   - 优化节点利用率
   - 降低运营成本

2. 高可用性
   - 跨区域部署
   - 故障域隔离
   - 负载均衡

3. 特殊需求满足
   - 硬件要求（如 GPU）
   - 性能要求（如 SSD）
   - 安全隔离需求

### 如何实现调度策略？
#### 1. 节点选择器（NodeSelector）
最简单的节点选择方式，通过标签来选择节点。

**使用场景**：
- 简单的节点分组
- 特定硬件要求
- 环境隔离

```yaml
# 为节点添加标签
kubectl label nodes <node-name> disktype=ssd

# Pod 配置
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  nodeSelector:
    disktype: ssd
  containers:
  - name: nginx
    image: nginx
```

#### 2. 节点亲和性（Node Affinity）
比 NodeSelector 更灵活的节点选择机制。

**类型**：
- requiredDuringSchedulingIgnoredDuringExecution：硬性要求
- preferredDuringSchedulingIgnoredDuringExecution：软性偏好

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-node-affinity
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: kubernetes.io/e2e-az-name
            operator: In
            values:
            - e2e-az1
            - e2e-az2
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchExpressions:
          - key: another-node-label-key
            operator: In
            values:
            - another-node-label-value
```

#### 3. Pod 亲和性与反亲和性
控制 Pod 之间的调度关系。

**使用场景**：
- 将相关服务的 Pod 调度到同一节点（亲和性）
- 将相同服务的 Pod 分散到不同节点（反亲和性）
- 实现高可用部署

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-pod-affinity
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: security
            operator: In
            values:
            - S1
        topologyKey: topology.kubernetes.io/zone
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: security
              operator: In
              values:
              - S2
          topologyKey: topology.kubernetes.io/zone
```

#### 4. 污点和容忍（Taints and Tolerations）
用于控制哪些 Pod 可以调度到特定节点。

**污点效果**：
- NoSchedule：不调度
- PreferNoSchedule：尽量不调度
- NoExecute：不调度且驱逐现有 Pod

```yaml
# 为节点添加污点
kubectl taint nodes node1 key=value:NoSchedule

# Pod 配置容忍
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  tolerations:
  - key: "key"
    operator: "Equal"
    value: "value"
    effect: "NoSchedule"
  containers:
  - name: nginx
    image: nginx
```

### 最佳实践
1. 调度策略选择
   - 使用 NodeSelector 满足简单需求
   - 使用 Node Affinity 实现复杂调度逻辑
   - 使用 Pod Anti-affinity 实现高可用
   - 使用 Taints 和 Tolerations 保护特殊节点

2. 性能考虑
   - 避免过于复杂的调度规则
   - 合理使用软性和硬性规则
   - 注意调度器的性能影响

3. 可维护性
   - 统一标签命名规范
   - 文档化调度策略
   - 定期review调度效果

### 常见问题排查
```bash
# 查看 Pod 调度状态
kubectl get pod <pod-name> -o wide

# 查看调度失败原因
kubectl describe pod <pod-name>

# 查看节点标签
kubectl get nodes --show-labels

# 查看节点污点
kubectl describe node <node-name> | grep Taints
```

## 常见问题与解决方案
### Pod 启动问题
1. 镜像拉取失败
```bash
# 检查镜像拉取状态
kubectl describe pod <pod-name>

# 配置私有仓库认证
kubectl create secret docker-registry regcred \
  --docker-server=<your-registry-server> \
  --docker-username=<your-name> \
  --docker-password=<your-password>
```

2. 资源不足
```bash
# 检查节点资源
kubectl describe node <node-name>

# 调整资源请求
kubectl set resources deployment <deployment-name> \
  --requests=cpu=200m,memory=512Mi
```

### 健康检查失败
```bash
# 查看 Pod 事件
kubectl describe pod <pod-name>

# 查看容器日志
kubectl logs <pod-name> -c <container-name>

# 进入容器调试
kubectl exec -it <pod-name> -c <container-name> -- /bin/sh
```

## 最佳实践
### 资源管理
- 合理设置资源请求和限制
- 使用 QoS 保障关键应用
- 监控资源使用情况

### 可靠性
- 实施健康检查
- 配置适当的重启策略
- 使用 Pod 干扰预算

### 安全性
- 使用安全上下文
- 实施网络策略
- 配置 RBAC 权限