# 11. 实战案例

## 案例背景
我们将部署一个典型的微服务应用，包含：
- 前端服务（Vue.js）
- 后端 API 服务（Spring Boot）
- 数据库（MySQL）
- 缓存服务（Redis）
- 消息队列（RabbitMQ）

### 系统架构
```ascii
                    [Ingress Controller]
                           |
                    [Service Mesh]
                    /      |      \
        [Frontend] [Backend API]  [Admin API]
                    /      |      \
            [MySQL]   [Redis]   [RabbitMQ]
```

## 前期准备
### 1. 命名空间规划
```bash
# 创建不同环境的命名空间
kubectl create namespace dev
kubectl create namespace staging
kubectl create namespace prod

# 设置默认命名空间
kubectl config set-context --current --namespace=dev
```

### 2. 资源配额设置
```yaml
# 开发环境配额（较小）
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-quota
  namespace: dev
spec:
  hard:
    requests.cpu: "2"
    requests.memory: "4Gi"
    limits.cpu: "4"
    limits.memory: 8Gi
    pods: "20"

---
# 生产环境配额（较大）
apiVersion: v1
kind: ResourceQuota
metadata:
  name: prod-quota
  namespace: prod
spec:
  hard:
    requests.cpu: "2"
    requests.memory: "4Gi"
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "100"

```

### 3. 网络策略
NetworkPolicy（网络策略）是 Kubernetes 的网络安全规则，类似防火墙规则，用来控制 Pod 之间的网络通信。让我用一个简单的例子来解释：

### 1. 基本概念
想象一个电商应用：
- 前端服务（frontend）
- 后端 API（backend）
- 数据库（database）

### 2. 典型的网络策略示例

````yaml
# 后端服务的网络策略
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
  namespace: dev
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database    # 允许访问数据库
    ports:
    - protocol: TCP
      port: 3306
  - to:
    - podSelector:
        matchLabels:
          app: redis      # 允许访问 Redis
    ports:
    - protocol: TCP
      port: 6379         # Redis 默认端口
````

### 3. 图解说明
```
[前端 Pod]  ----允许访问----> [后端 Pod] ----允许访问----> [数据库 Pod]
   ↑                            ↑                           ↑
app=frontend               app=backend                 app=database
```

### 4. 实际测试示例

1. **创建测试命名空间**
````bash
kubectl create namespace test-policy
````

2. **部署测试服务**
````yaml
# frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: nginx
        image: nginx
---
# backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: nginx
        image: nginx
````

3. **测试连接**
````bash
# 在没有网络策略时，所有 Pod 都可以互相访问
kubectl exec -it frontend-pod -- curl backend-service:8080  # 成功

# 应用网络策略后
kubectl apply -f network-policy.yaml

# 再次测试连接
kubectl exec -it frontend-pod -- curl backend-service:8080  # 成功
kubectl exec -it other-pod -- curl backend-service:8080    # 失败
````

### 5. 常见用例

1. **默认拒绝所有流量**
````yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}    # 选择所有 Pod
  policyTypes:
  - Ingress
  - Egress
````

2. **只允许特定命名空间访问**
````yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-dev
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          environment: dev
````

### 6. 最佳实践

1. **从严原则**
   - 默认拒绝所有流量
   - 只允许必要的通信

2. **分层设计**
   - 按应用层级设置策略
   - 前端→后端→数据库

3. **标签管理**
   - 使用清晰的标签策略
   - 便于网络策略的管理

4. **测试验证**
   - 在应用策略前充分测试
   - 保留紧急回滚方案

NetworkPolicy 是实现零信任安全架构的重要工具，通过细粒度的网络访问控制，大大提高了集群的安全性。

## 应用部署
### 1. 数据持久化服务
#### MySQL 部署


啊，确实这是个很好的问题。在部署 MySQL 之前，我们需要先创建 Secret。让我展示完整的部署步骤：

1. **首先创建 MySQL 的 Secret**
`````yaml:mysql-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secret
type: Opaque
data:
  # echo -n 'your_password' | base64
  password: eW91cl9wYXNzd29yZA==  # 'your_password' 的 base64 编码
`````

2. **创建 Secret**
`````bash
# 方法1：使用 yaml 文件创建
kubectl apply -f mysql-secret.yaml

# 方法2：直接用命令创建（推荐，更安全）
kubectl create secret generic mysql-secret \
  --from-literal=password=your_password
`````

3. **然后再部署 MySQL**
`````yaml:mysql.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
  namespace: dev
spec:
  serviceName: mysql
  replicas: 1
  selector:
    matchLabels:
      app: database    # 改为 database
  template:
    metadata:
      labels:
        app: database  # 改为 database
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        ports:
        - containerPort: 3306
        volumeMounts:
        - name: mysql-storage
          mountPath: /var/lib/mysql
      volumes:
      - name: mysql-storage
        persistentVolumeClaim:
          claimName: mysql-pvc
`````

4. **验证部署**
```bash
# 检查 secret 是否创建成功
kubectl get secrets mysql-secret

# 检查 MySQL pod 是否正常运行
kubectl get pods -l app=database

# 检查 MySQL 日志
kubectl logs -l app=database
```

5. **测试连接**
```bash
# 进入 MySQL pod
kubectl exec -it mysql-0 -- mysql -uroot -p

# 输入创建 secret 时设置的密码
```

关于 Secret 的一些最佳实践：
1. 不要将实际密码提交到代码仓库
2. 考虑使用 Vault 等外部密钥管理系统
3. 在不同环境使用不同的 secret
4. 定期轮换密码



#### Redis 部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: dev
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:6.2
        resources:          # 添加资源限制
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        ports:
        - containerPort: 6379
```

在 minikube 中使用本地镜像仓库，需要启用 registry 插件。这里是完整的步骤：

1. **启用 registry 插件**
``````bash
# 启用 registry 插件
minikube addons enable registry

# 验证插件状态
minikube addons list | grep registry
``````


2. **配置镜像仓库访问**
``````bash
# 切换到 minikube 的 docker 环境
eval $(minikube docker-env)

# 验证环境切换
docker ps  # 应该能看到 minikube 的容器
``````


3. **构建并推送镜像**
``````bash
# 构建镜像
docker build -t localhost:5000/backend:v1.0 .

# 推送到 minikube 的 registry
docker push localhost:5000/backend:v1.0
``````


4. **在 deployment 中使用**
``````yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: localhost:5000/backend:v1.0
        # 或者使用 registry.kube-system.svc.cluster.local:5000/backend:v1.0
``````


注意事项：
1. 确保 registry 插件正常运行
2. 使用正确的镜像地址格式
3. 如果遇到问题，可以检查 registry pod 的日志：
``````bash
kubectl logs -n kube-system -l kubernetes.io/minikube-addons=registry
``````




### 2. 后端服务部署
[后端服务部署详细说明](practicals/make-fastapi-app.md)



### 3. 前端服务部署
[前端服务部署详细说明](practicals/frontend-deployment.md)

### 4. 服务暴露

让我们修改服务暴露的配置，使其适用于我们的实际场景。我们使用 Ingress 来暴露前端和后端服务：

```yaml:ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: dev
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$1
spec:
  rules:
  - host: app.local    # 在本地测试时使用
    http:
      paths:
      - path: /api/(.*)     # 后端 API 路径
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 80
      - path: /(.*)         # 前端路径
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```



在 minikube 中使用 Ingress 需要以下步骤：

1. **启用 Ingress 插件**
```bash
# 启用 Ingress
minikube addons enable ingress

# 验证 Ingress 控制器是否运行
kubectl get pods -n ingress-nginx
```



2. **应用 Ingress 配置**
```bash
# 应用配置
kubectl apply -f ingress.yaml

# 查看 Ingress 状态
kubectl get ingress -n dev
```



3. **配置本地 hosts**
```````bash
# 获取 minikube IP
minikube ip

# 添加到 /etc/hosts（需要 sudo 权限）
echo "$(minikube ip) app.local" | sudo tee -a /etc/hosts
```````



4. **测试访问**
```````bash
# 访问前端
curl http://app.local

# 访问后端 API
curl http://app.local/api/redis-test
```````

主要变化：
1. 使用了路径重写（rewrite-target）
2. 简化了 host 配置
3. 添加了正确的路径匹配
4. 确保与我们之前的服务配置匹配


> 非常感谢，我们的测试work了，但是我有一点不懂，之前不是说network-policy限制了只有frontend才能访问backend吗？为什么我们curl http://app.local/api/redis-test也是可以的呢？是我哪里理解错了吗？

好问题！这是因为 Ingress Controller 的流量不受我们之前定义的 NetworkPolicy 限制。让我解释一下流量路径：

1. **当前流量路径**：
```
外部请求 -> Ingress Controller -> Backend Service
```

2. **NetworkPolicy 限制的是**：
```
Frontend Pod -> Backend Pod
```

如果要限制只允许通过 Ingress 访问，我们需要修改 NetworkPolicy：

```yaml:network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
  namespace: dev
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: ingress-nginx    # 允许来自 ingress-nginx 命名空间的流量
      podSelector:
        matchLabels:
          app.kubernetes.io/name: ingress-nginx         # 匹配 Ingress Controller 的标签
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 3306
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

这样配置后：
1. 允许前端 Pod 访问后端
2. 允许 Ingress Controller 访问后端
3. 允许后端访问数据库和 Redis
4. 拒绝其他所有访问

要测试是否生效：
```bash
# 应用新的网络策略
kubectl apply -f network-policy.yaml

# 创建一个测试 Pod
kubectl run test-pod --image=nginx -n dev

# 尝试从测试 Pod 访问后端（应该失败）
kubectl exec -it test-pod -n dev -- curl backend:80

# 通过 Ingress 访问（应该成功）
curl http://app.local/api/redis-test
```


## 监控和日志
### 1. Prometheus 配置
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-monitor
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: metrics
```

### 2. 日志收集
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      read_from_head true
      <parse>
        @type json
      </parse>
    </source>
```









啊对，抱歉！让我们先给 FastAPI 应用添加监控功能。我们需要修改后端代码来支持 Prometheus 指标收集：

1. **更新 requirements.txt**
````````text:requirements.txt
fastapi==0.68.0
uvicorn==0.15.0
redis==4.5.1
mysqlclient==2.1.1
sqlalchemy==1.4.23
prometheus-fastapi-instrumentator==5.7.1   # 添加这行
````````keyi.lee/work-note/2024/12/k8s/practicals/fastapi-k8s-demo/main.py



2. **修改 main.py**
````````python:main.py
from fastapi import FastAPI
from redis import Redis
from sqlalchemy import create_engine
from prometheus_fastapi_instrumentator import Instrumentator
import os

app = FastAPI()

# 添加 Prometheus 监控
@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)

# Redis 连接
redis_client = Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=6379,
    db=0
)

# MySQL 连接
DATABASE_URL = f"mysql://root:{os.getenv('MYSQL_ROOT_PASSWORD')}@{os.getenv('MYSQL_HOST', 'mysql')}/test"
engine = create_engine(DATABASE_URL)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/redis-test")
def test_redis():
    redis_client.incr('hits')
    return {"hits": int(redis_client.get('hits') or 0)}

@app.get("/mysql-test")
def test_mysql():
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            return {"mysql": "connected"}
    except Exception as e:
        return {"error": str(e)}
````````



3. **重新构建和部署后端**
````````bash
# 构建新镜像
docker build -t localhost:5000/backend:v2 .
docker push localhost:5000/backend:v2

# 更新 deployment
kubectl set image deployment/backend backend=localhost:5000/backend:v2 -n dev
````````



4. **安装简化版的 Prometheus（适用于 minikube 测试）**
````````yaml:prometheus.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: dev
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'backend'
        static_configs:
          - targets: ['backend:80']

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: dev
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus/prometheus.yml
          subPath: prometheus.yml
      volumes:
      - name: config
        configMap:
          name: prometheus-config

---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: dev
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
  type: NodePort
````````



5. **部署并测试**
````````bash
# 应用 Prometheus 配置
kubectl apply -f prometheus.yaml

# 获取 Prometheus 访问地址
minikube service prometheus -n dev

# 测试指标收集
curl http://backend-service/metrics
````````



现在你应该能看到：
1. FastAPI 应用暴露的 metrics 端点
2. 基本的请求统计（如请求数、响应时间等）
3. Prometheus 界面中的指标数据











对的！让我一步步指导你配置 Grafana：

1. **添加 Prometheus 数据源**
```
1. 点击左侧齿轮图标 (Configuration)
2. 选择 "Data sources"
3. 点击 "Add data source"
4. 选择 "Prometheus"
5. URL 填写: http://prometheus:9090
6. 点击 "Save & Test"
```

2. **导入预制仪表板**
```
1. 点击左侧 "+" 图标
2. 选择 "Import"
3. 输入以下仪表板 ID：
   - FastAPI: 14282（FastAPI application dashboard）
   - Redis: 763（Redis Dashboard for Prometheus Redis Exporter）
   - MySQL: 7362（MySQL Overview）
4. 在 "Prometheus" 下拉菜单中选择刚才添加的数据源
5. 点击 "Import"
```

3. **或者创建自定义面板**
```
1. 点击 "Create" -> "Dashboard"
2. 点击 "Add new panel"
3. 在 Query 中添加 Prometheus 查询，例如：
   - FastAPI 请求总数：
     http_requests_total
   - 请求延迟：
     rate(http_request_duration_seconds_sum[5m])
   - Redis 命令：
     redis_commands_total
```

4. **常用指标示例**
```
# FastAPI 指标
- http_requests_total
- http_request_duration_seconds_bucket
- http_request_duration_seconds_count
- http_request_duration_seconds_sum

# Redis 指标
- redis_connected_clients
- redis_commands_total
- redis_memory_used_bytes

# MySQL 指标
- mysql_global_status_queries
- mysql_global_status_threads_connected
- mysql_global_status_bytes_received
```

需要我详细解释某个部分吗？或者你想了解更多关于创建自定义仪表板的内容？


## CI/CD 集成
### 1. Jenkins Pipeline
```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'mvn clean package'
                sh 'docker build -t my-registry/backend:${BUILD_NUMBER} .'
            }
        }
        stage('Test') {
            steps {
                sh 'mvn test'
            }
        }
        stage('Deploy') {
            steps {
                sh 'kubectl set image deployment/backend-api backend=my-registry/backend:${BUILD_NUMBER}'
            }
        }
    }
}
```

### 2. GitLab CI
```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/backend-api backend=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

## 运维管理
### 1. 扩容场景
```bash
# 手动扩容
kubectl scale deployment backend-api --replicas=5

# 自动扩容
kubectl autoscale deployment backend-api --min=2 --max=5 --cpu-percent=80
```

### 2. 版本更新
```bash
# 滚动更新
kubectl set image deployment/backend-api backend=my-registry/backend:v1.1

# 更新状态检查
kubectl rollout status deployment/backend-api

# 回滚
kubectl rollout undo deployment/backend-api
```

### 3. 问题排查
```bash
# 查看 Pod 状态
kubectl get pods -l app=backend

# 查看容器日志
kubectl logs -f deployment/backend-api

# 进入容器调试
kubectl exec -it deployment/backend-api -- /bin/sh

# 查看资源使用
kubectl top pods
```

## 最佳实践总结
1. 配置管理
   - 使用 ConfigMap 和 Secret 管理配置
   - 环境变量集中管理
   - 敏感信息加密存储

2. 高可用设计
   - 合理设置副本数
   - 配置资源限制
   - 实施健康检查
   - 配置自动扩缩容

3. 安全防护
   - 实施网络策略
   - 配置 RBAC 权限
   - 定期安全扫描
   - 镜像安全检查

4. 监控告警
   - 配置资源监控
   - 设置告警规则
   - 日志集中收集
   - 定期性能分析 