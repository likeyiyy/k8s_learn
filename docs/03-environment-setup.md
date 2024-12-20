# 3. K8s 环境搭建

## Minikube 本地环境
### 系统要求
- CPU：2核心及以上
- 内存：2GB 及以上
- 硬盘空间：20GB 及以上
- 网络连接：能访问外网
- 虚拟化支持：
  - Linux: KVM
  - macOS: HyperKit
  - Windows: Hyper-V 或 VirtualBox

### 安装步骤
1. 安装虚拟化支持
```bash
# Linux 检查 KVM
egrep -c '(vmx|svm)' /proc/cpuinfo
# 如果输出 > 0，表示支持虚拟化

# 安装 KVM
sudo apt-get install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils
```

2. 安装 Minikube
```bash
# Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# MacOS
brew install minikube

# Windows (PowerShell)
New-Item -Path 'c:\' -Name 'minikube' -ItemType Directory
Invoke-WebRequest -OutFile 'c:\minikube\minikube.exe' -Uri 'https://github.com/kubernetes/minikube/releases/latest/download/minikube-windows-amd64.exe'
```

3. 启动集群
```bash
# 使用 Docker 驱动
minikube start --driver=docker

# 指定 Kubernetes 版本
minikube start --kubernetes-version=v1.24.0

# 配置资源
minikube start --cpus=4 --memory=8192mb
```

### 常用命令详解
```bash
# 查看集群状态
minikube status

# 访问 Dashboard
minikube dashboard

# 管理插件
minikube addons list
minikube addons enable ingress
minikube addons enable metrics-server

# 访问集群服务
minikube service list
minikube service myapp-service

# 隧道创建（用于 LoadBalancer 类型服务）
minikube tunnel
```

## kubectl 命令行工具
### 安装配置
1. 安装 kubectl
```bash
# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# MacOS
brew install kubectl

# Windows (PowerShell)
curl -LO "https://dl.k8s.io/release/v1.24.0/bin/windows/amd64/kubectl.exe"
```

2. 配置自动补全
```bash
# Bash
echo 'source <(kubectl completion bash)' >>~/.bashrc

# Zsh
echo 'source <(kubectl completion zsh)' >>~/.zshrc
```

### 配置文件管理
```bash
# 查看当前配置
kubectl config view

# 切换上下文
kubectl config use-context minikube

# 设置命名空间
kubectl config set-context --current --namespace=myapp
```

### 基本操作命令
1. 资源管理
```bash
# 创建资源
kubectl create deployment nginx --image=nginx

# 应用配置文件
kubectl apply -f manifest.yaml

# 查看资源
kubectl get pods
kubectl get services
kubectl get deployments

# 删除资源
kubectl delete deployment nginx
```

2. 调试命令
```bash
# 查看日志
kubectl logs pod-name
kubectl logs -f deployment/nginx

# 进入容器
kubectl exec -it pod-name -- /bin/bash

# 端口转发
kubectl port-forward service/nginx 8080:80

# 复制文件
kubectl cp pod-name:/path/to/file ./local-file
```

## K8s 集群搭建
### 使用 kubeadm 搭建
1. 前置条件
```bash
# 关闭 Swap
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

# 配置内核参数
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter
```

2. 安装容器运行时
```bash
# 安装 containerd
sudo apt-get update
sudo apt-get install -y containerd.io

# 配置 containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
```

3. 安装 kubeadm、kubelet 和 kubectl
```bash
# 添加 Kubernetes 仓库
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-archive-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list

# 安装组件
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

4. 初始化集群
```bash
# 主节点初始化
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# 配置 kubectl
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# 安装网络插件（以 Calico 为例）
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```

### 集群验证
```bash
# 检查节点状态
kubectl get nodes

# 检查系统组件
kubectl get pods -n kube-system

# 部署测试应用
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80 --type=NodePort
```

## 常见问题解决
### 安装问题
1. Minikube 启动失败
```bash
# 清理旧的配置
minikube delete
rm -rf ~/.minikube

# 使用调试模式启动
minikube start --v=7 --alsologtostderr
```

2. kubectl 连接问题
```bash
# 检查配置
kubectl config view
kubectl cluster-info

# 重置配置
rm ~/.kube/config
minikube update-context
```

### 网络问题
1. Pod 网络问题
```bash
# 检查 DNS
kubectl run busybox --rm -it --image=busybox -- nslookup kubernetes.default

# 检查网络插件
kubectl get pods -n kube-system | grep calico
```

2. 服务访问问题
```bash
# 检查服务状态
kubectl get svc
kubectl describe svc my-service

# 检查端点
kubectl get endpoints my-service
```

## 环境维护
### 日常维护
- 定期更新组件
- 监控资源使用
- 备份配置文件
- 清理未使用资源

### 升级建议
- 遵循版本兼容性
- 先测试环境验证
- 准备回滚方案
- 记录升级日志