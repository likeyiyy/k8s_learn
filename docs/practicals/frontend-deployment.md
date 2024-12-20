关于前端部署，确实有多种方案：

1. **静态文件托管（你提到的方案）**
```
前端文件 -> OSS/CDN -> 用户浏览器
```
优点：
- 成本低
- 性能好（CDN 加速）
- 部署简单
- 易于缓存

2. **Nginx 容器部署（K8s方案）**
```````yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 2
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
        image: nginx:alpine
        volumeMounts:
        - name: static-files
          mountPath: /usr/share/nginx/html
        ports:
        - containerPort: 80
```````
适用场景：
- 需要特定的 Nginx 配置（如 URL 重写、反向代理）
- 需要地理负载均衡
- 需要 SSL 终止
- 需要访问控制
- 需要自定义 HTTP 头

3. **SPA（单页应用）特殊需求**
```````nginx
# nginx.conf
location / {
    try_files $uri $uri/ /index.html;  # 处理前端路由
}

# 反向代理 API
location /api {
    proxy_pass http://backend-service;
}
```````

4. **实际生产环境的混合方案**
```
静态资源 -> OSS/CDN
↓
Nginx（处理路由、SSL、代理）
↓
后端 API
```

所以，总结一下：
1. 如果是纯静态网站，用 OSS/CDN 是最好的选择
2. 如果需要特定的服务器配置，用 Nginx 部署在 K8s 中
3. 大型应用通常采用混合方案：静态文件走 CDN，Nginx 处理动态需求

你的项目具体是哪种情况？我可以帮你设计最合适的方案。


为了让示例完整，我们创建一个最简单的前端页面来调用我们的后端 API：

1. **创建前端项目**
```````bash
mkdir frontend
cd frontend

# 创建一个简单的 index.html
cat > index.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>K8s Demo</title>
</head>
<body>
    <h1>Kubernetes Demo</h1>
    <div>
        <h2>Redis Hits: <span id="hits">0</span></h2>
        <button onclick="checkRedis()">Test Redis</button>
    </div>
    <div>
        <h2>MySQL Status: <span id="mysql">Unknown</span></h2>
        <button onclick="checkMySQL()">Test MySQL</button>
    </div>

    <script>
    async function checkRedis() {
        const response = await fetch('/api/redis-test');
        const data = await response.json();
        document.getElementById('hits').textContent = data.hits;
    }

    async function checkMySQL() {
        const response = await fetch('/api/mysql-test');
        const data = await response.json();
        document.getElementById('mysql').textContent = 
            data.mysql ? 'Connected' : 'Error';
    }
    </script>
</body>
</html>
EOF

# 创建 Dockerfile
cat > Dockerfile << EOF
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EOF

# 创建 nginx 配置
cat > nginx.conf << EOF
server {
    listen 80;
    server_name localhost;

    location / {
        root   /usr/share/nginx/html;
        index  index.html;
    }

    location /api/ {
        proxy_pass http://backend.dev.svc.cluster.local/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF
```````


2. **构建和推送前端镜像**
```````bash
# 确保在 minikube 环境
eval $(minikube docker-env)

# 构建镜像
docker build -t localhost:5000/frontend:v1 .
docker push localhost:5000/frontend:v1
```````


3. **创建前端 Deployment**
```````yaml:frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: dev
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
      - name: frontend
        image: localhost:5000/frontend:v1
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```````


4. **创建前端 Service**
```````yaml:frontend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: dev
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: NodePort
```````


5. **应用配置**
```````bash
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml

# 获取访问 URL
minikube service frontend -n dev
```````


这个示例展示了：
1. 前端如何通过 Nginx 代理访问后端 API
2. 完整的前后端分离架构
3. 服务之间的通信
4. 资源限制和标签的使用

访问生成的 URL 后，你应该能看到一个简单的页面，可以测试 Redis 和 MySQL 的连接。

