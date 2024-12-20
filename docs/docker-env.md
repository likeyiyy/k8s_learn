# Docker 环境切换

让我们理清这两个 Docker 环境：

1. **本地 Docker 环境**
   - 直接运行在你的主机上
   - 使用 `~/.docker/config.json` 的配置
   - 默认情况下的 Docker 命令都是指向这个环境

2. **Minikube 的 Docker 环境**
   - 运行在 minikube 虚拟机中
   - 需要通过 `eval $(minikube docker-env)` 切换到这个环境
   - 配置需要通过 minikube 的启动参数来设置

可以通过这些命令来回切换：
```bash
# 切换到 minikube 的 Docker
eval $(minikube docker-env)

# 切换回本地 Docker
eval $(minikube docker-env -u)
```

一个实用的建议是：在使用 Docker 命令之前，可以先检查一下当前指向哪个环境：
```bash
docker info | grep "Server Version"
# 或
echo $DOCKER_HOST
```
