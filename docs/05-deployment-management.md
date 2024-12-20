# 5. 应用部署与管理

## Deployment 实践

### 什么是 Deployment？
Deployment 是 Kubernetes 中用于声明式地管理 Pod 和 ReplicaSet 的资源对象，它提供了：
- 声明式的应用更新
- 滚动发布和回滚
- 扩容和缩容
- 暂停和继续部署

### 为什么需要 Deployment？
1. 应用管理需求
   - 确保应用程序的可用性
   - 支持无缝更新和回滚
   - 维护应用程序的多个副本
   - 自动处理故障恢复

2. 运维效率提升
   - 自动化部署流程
   - 降低人为错误
   - 简化版本管理
   - 提供一致的部署体验

3. 业务需求满足
   - 支持蓝绿部署
   - 支持金丝雀发布
   - 灵活的发布策略
   - 快速响应变化

### 如何使用 Deployment？
#### 1. 创建 Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
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
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"
```

#### 2. 部署策略配置
```yaml
spec:
  strategy:
    type: RollingUpdate    # 也可以是 Recreate
    rollingUpdate:
      maxSurge: 1          # 最大超出 replicas 的 Pod 数量
      maxUnavailable: 0    # 最大不可用 Pod 数量
```

#### 3. 常用操作命令
```bash
# 创建 Deployment
kubectl apply -f deployment.yaml

# 查看部署状态
kubectl get deployment nginx-deployment
kubectl rollout status deployment/nginx-deployment

# 查看 Deployment 详情
kubectl describe deployment nginx-deployment

# 扩缩容
kubectl scale deployment nginx-deployment --replicas=5

# 更新镜像
kubectl set image deployment/nginx-deployment nginx=nginx:1.16.1
```

### 部署策略详解
#### 1. 重建策略（Recreate）
- 特点：先删除所有旧版本 Pod，再创建新版本
- 适用场景：
  - 应用不支持多版本并存
  - 需要快速切换版本
  - 开发测试环境

#### 2. 滚动更新（RollingUpdate）
- 特点：逐步替换 Pod，保证服务可用性
- 配置参数：
  - maxSurge：最大超出 Pod 数量
  - maxUnavailable：最大不可用 Pod 数量
- 适用场景：
  - 生产环境
  - 需要零停机更新
  - 支持多版本并存

#### 3. 金丝雀发布（Canary Deployment）
##### 基础认知
**概念**：
- 金丝雀发布源自矿工用金丝雀探测矿井中是否有有毒气体
- 在 K8s 中指先发布一小部分新版本应用，用于验证新版本的稳定性

**目的**：
- 降低发布风险
- 及早发现问题
- 快速回滚能力
- 用户体验保护

**原理**：
- 保持大部分流量在稳定版本
- 将少量流量导向新版本
- 通过标签选择器控制流量分配
- 逐步增加新版本比例

##### 实操要点
1. 部署配置
```yaml
# 金丝雀版本
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-canary
spec:
  replicas: 1    # 控制金丝雀版本的副本数
  selector:
    matchLabels:
      app: nginx
      track: canary
  template:
    metadata:
      labels:
        app: nginx
        track: canary    # 使用 track 标签区分版本
    spec:
      containers:
      - name: nginx
        image: nginx:1.16.1
```

2. 流量控制
```yaml
# 服务配置
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx    # 同时匹配稳定版和金丝雀版本
  ports:
  - port: 80
```

##### 关联知识
- 服务网格（如 Istio）的流量控制
- 监控和度量指标收集
- A/B 测试策略
- 负载均衡配置

##### 问题处理
1. 流量分配不均
```bash
# 检查 Pod 标签
kubectl get pods --show-labels

# 验证服务选择器
kubectl describe svc nginx-service
```

2. 版本切换问题
```bash
# 监控金丝雀版本状态
kubectl rollout status deployment/nginx-canary

# 查看金丝雀版本日志
kubectl logs -l track=canary
```

#### 4. 蓝绿部署（Blue-Green Deployment）
##### 基础认知
**概念**：
- 同时维护两个完全相同的环境，一个是当前运行的版本（蓝），一个是准备发布的版本（绿）
- 通过切换服务流量来实现版本更新

**目的**：
- 零停机时间部署
- 快速回滚能力
- 环境隔离
- 减少发布风险

**原理**：
- 部署新版本（绿）环境
- 测试验证新环境
- 切换流量到新环境
- 保留旧环境（蓝）作为回滚选项

##### 实操要点
1. 环境配置
```yaml
# 蓝版本部署
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
      version: blue
  template:
    metadata:
      labels:
        app: nginx
        version: blue
    spec:
      containers:
      - name: nginx
        image: nginx:1.14.2

---
# 绿版本部署
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
      version: green
  template:
    metadata:
      labels:
        app: nginx
        version: green
    spec:
      containers:
      - name: nginx
        image: nginx:1.16.1
```

2. 服务切换
```yaml
# 服务配置
apiVersion: v1
kind: Service
metadata:
  name: nginx-prod
spec:
  selector:
    app: nginx
    version: blue    # 切换到 green 实现版本更新
  ports:
  - port: 80
```

##### 关联知识
- 负载均衡配置
- 会话保持
- 数据库迁移
- DNS 配置

##### 问题处理
1. 切换失败处理
```bash
# 验证新版本就绪状态
kubectl get pods -l version=green

# 快速回滚到蓝版本
kubectl patch svc nginx-prod -p '{"spec":{"selector":{"version":"blue"}}}'
```

2. 资源问题
```bash
# 检查资源使用情况
kubectl top pods -l app=nginx

# 清理旧版本
kubectl delete deployment nginx-blue
```

### 部署策略对比
#### 特点对比
| 特性 | 重建策略（Recreate） | 滚动更新（RollingUpdate） | 金丝雀发布 | 蓝绿部署 |
|------|---------------------|------------------------|-----------|----------|
| 停机时间 | 有 | 无 | 无 | 无 |
| 资源需求 | 低 | 中 | 中 | 高 |
| 回滚速度 | 快 | 中 | 快 | 快 |
| 用户影响 | 全用户 | 部分用户 | 小部分用户 | 无 |
| 复杂度 | 低 | 中 | 高 | 高 |

#### 场景选择
1. 重建策略适用于：
   - 开发环境快速部署
   - 数据库等有状态应用
   - 不要求服务连续性的场景
   - 资源受限的环境

2. 滚动更新适用于：
   - 生产环境标准更新
   - 无状态应用
   - 要求服务持续可用
   - 版本兼容性好的应用

3. 金丝雀发布适用于：
   - 需要验证新功能
   - 风险较高的更新
   - 具备完善监控体系
   - 可以接受部分用户测试

4. 蓝绿部署适用于：
   - 关键业务应用
   - 要求零停机时间
   - 资源充足的环境
   - 需要完整测试验证

#### 风险评估
1. 重建策略
   - 优势：
     - 实现简单
     - 资源利用率高
     - 回滚迅速
   - 劣势：
     - 存在停机时间
     - 用户体验差
     - 不适合生产环境

2. 滚动更新
   - 优势：
     - 零停机时间
     - 资源利用率合理
     - 用户影响小
   - 劣势：
     - 更新时间较长
     - 需要版本兼容
     - 回滚相对复杂

3. 金丝雀发布
   - 优势：
     - 风险可控
     - 易于监控验证
     - 支持灰度测试
   - 劣势：
     - 配置复杂
     - 需要额外监控
     - 发布周期长

4. 蓝绿部署
   - 优势：
     - 环境隔离
     - 回滚简单
     - 测试充分
   - 劣势：
     - 资源成本高
     - 配置复杂
     - 数据同步难

#### 选择建议
1. 资源考虑
   - 资源充足：可以考虑蓝绿部署
   - 资源受限：建议使用滚动更新
   - 开发环境：可以使用重建策略
   - 灰度测试：选择金丝雀发布

2. 应用特点
   - 无状态应用：滚动更新或蓝绿部署
   - 有状态应用：重建策略或蓝绿部署
   - 新功能验证：金丝雀发布
   - 关键业务：蓝绿部署

3. 运维能力
   - 基础设施完善：可以采用复杂策略
   - 监控能力强：适合金丝雀发布
   - 自动化程度高：所有策略都可考虑
   - 人力资源有限：建议使用简单策略

### 发布策略选择建议
1. 选择金丝雀发布当：
   - 需要在真实用户环境中验证
   - 可以接受部分用户体验新版本
   - 有完善的监控和度量系统

2. 选择蓝绿部署当：
   - 需要零停机时间更新
   - 有足够的资源运行两个环境
   - 需要完整的环境测试
   - 可以快速切换版本

### 最佳实践
1. 配置建议
   - 始终设置资源限制
   - 使用合适的副本数
   - 配置合理的健康检查
   - 设置适当的更新策略

2. 标签管理
   - 使用有意义的标签
   - 保持标��的一致性
   - 避免标签冲突

3. 版本控制
   - 使用语义化版本号
   - 保留发布历史记录
   - 准备回滚方案

### 故障排查
```bash
# 查看部署状态
kubectl rollout status deployment/nginx-deployment

# 查看部署历史
kubectl rollout history deployment/nginx-deployment

# 查看特定版本详情
kubectl rollout history deployment/nginx-deployment --revision=2

# 回滚到上一版本
kubectl rollout undo deployment/nginx-deployment

# 回滚到特定版本
kubectl rollout undo deployment/nginx-deployment --to-revision=2
```

## 滚动更新

### 什么是滚动更新？
滚动更新（Rolling Update）是 Kubernetes 中实现零停机部署的一种策略，通过逐步替换应用程序的实例来完成更新。它是 Deployment 的默认更新策略。

### 为什么需要滚动更新？
1. 业务连续性
   - 确保服务不中断
   - 保持用户访问正常
   - 避免更新过程的服务损失

2. 风险控制
   - 渐进式更新
   - 及时发现问题
   - 快速回滚能力

3. 资源效率
   - 平滑的资源使用
   - 避免资源浪费
   - 控制更新速度

### 如何配置滚动更新？
#### 1. 更新策略配置
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # 可以超出期望副本数的最大 Pod 数量
      maxUnavailable: 0  # 更新过程中允许不可用的最大 Pod 数量
  minReadySeconds: 5    # Pod 就绪后的最小等待时间
  revisionHistoryLimit: 10  # 保留的历史版本数
```

#### 2. 关键参数说明
1. maxSurge
   - 定义：可以超出期望副本数的最大 Pod 数量
   - 可以是数字或百分比
   - 示例：如果 replicas=3，maxSurge=1，则最多可以有 4 个 Pod

2. maxUnavailable
   - 定义：更新过程中允许不可用的最大 Pod 数量
   - 可以是数字或百分比
   - 示例：如果 replicas=3，maxUnavailable=1，则至少要有 2 个 Pod 可用

3. minReadySeconds
   - 定义：新创建的 Pod 就绪后的最小等待时间
   - 用于确保 Pod 真正就绪
   - 默认值为 0

4. revisionHistoryLimit
   - 定义：保留的历史版本数
   - 用于回滚操作
   - 默认值为 10

### 更新流程详解
#### 1. 更新触发
```bash
# 通过命令更新镜像
kubectl set image deployment/nginx-deployment nginx=nginx:1.16.1

# 或者修改配置文件
kubectl edit deployment/nginx-deployment

# 使用声明式配置
kubectl apply -f deployment.yaml
```

#### 2. Pod 替换过程
1. 创建新 Pod
   - 基于新配置创建 Pod
   - 等待 Pod 就绪
   - 遵守 maxSurge 限制

2. 终止旧 Pod
   - 遵守 maxUnavailable 限制
   - 等待优雅终止期
   - 删除旧 Pod

#### 3. 健康检查
```yaml
spec:
  template:
    spec:
      containers:
      - name: nginx
        readinessProbe:
          httpGet:
            path: /healthz
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 4. 完成确认
```bash
# 查看更新状态
kubectl rollout status deployment/nginx-deployment

# 查看 Pod 状态
kubectl get pods -l app=nginx

# 查看更新历史
kubectl rollout history deployment/nginx-deployment
```

### 最佳实践
1. 更新策略设置
   - 设置合适的 maxSurge 和 maxUnavailable
   - 配置适当的健康检查
   - 设置合理的 minReadySeconds

2. 资源管理
   - 预留足够的资源配额
   - 考虑节点资源容量
   - 合理设置 Pod 资源请求

3. 监控和告警
   - 监控更新进度
   - 设置超时告警
   - 准备回滚方案

### 常见问题处理
1. 更新卡住
```bash
# 检查更新状态
kubectl rollout status deployment/nginx-deployment

# 查看详细事件
kubectl describe deployment nginx-deployment

# 如需取消更新
kubectl rollout undo deployment/nginx-deployment
```

2. Pod 启动失败
```bash
# 查看 Pod 状态
kubectl get pods -l app=nginx

# 查看 Pod 日志
kubectl logs <pod-name>

# 查看 Pod 详情
kubectl describe pod <pod-name>
```

3. 资源不足
```bash
# 检查节点资源
kubectl describe nodes

# 调整更新策略
kubectl patch deployment nginx-deployment -p '{"spec":{"strategy":{"rollingUpdate":{"maxSurge":1,"maxUnavailable":1}}}}'
```

### 注意事项
1. 版本兼容性
   - 确保新旧版本可以共存
   - 注意数据库架构变更
   - 考虑 API 兼容性

2. 性能影响
   - 评估更新对系统的影响
   - 选择合适的更新时间
   - 控制更新速度

3. 回滚准备
   - 保留足够的历史版本
   - 测试回滚流程
   - 准备回滚脚本

## 回滚操作

### 什么是回滚？
回滚是将应用恢复到之前某个已知正常版本的操作。在 Kubernetes 中，Deployment 提供了内置的回滚机制，可以方便地将应用回退到之前的版本。

### 为什么需要回滚？
1. 故障恢复
   - 新版本出现严重问题
   - 性能显著下降
   - 功能不符合预期
   - 安全漏洞发现

2. 风险管理
   - 快速故障恢复
   - 减少服务中断
   - 保护业务连续性

3. 版本管理
   - 版本历史追踪
   - 变更记录保存
   - 版本对比分析

### 如何实现回滚？
#### 1. 版本控制
```bash
# 查看部署历史
kubectl rollout history deployment/nginx-deployment

# 查看特定版本详情
kubectl rollout history deployment/nginx-deployment --revision=2

# 比较不同版本
kubectl rollout history deployment/nginx-deployment --revision=2 --revision=3
```

#### 2. 回滚操作
```yaml
# deployment-rollback.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  revisionHistoryLimit: 10  # 保留的历史版本数
```

```bash
# 回滚到上一版本
kubectl rollout undo deployment/nginx-deployment

# 回滚到特定版本
kubectl rollout undo deployment/nginx-deployment --to-revision=2

# 暂停部署（在回滚过程中需要时）
kubectl rollout pause deployment/nginx-deployment

# 恢复部署
kubectl rollout resume deployment/nginx-deployment
```

### 回滚策略
#### 1. 自动回滚
- 基于监控指标
```yaml
# 使用 Prometheus 和自定义指标
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nginx-hpa
spec:
  metrics:
  - type: Pods
    pods:
      metric:
        name: error_rate
      target:
        type: AverageValue
        averageValue: 100m
```

- 基于健康检查
```yaml
spec:
  template:
    spec:
      containers:
      - name: nginx
        livenessProbe:
          httpGet:
            path: /healthz
            port: 80
          failureThreshold: 3
```

#### 2. 手动回滚
1. 回滚前检查
```bash
# 检查目标版本状态
kubectl describe deployment/nginx-deployment

# 验证历史版本
kubectl rollout history deployment/nginx-deployment
```

2. 执行回滚
```bash
# 执行回滚
kubectl rollout undo deployment/nginx-deployment --to-revision=2

# 监控回滚进度
kubectl rollout status deployment/nginx-deployment
```

#### 3. 部分回滚
- 使用金丝雀发布进行部分回滚
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-rollback
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
      version: rollback
```

### 回滚监控
#### 1. 监控指标
```bash
# 监控 Pod 状态
kubectl get pods -w

# 查看资源使用情况
kubectl top pods

# 查看部署事件
kubectl describe deployment/nginx-deployment
```

#### 2. 日志分析
```bash
# 收集应用日志
kubectl logs -l app=nginx

# 查看系统事件
kubectl get events --sort-by=.metadata.creationTimestamp
```

### 最佳实践
1. 回滚准备
   - 保留足够的版本历史
   - 记录版本变更信息
   - 准备回滚脚本
   - 定期测试回滚流程

2. 数据处理
   - 考虑数据兼容性
   - 准备数据回滚方案
   - 保护重要数据
   - 验证数据一致性

3. 回滚演练
   - 在测试环境验证
   - 制定回滚流程
   - 明确回滚触发条件
   - 分配角色责任

### 常见问题处理
1. 回滚失败
```bash
# 检查回滚状态
kubectl rollout status deployment/nginx-deployment

# 查看详细错误
kubectl describe deployment/nginx-deployment

# 强制回滚（谨慎使用）
kubectl replace --force -f old-deployment.yaml
```

2. 版本冲突
```bash
# 检查版本历史
kubectl rollout history deployment/nginx-deployment

# 清理历史版本（必要时）
kubectl patch deployment nginx-deployment -p '{"spec":{"revisionHistoryLimit":5}}'
```

3. 资源问题
```bash
# 检查资源使用
kubectl describe nodes

# 调整资源限制
kubectl set resources deployment/nginx-deployment -c=nginx cpu=200m,memory=512Mi
```

### 注意事项
1. 回滚前评估
   - 评估影响范围
   - 确认数据兼容性
   - 检查依赖服务
   - 准备应急方案

2. 回滚过程
   - 监控关键指标
   - 控制回滚速度
   - 及时通知相关方
   - 记录操作日志

3. 回滚后确认
   - 验证服务状态
   - 检查数据一致性
   - 确认性能指标
   - 更新相关文档

## 弹性伸缩

### 什么是弹性伸缩？
弹性伸缩是 Kubernetes 中根据工作负载动态调整应用规模的机制，包括：
- 水平扩展（Pod 数量的增减）
- 垂直扩展（Pod 资��的调整）
- 集群级别的节点扩展

### 为什么需要弹性伸缩？
1. 资源优化
   - 按需分配资源
   - 提高资源利用率
   - 降低运营成本

2. 性能保障
   - 应对流量波动
   - 保证服务质量
   - 避免过载

3. 成本效益
   - 削峰填谷
   - 避免资源浪费
   - 优化成本支出

### 如何实现弹性伸缩？
#### 1. 手动伸缩
```bash
# 使用 kubectl scale 命令
kubectl scale deployment nginx-deployment --replicas=5

# 直接编辑 deployment
kubectl edit deployment nginx-deployment

# 使用配置文件
kubectl apply -f deployment.yaml
```

#### 2. 水平自动伸缩（HPA）
```yaml
apiVersion: autoscaling/v2
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
```

#### 3. 垂直自动伸缩（VPA）
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: nginx-vpa
spec:
  targetRef:
    apiVersion: "apps/v1"
    kind: Deployment
    name: nginx-deployment
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: '*'
      minAllowed:
        cpu: 100m
        memory: 50Mi
      maxAllowed:
        cpu: 1
        memory: 500Mi
```

### 伸缩策略详解
#### 1. 基于指标的伸缩
```yaml
spec:
  metrics:
  # CPU 使用率
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  
  # 自定义指标
  - type: Pods
    pods:
      metric:
        name: packets-per-second
      target:
        type: AverageValue
        averageValue: 1k
```

#### 2. 基于时间的伸缩
```yaml
# 使用 CronHPA 进行定时伸缩
apiVersion: autoscaling.k8s.io/v1
kind: CronHorizontalPodAutoscaler
metadata:
  name: nginx-chpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx-deployment
  schedules:
  - name: "scale-up"
    schedule: "0 9 * * 1-5"
    targetReplicas: 10
  - name: "scale-down"
    schedule: "0 18 * * 1-5"
    targetReplicas: 2
```

### 监控和调整
#### 1. 监控指标
```bash
# 查看 HPA 状态
kubectl get hpa

# 查看详细信息
kubectl describe hpa nginx-hpa

# 查看资源使用情况
kubectl top pods
```

#### 2. 调整策略
```yaml
spec:
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
      - type: Pods
        value: 4
        periodSeconds: 15
```

### 最佳实践
1. 资源配置
   - 设置合适的资源请求和限制
   - 配置合理的伸缩范围
   - 避免资源震荡

2. 监控告警
   - 监控伸缩事件
   - 设置关键指标告警
   - 记录伸缩历史

3. 性能优化
   - 优化应用启动时间
   - 合理设置探针
   - 控制伸缩速度

### 常见问题处理
1. 伸缩不生效
```bash
# 检查 HPA 状态
kubectl describe hpa nginx-hpa

# 验证指标是否正常
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/pods"

# 检查资源限制
kubectl describe resourcequota
```

2. 伸缩震荡
```yaml
# 调整稳定窗口
spec:
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
```

3. 资源不足
```bash
# 检查节点资源
kubectl describe nodes

# 检查 Pod 事件
kubectl describe pods
```

### 注意事项
1. 应用特性
   - 考虑应用启动时间
   - 注意服务依赖关系
   - 评估数据一致性

2. 资源规划
   - 预留足够资源
   - 考虑成本因素
   - 设置资源配额

3. 监控反馈
   - 持续监控性能
   - 及时调整策略
   - 记录优化经验

## 服务发现

### 什么是服务发现？
服务发现是一种自动检测和定位服务实例的机制。在 Kubernetes 中，它允许应用程序和服务无需知道对方的具体网络位置就能相互通信。

### 为什么需要服务发现？
1. 动态环境需求
   - Pod IP 地址不固定
   - 服务实例会动态变化
   - 负载均衡需求
   - 故障自动处理

2. 解耦需求
   - 服务间解耦
   - 简化配置管理
   - 提高可维护性
   - 支持微服务架构

3. 可用性需求
   - 自动故障转移
   - 负载分散
   - 服务健康检查
   - 动态扩缩容支持

### 如何实现服务发现？
#### 1. Service 创建
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: myapp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP  # 可以是 ClusterIP、NodePort、LoadBalancer
```

#### 2. Endpoint 管理
```yaml
apiVersion: v1
kind: Endpoints
metadata:
  name: my-service
subsets:
- addresses:
  - ip: 10.244.0.11
  - ip: 10.244.0.12
  ports:
  - port: 8080
```

### 服务发现机制
#### 1. 环境变量
- Kubernetes 自动注入服务信息
```bash
# 查看 Pod 中的环境变量
kubectl exec my-pod -- env | grep SERVICE

# 环境变量格式
MY_SERVICE_SERVICE_HOST=10.0.0.11
MY_SERVICE_SERVICE_PORT=80
```

#### 2. DNS
```yaml
# CoreDNS 配置
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health
        kubernetes cluster.local in-addr.arpa ip6.arpa {
           pods insecure
           upstream
           fallthrough in-addr.arpa ip6.arpa
        }
        prometheus :9153
        forward . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }
```

#### 3. Service 代理
```yaml
# 创建 Service 代理
apiVersion: v1
kind: Service
metadata:
  name: my-service-proxy
spec:
  type: ExternalName
  externalName: my-service.default.svc.cluster.local
```

#### 4. 服务网格集成
```yaml
# Istio 虚拟服务配置
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: my-service-route
spec:
  hosts:
  - my-service
  http:
  - route:
    - destination:
        host: my-service
        subset: v1
      weight: 90
    - destination:
        host: my-service
        subset: v2
      weight: 10
```

### 最佳实践
1. 服务配置
   - 使用合适的服务类型
   - 配置健康检查
   - 设置合理的超时时间
   - 实施服务分组

2. DNS 策略
   - 配置 DNS 缓存
   - 使用合适的搜索域
   - 监控 DNS 性能
   - 处理 DNS 故障

3. 负载均衡
   - 选择合适的负载均衡策略
   - 配置会话亲和性
   - 设置合理的权重
   - 监控负载分布

### 常见问题处理
1. 服务访问问题
```bash
# 检查服务状态
kubectl get svc my-service

# 验证 Endpoints
kubectl get endpoints my-service

# 测试服务连通性
kubectl run test-pod --rm -it --image=busybox -- wget -qO- http://my-service
```

2. DNS 解析问题
```bash
# 检查 DNS 配置
kubectl get configmap coredns -n kube-system -o yaml

# 测试 DNS 解析
kubectl run dns-test --rm -it --image=busybox -- nslookup my-service

# 查看 CoreDNS 日志
kubectl logs -n kube-system -l k8s-app=kube-dns
```

3. 负载均衡问题
```bash
# 检查服务分发
kubectl describe svc my-service

# 监控流量分布
kubectl get endpoints my-service -o yaml

# 测试负载均衡
for i in $(seq 1 10); do kubectl run test-$i --rm -it --image=busybox -- wget -qO- http://my-service; done
```

### 注意事项
1. 性能考虑
   - DNS 缓存设置
   - 服务发现延迟
   - 负载均衡开销
   - 网络性能影响

2. 安全性
   - 服务访问控制
   - 网络策略配置
   - 证书管理
   - 敏感信息保护

3. 可观测性
   - 服务监控
   - 日志收集
   - 链路追踪
   - 性能分析