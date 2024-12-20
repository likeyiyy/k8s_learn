让我们用 FastAPI 创建一个最小的测试项目，它会同时使用到 MySQL 和 Redis：

1. **创建项目结构**
```````bash
mkdir fastapi-k8s-demo
cd fastapi-k8s-demo

# 创建项目文件
touch main.py requirements.txt Dockerfile
```````

2. **requirements.txt**
```````text
fastapi==0.68.0
uvicorn==0.15.0
redis==4.5.1
mysqlclient==2.1.1
sqlalchemy==1.4.23
```````

3. **main.py**
```````python
from fastapi import FastAPI
from redis import Redis
from sqlalchemy import create_engine
import os

app = FastAPI()

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
```````

4. **Dockerfile**
```````Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y default-libmysqlclient-dev build-essential && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```````

5. **构建和推送镜像**
```````bash
# 确保在 minikube 的 docker 环境中
eval $(minikube docker-env)

# 构建镜像
docker build -t localhost:5000/backend:v1 .
docker push localhost:5000/backend:v1
```````

6. **创建后端服务的 Deployment**
```````yaml:backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: dev
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
        image: localhost:5000/backend:v1
        ports:
        - containerPort: 8000
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        - name: MYSQL_HOST
          value: "mysql"
        - name: REDIS_HOST
          value: "redis"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```````

7. **创建 Service**
```````yaml:backend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: dev
spec:
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 8000
  type: NodePort
```````

8. **应用配置**
```````bash
# 应用部署
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml

# 获取服务 URL
minikube service backend -n dev
```````

9. **测试 API 端点**
```````bash
# 测试基本连接
curl http://<service-url>/

# 测试 Redis 连接
curl http://<service-url>/redis-test

# 测试 MySQL 连接
curl http://<service-url>/mysql-test
```````

这个最小示例：
1. 使用了我们之前设置的 MySQL 和 Redis
2. 符合网络策略的要求
3. 包含了资源限制
4. 提供了简单的测试端点





是的，`minikube service` 是 minikube 提供的一个便捷命令，它会：
1. 自动创建一个到 NodePort 服务的隧道
2. 返回一个可访问的 URL

在正式的 Kubernetes 环境中，访问服务有几种常见方式：

1. **通过 LoadBalancer**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  type: LoadBalancer    # 修改类型为 LoadBalancer
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 8000
```
- 云环境会自动分配外部 IP
- 可以通过 `kubectl get svc` 查看外部 IP


2. **通过 Ingress**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: backend-ingress
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 80
```
- 需要配置 DNS 解析
- 需要安装 Ingress Controller


3. **通过 NodePort**
```bash
# 获取节点 IP
kubectl get nodes -o wide

# 获取服务端口
kubectl get svc backend

# 访问格式
http://<node-ip>:<node-port>
```


4. **通过端口转发（开发测试用）**
```bash
# 直接转发到 Pod
kubectl port-forward pod/<pod-name> 8080:8000

# 或转发到服务
kubectl port-forward svc/backend 8080:80
```


生产环境最佳实践：
1. 内部服务使用 ClusterIP
2. 外部访问使用 Ingress
3. LoadBalancer 用于特殊场景
4. NodePort 主要用于测试





让我们来排查 Redis 连接问题：

1. **首先检查 Redis Pod 状态**
```````bash
# 检查 Redis Pod
kubectl get pods -l app=redis -n dev

# 查看 Redis Pod 详细信息
kubectl describe pod -l app=redis -n dev

# 查看 Redis 日志
kubectl logs -l app=redis -n dev
```````


2. **检查 Redis Service**
```````bash
# 检查 Redis Service 是否存在
kubectl get svc -n dev | grep redis

# 如果没有 Service，需要创建一个
```````


创建 Redis Service：
```````yaml:redis-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: dev
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
```````


3. **测试 Redis 连接**
```````bash
# 进入后端 Pod 测试 Redis 连接
kubectl exec -it $(kubectl get pod -l app=backend -n dev -o jsonpath='{.items[0].metadata.name}') -n dev -- sh

# 在 Pod 内安装 redis-cli（如果需要）
apt-get update && apt-get install -y redis-tools

# 测试连接
redis-cli -h redis ping
```````


4. **检查网络策略**
确保网络策略允许后端访问 Redis：
```````yaml:network-policy.yaml
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
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```````


5. **如果还有问题，可以临时禁用网络策略进行测试**
```````bash
kubectl delete networkpolicy backend-policy -n dev
```````








是的！MySQL 也需要一个 Service。让我们创建 MySQL 的 Service：

```yaml:mysql-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql    # 这个名字要和代码中的 MYSQL_HOST 环境变量匹配
  namespace: dev
spec:
  selector:
    app: database    # 注意这里要匹配我们之前给 MySQL StatefulSet 设置的标签
  ports:
  - port: 3306
    targetPort: 3306
  type: ClusterIP
```



应用配置：
```bash
kubectl apply -f mysql-service.yaml

# 验证 Service 创建
kubectl get svc -n dev

# 测试连接
kubectl exec -it $(kubectl get pod -l app=backend -n dev -o jsonpath='{.items[0].metadata.name}') -n dev -- sh
# 在 pod 内
curl mysql:3306
```



现在我们有：
1. Redis Service: redis:6379
2. MySQL Service: mysql:3306
3. Backend Service: backend:80







啊，这个错误是因为我们还没有创建 `test` 数据库。让我们连接到 MySQL 并创建数据库：

````bash
# 进入 MySQL Pod
kubectl exec -it $(kubectl get pod -l app=database -n dev -o jsonpath='{.items[0].metadata.name}') -n dev -- bash

# 连接到 MySQL（使用之前在 secret 中设置的密码）
mysql -u root -p

# 在 MySQL 命令行中创建数据库
CREATE DATABASE test;

# 验证数据库创建
SHOW DATABASES;

# 退出 MySQL
exit
````


或者用一行命令：
````bash
kubectl exec -it $(kubectl get pod -l app=database -n dev -o jsonpath='{.items[0].metadata.name}') -n dev -- mysql -u root -p$MYSQL_ROOT_PASSWORD -e 'CREATE DATABASE test;'
````


创建完数据库后，再次测试后端连接：
````bash
curl http://<service-url>/mysql-test
````
