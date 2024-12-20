# 9. 配置与安全

## 为什么需要关注配置管理和安全？
在生产环境中，配置管理和安全性是两个最关键的问题：
1. 配置管理
   - 应用配置需要与代码分离
   - 配置需要能够动态更新
   - 敏感信息需要特殊处理
   - 配置需要版本控制

2. 安全性
   - 保护集群免受外部攻击
   - 控制内部访问权限
   - 保护敏感数据
   - 确保合规性

## ConfigMap 详解
### 什么是 ConfigMap？
ConfigMap 是 Kubernetes 中用于存储非敏感配置数据的资源对象。它可以存储：
- 配置文件
- 命令行参数
- 环境变量
- 其他配置数据

### 创建和使用
#### 1. 从文件创建
```bash
# 创建包含配置文件的 ConfigMap
kubectl create configmap nginx-conf --from-file=nginx.conf

# 从目录创建
kubectl create configmap app-config --from-file=./config
```

#### 2. 从键值对创建
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: "mysql://localhost:3306/db"
  cache_size: "100"
  features.json: |
    {
      "feature1": true,
      "feature2": false
    }
```

#### 3. 在 Pod 中使用
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: web
    image: nginx
    # 作为环境变量使用
    env:
    - name: DB_URL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database_url
    
    # 作为文件挂载
    volumeMounts:
    - name: config-volume
      mountPath: /etc/nginx/conf.d
  
  volumes:
  - name: config-volume
    configMap:
      name: nginx-conf
```

### 最佳实践
1. 配置管理
   - 使用版本控制管理配置
   - 环境特定的配置分离
   - 避免存储敏感信息
   - 使用命名约定

2. 更新策略
   - 使用滚动更新
   - 配置热重载
   - 版本回滚计划
   - 监控配置变更

## Secret 管理
### 什么是 Secret？
Secret 用于存储和管理敏感信息，如：
- 密码
- OAuth 令牌
- SSH 密钥
- TLS 证书

### Secret 类型
1. Opaque（通用）
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  username: dXNlcm5hbWU=  # base64 编码
  password: cGFzc3dvcmQ=
```

2. kubernetes.io/tls
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: <base64 encoded cert>
  tls.key: <base64 encoded key>
```

3. kubernetes.io/dockerconfigjson
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: docker-registry
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64 encoded docker config>
```

### 使用 Secret
#### 1. 环境变量方式
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: app
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: password
```

#### 2. 文件挂载方式
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: app
    volumeMounts:
    - name: secret-volume
      mountPath: "/etc/secrets"
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: db-secret
```

### 安全最佳实践
1. Secret 管理
   - 加密存储
   - 最小权限原则
   - 定期轮换
   - 审计日志

2. 访问控制
   - 使用 RBAC 限制访问
   - 监控 Secret 使用
   - 实施网络策略
   - 配置 Pod 安全策略

## RBAC 权限控制
### 基本概念
- Role：定义命名空间内的权限
- ClusterRole：定义集群级别的权限
- RoleBinding：将角色绑定到用户
- ClusterRoleBinding：集群级别的角色绑定

### 配置示例
#### 1. 创建 Role
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
```

#### 2. 创建 RoleBinding
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### 最佳实践
1. 权限设计
   - 最小权限原则
   - 职责分离
   - 定期审查
   - 权限分组

2. 监控和审计
   - 记录访问日志
   - 监控异常行为
   - 定期权限审计
   - 合规性检查

## 安全上下文
### Pod 安全上下文
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-context-demo
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
  containers:
  - name: sec-ctx-demo
    image: busybox
    command: [ "sh", "-c", "sleep 1h" ]
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
```

### 网络策略
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
      port: 80
```

## 常见问题处理
### 配置问题
1. ConfigMap 更新不生效
```bash
# 检查 ConfigMap
kubectl describe configmap app-config

# 强制 Pod 重新加载
kubectl rollout restart deployment app
```

2. Secret 访问权限问题
```bash
# 检查 RBAC 配置
kubectl auth can-i get secrets --as=system:serviceaccount:default:myapp

# 查看详细权限
kubectl describe rolebinding <binding-name>
```

### 安全问题
1. 权限提升
```bash
# 审计用户权限
kubectl auth reconcile -f rbac.yaml

# 查看角色绑定
kubectl get rolebindings,clusterrolebindings
```

2. 网络隔离
```bash
# 检查网络策略
kubectl describe networkpolicy api-allow

# 测试网络连接
kubectl run test --rm -it --image=busybox -- wget -O- http://api-service
```

