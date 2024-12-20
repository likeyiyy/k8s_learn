# 6. 服务暴露与访问

## 引言：为什么需要关注服务暴露？
在实际工作中，我们经常会遇到这些场景：
1. 微服务架构中，服务之间需要相互访问
2. 外部用户需要访问应用服务
3. 测试环境需要临时对外暴露服务
4. 生产环境需要安全可控的服务访问

Kubernetes 提供了多种服务暴露方式，每种方式都有其适用场景。选择正确的方式对于应用的可用性、安全性和性能都至关重要。

## Service 类型详解
### ClusterIP：集群内部访问的基础
#### 什么是 ClusterIP？
ClusterIP 是 Kubernetes 中最基本的 Service 类型，它提供了集群内部的服务发现和负载均衡功能。

#### 实际应用场景
1. 微服务架构中的服务间通信
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: backend-service
   spec:
     type: ClusterIP
     selector:
       app: backend
     ports:
     - port: 80          # Service 端口
       targetPort: 8080  # 容器端口
   ```

2. 内部缓存服务
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: redis-service
   spec:
     type: ClusterIP
     selector:
       app: redis
     ports:
     - port: 6379
       targetPort: 6379
   ```

#### 使用技巧
1. 服务发现
```bash
# 通过 DNS 访问服务
backend-service.default.svc.cluster.local

# 环境变量方式
BACKEND_SERVICE_SERVICE_HOST
BACKEND_SERVICE_SERVICE_PORT
```

2. 调试方法
```bash
# 验证服务是否正常
kubectl run test-pod --rm -it --image=busybox -- wget -qO- http://backend-service

# 检查 endpoints
kubectl get endpoints backend-service
```

3. 常见问题处理
- Service 无法访问
```bash
# 检查 Service 配置
kubectl describe svc backend-service

# 验证 Pod 标签
kubectl get pods --show-labels | grep backend
```

### NodePort：直接对外暴露服务
#### 什么是 NodePort？
NodePort 是一种将服务直接暴露在节点物理网络上的方式，它在所有节点上开放指定端口，将请求转发到内部服务。端口范围默认是 30000-32767。

#### 实际应用场景
1. 开发测试环境
   - 快速验证服务
   - 临时对外提供访问
   - 演示环境部署

2. 小规模生产环境
   - 简单的对外服务
   - 内部测试服务
   - 无负载均衡器的环境

#### 配置示例
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80          # 集群内部访问端口
    targetPort: 8080  # 容器端口
    nodePort: 30080   # 节点端口，可选，不指定会随机分配
```

#### 使用技巧
1. 访问方式
```bash
# 获取节点 IP
kubectl get nodes -o wide

# 访问服务
curl http://<node-ip>:30080

# 在集群内部仍可通过 ClusterIP 访问
curl http://web-service
```

2. 安全考虑
- 配置防火墙规则
```bash
# 只允许特定 IP 访问
iptables -A INPUT -p tcp --dport 30080 -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 30080 -j DROP
```

- 使用 NGINX 作为前置代理
```nginx
upstream nodeport_service {
    server node1:30080;
    server node2:30080;
}

server {
    listen 80;
    server_name example.com;
    
    location / {
        proxy_pass http://nodeport_service;
    }
}
```

### LoadBalancer：云环境的标准方案
#### 什么是 LoadBalancer？
LoadBalancer 类型的 Service 会自动创建外部负载均衡器，将流量分发到后端 Pod。这通常需要云服务提供商的支持。

#### 实际应用场景
1. 生产环境服务暴露
   - 高可用web服务
   - API 网关
   - 需要固定外部 IP 的服务

2. 特殊需求场景
   - SSL 终止
   - 流量监控
   - 智能路由

#### 配置示例
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb  # AWS 网络负载均衡器
    service.beta.kubernetes.io/aws-load-balancer-internal: "true"  # 内部负载均衡器
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
  sessionAffinity: ClientIP  # 启用会话亲和性
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

#### 最佳实践
1. 成本优化
   - 合理使用内部/外部负载均衡器
   - 考虑使用 Ingress 替代多个 LoadBalancer
   - 及时清理未使用的负载均衡器

2. 高可用配置
```yaml
spec:
  # 确保负载均衡器后端有足够的 Pod
  minReplicas: 3
  # 配置健康检查
  healthCheckNodePort: 30000
  # 配置会话保持
  sessionAffinity: ClientIP
```

3. 监控和维护
```bash
# 查看负载均衡器状态
kubectl get svc web-service -o wide

# 检查负载均衡器事件
kubectl describe svc web-service

# 验证后端 Pod 健康状态
kubectl get endpoints web-service
```

#### 常见问题处理
1. 负载均衡器创建失败
```bash
# 检查云服务商配额
# 验证服务账号权限
# 查看控制器日志
kubectl logs -n kube-system -l k8s-app=cloud-controller-manager
```

2. 流量分配不均
```bash
# 检查 Pod 绪状态
kubectl get pods -l app=web -o wide

# 验证服务配置
kubectl describe svc web-service

# 测试负载分布
for i in {1..100}; do curl http://<load-balancer-ip>; done
```

3. 会话保持问题
```bash
# 验证会话亲和性配置
kubectl get svc web-service -o yaml | grep sessionAffinity

# 测试会话保持
curl -b "session=test" http://<load-balancer-ip>
```

## Ingress 配置

### 什么是 Ingress？
Ingress 是 Kubernetes 中管理外部访问集群内服务的 API 对象，通常负责提供负载均衡、SSL 终止和基于名称的虚拟主机等功能。它是一个更高层次的服务暴露方案，可以取代多个 LoadBalancer Service。

### 为什么需要 Ingress？
1. 统一入口管理
   - 集中管理多个服务的访问
   - 降低维护成本
   - 简化证书管理
   - 优化资源使用

2. 灵活的路由规则
   - 基于路径的路由
   - 基于域名的路由
   - URL 重写
   - 流量分配

3. 成本优化
   - 共享负载均衡器
   - 减少公网 IP 使用
   - 简化 DNS 配置

### 实现方案
#### 1. Ingress Controller
常用的实现：
- Nginx Ingress Controller（最常用）
- Traefik
- HAProxy
- Kong
- Istio Gateway

安装示例（Nginx Ingress）：
```bash
# 使用 Helm 安装
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx

# 或使用 YAML 安装
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

#### 2. 基础配置示例
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: minimal-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.example.com    # 域名路由
    http:
      paths:
      - path: /api             # 路径路由
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
  tls:                         # HTTPS 配置
  - hosts:
    - myapp.example.com
    secretName: myapp-tls
```

### 高级配置场景
#### 1. 流量控制
```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/limit-rps: "10"
    nginx.ingress.kubernetes.io/proxy-body-size: "8m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "15"
```

#### 2. 会话亲和性
```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/session-cookie-name: "route"
    nginx.ingress.kubernetes.io/session-cookie-expires: "172800"
```

#### 3. SSL/TLS 配置
```yaml
# 创建证书密钥
kubectl create secret tls myapp-tls \
  --key privkey.pem \
  --cert cert.pem

# Ingress 配置
spec:
  tls:
  - hosts:
    - myapp.example.com
    secretName: myapp-tls
```

### 最佳实践
1. 安全配置
```yaml
metadata:
  annotations:
    # 强制 HTTPS
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    # 配置 HSTS
    nginx.ingress.kubernetes.io/hsts: "true"
    # 配置 CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
```

2. 性能优化
```yaml
metadata:
  annotations:
    # 启用 GZIP
    nginx.ingress.kubernetes.io/enable-gzip: "true"
    # 配置缓存
    nginx.ingress.kubernetes.io/proxy-buffering: "on"
    nginx.ingress.kubernetes.io/proxy-buffer-size: "8k"
```

3. 监控和日志
```yaml
metadata:
  annotations:
    # 启用访问日志
    nginx.ingress.kubernetes.io/enable-access-log: "true"
    # 配置监控
    nginx.ingress.kubernetes.io/enable-metrics: "true"
```

### 常见问题处理
1. 路由不生效
```bash
# 检查 Ingress 状态
kubectl describe ingress minimal-ingress

# 查看 Ingress Controller 日志
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# 验证后端服务
kubectl get svc api-service web-service
```

2. 证书问题
```bash
# 检查证书密钥
kubectl describe secret myapp-tls

# 验证证书配置
kubectl get ingress minimal-ingress -o yaml | grep tls -A 5

# 测试 HTTPS 访问
curl -v https://myapp.example.com
```

3. 性能问题
```bash
# 检查 Ingress Controller 资源使用
kubectl top pods -n ingress-nginx

# 查看连接状态
kubectl exec -it -n ingress-nginx <ingress-pod> -- nginx -T

# 负载测试
ab -n 1000 -c 100 https://myapp.example.com/api/
```

### 注意事项
1. 规划建议
   - 合理规划域名和路径
   - 考虑证书管理方案
   - 评估性能需求
   - 制定备份策略

2. 安全考虑
   - 及时更新证书
   - 配置访问控制
   - 启用 WAF 功能
   - 监控异常访问

3. 维护建议
   - 定期更新版本
   - 监控资源使用
   - 备份配置
   - 制定故障处理流程

## 负载均衡详解

### 什么是负载均衡？
负载均衡是将工作负载分布到多个后端服务器的过程。在 Kubernetes 中，负载均衡是服务发现和路由的核心功能。

### 为什么需要负载均衡？
1. 高可用性
   - 消除单点故障
   - 自动故障转移
   - 平滑处理服务更新

2. 性能优化
   - 分散访问压力
   - 提高响应速度
   - 优化资源利用

3. 灵活扩展
   - 支持动态扩缩容
   - 适应流量变化
   - 便于维护升级

### 负载均衡策略
#### 1. RoundRobin（轮询）
- 最简单的负载均衡算法
- 适用场景：
  - 后端服务能力相近
  - 请求复杂度相似
  - 无状态服务

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: ClusterIP
  sessionAffinity: None  # 默认使用轮询
```

#### 2. SessionAffinity（会话亲和）
- 基于客户端 IP 的会话保持
- 适用场景：
  - 有状态服务
  - 需要会话保持
  - 缓存优化

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

#### 3. 基于权重的负载均衡
使用 Ingress 配置：
```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "30"
```

### 高级特性
#### 1. 健康检查
```yaml
spec:
  containers:
  - name: web
    readinessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 10
    livenessProbe:
      httpGet:
        path: /live
        port: 8080
```

#### 2. 故障转移
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: web
```

## 服务网络详解

### 什么是服务网络？
服务网络是 Kubernetes 中实现服务发现和负载均衡的网络层，包括 Pod 网络、Service 网络等多个层面。

### 网络模型
#### 1. Pod 网络
- 特点：
  - 每个 Pod 有唯一 IP
  - Pod 间可直接通信
  - 跨节点通信需要 CNI 支持

```bash
# 查看 Pod IP
kubectl get pods -o wide

# 测试 Pod 间通信
kubectl exec -it pod1 -- ping <pod2-ip>
```

#### 2. Service 网络
- 特点：
  - 稳定的服务访问点
  - 自动负载均衡
  - 服务发现支持

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  clusterIP: 10.0.1.100  # 可选指定
  ports:
  - port: 80
```

#### 3. 集群网络
- 组件：
  - kube-proxy
  - CNI 插件
  - CoreDNS

### 网络策略
#### 1. 入站规则控制
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-allow
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 8080
```

#### 2. 出站规则控制
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-egress
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: db
    ports:
    - protocol: TCP
      port: 5432
```

### 最佳实践
1. 网络规划
   - 合理规划 IP 地址段
   - 考虑跨集群通信
   - 规划网络策略
   - 配置服务质量

2. 安全加固
   - 实施最小权限原则
   - 隔离关键服务
   - 监控网络流量
   - 定期安全审计

3. 性能优化
   - 选择合适的 CNI 插件
   - 优化网络配置
   - 监控网络性能
   - 处理网络瓶颈

### 常见问题处理
1. 网络连通性问题
```bash
# 检查网络策略
kubectl get networkpolicies

# 测试网络连通性
kubectl run test-pod --rm -it --image=nicolaka/netshoot -- bash
```

2. DNS 解析问题
```bash
# 检查 CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns

# 测试 DNS 解析
kubectl run dns-test --rm -it --image=busybox -- nslookup kubernetes.default
```

3. 性能问题
```bash
# 网络性能测试
kubectl run perf-test --rm -it --image=networkstatic/iperf3 -- -c <target-ip>

# 查看网络插件状态
kubectl get pods -n kube-system -l k8s-app=calico-node
```