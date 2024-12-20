# 7. Kubernetes 网络

## 基础网络概念
### 什么是容器网络？
容器网络是为容器提供网络连接的系统。在 Kubernetes 中，每个 Pod 都有自己的网络命名空间，这个命名空间包含：
- 自己的网络接口
- IP 地址
- 路由表
- 网络规则

### 网络命名空间（Network Namespace）
#### 概念解释
网络命名空间是 Linux 内核提供的网络隔离机制，它允许：
- 不同命名空间有独立的网络栈
- 独立的路由表
- 独立的防火墙规则
- 独立的网络设备

#### 实际演示
```bash
# 创建网络命名空间
ip netns add ns1

# 查看网络命名空间
ip netns list

# 在命名空间中执行命令
ip netns exec ns1 ip addr

# 创建虚拟网络设备对
ip link add veth0 type veth peer name veth1

# 将设备移动到命名空间
ip link set veth1 netns ns1
```

### 网络通信原理
#### 1. 容器到容器（同一个 Pod 内）
- 共享网络命名空间
- 通过 localhost 通信
- 直接访问对方端口

示例：
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-pod
spec:
  containers:
  - name: web
    image: nginx
  - name: sidecar
    image: busybox
    command: ['sh', '-c', 'while true; do wget -q -O- http://localhost:80; sleep 5; done']
```

#### 2. Pod 到 Pod（同一个节点）
- 通过虚拟网桥通信
- 直接路由
- 扁平网络

网络流程图：
```ascii
Pod1 [veth0] <--> [bridge] <--> [veth1] Pod2
```

配置示例：
```bash
# 查看网桥配置
bridge link show

# 查看 Pod 网络接口
kubectl exec -it pod-name -- ip addr

# 测试 Pod 间通信
kubectl exec -it pod1 -- ping <pod2-ip>
```

#### 3. Pod 到 Pod（跨节点）
- 通过 CNI 插件实现
- 需要配置路由规则
- 可能需要封装协议


## CNI（容器网络接口）详解

### 为什么需要 CNI？
#### 1. 设计理念
Kubernetes 在设计之初就秉承了以下理念：
- 关注点分离：核心功能和网络实现解耦
- 可插拔架构：支持不同的网络方案
- 标准化接口：统一的网络配置标准

#### 2. 不同场景的需求
不同的使用场景对网络有不同的需求：
- 公有云环境：需要与云服务商的网络方案集成
- 私有化部署：可能需要与现有网络基础设施整合
- 混合云环境：需要支持跨云网络通信
- 高性能计算：对网络延迟和带宽有特殊要求

#### 3. CNI 带来的好处
1. 对于用户
   - 可以根据需求选择合适的网络方案
   - 可以平滑切换网络实现
   - 降低网络配置的复杂度

2. 对于开发者
   - 专注于网络功能实现
   - 不需要修改 Kubernetes 代码
   - 可以复用现有的网络方案

3. 对于运维人员
   - 统一的配置方式
   - 标准化的故障排查流程
   - 便于管理和维护

### CNI 的本质
CNI（Container Network Interface）是一个标准化的接口规范，它定义了：
1. 容器运行时和网络插件之间如何通信
2. 网络插件的实现规范
3. 容器网络的配置方式

### CNI 的工作流程
#### 1. 基本流程
```ascii
容器运行时 --> CNI Plugin --> 网络配置 --> 网络命名空间
     |            |              |            |
     |            |              |            |
  创建容器    调用插件接口    应用配置     配置网络
```

#### 2. 详细步骤
1. 容器创建时：
   ```bash
   # 1. 创建网络命名空间
   ip netns add <container-ns>
   
   # 2. CNI 插件被调用
   # 环境变量设置
   CNI_COMMAND=ADD
   CNI_CONTAINERID=<container-id>
   CNI_NETNS=/var/run/netns/<container-ns>
   CNI_IFNAME=eth0
   CNI_PATH=/opt/cni/bin
   
   # 3. 执行插件
   /opt/cni/bin/bridge < /etc/cni/net.d/10-bridge.conf
   ```

2. 容器删除时：
   ```bash
   # 环境变量设置
   CNI_COMMAND=DEL
   # ... 其他变量同上
   
   # 清理网络资源
   /opt/cni/bin/bridge < /etc/cni/net.d/10-bridge.conf
   ```

### CNI 规范详解
#### 1. 插件职责
- 创建容器网络接口
- 管理 IP 地址分配
- 配置路由规则
- 实现网络策略

#### 2. 接口定义
```go
type CNI interface {
    AddNetworkList (net *NetworkConfigList, rt *RuntimeConf) (types.Result, error)
    DelNetworkList (net *NetworkConfigList, rt *RuntimeConf) error
    AddNetwork (net *NetworkConfig, rt *RuntimeConf) (types.Result, error)
    DelNetwork (net *NetworkConfig, rt *RuntimeConf) error
}
```

#### 3. 配置规范
```json
{
    "cniVersion": "0.4.0",
    "name": "dbnet",
    "type": "bridge",
    // 插件特定配置
    "bridge": "cni0",
    "ipam": {
        "type": "host-local",
        "subnet": "10.1.0.0/16",
        "gateway": "10.1.0.1"
    },
    "dns": {
        "nameservers": ["10.1.0.1"]
    },
    // 高级特性
    "prevResult": {},           // 链式插件前一个结果
    "runtimeConfig": {},        // 运行时配置
    "capabilities": {},         // 插件能力声明
}
```

### CNI 插件类型
#### 1. 主网络插件
- bridge：创建网桥
- ipvlan：使用 ipvlan 驱动
- macvlan：使用 macvlan 驱动
- ptp：创建 veth 对
- host-device：移动主机网络设备

#### 2. IPAM 插件
- dhcp：使用 DHCP 分配 IP
- host-local：使用本地文件管理 IP
- static：静态 IP 配置

#### 3. Meta 插件
- flannel：配合 Flannel 使用
- tuning：调整现有接口
- portmap：端口映射
- bandwidth：带宽限制



### 常见 CNI 插件对比
#### 1. Calico
特点：
- 基于 BGP 的路由方案
- 支持网络策略
- 高性能，无封装开销
- 支持加密通信

配置示例：
```yaml
apiVersion: projectcalico.org/v3
kind: IPPool
metadata:
  name: default-ipv4-ippool
spec:
  cidr: 192.168.0.0/16
  ipipMode: Always
  natOutgoing: true
```

#### 2. Flannel
特点：
- 简单易用
- 使用 VXLAN 封装
- 适合小型集群
- 配置简单

配置示例：
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kube-flannel-cfg
data:
  net-conf.json: |
    {
      "Network": "10.244.0.0/16",
      "Backend": {
        "Type": "vxlan"
      }
    }
```

#### 3. Cilium
特点：
- 基于 eBPF
- 高性能
- 支持 L7 策略
- 强大的监控能力

配置示例：
```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: http-policy
spec:
  endpointSelector:
    matchLabels:
      app: web
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP
      rules:
        http:
        - method: GET
          path: "/api/v1/"
```

### CNI 插件开发
#### 1. 基本结构
```go
package main

import (
    "github.com/containernetworking/cni/pkg/skel"
    "github.com/containernetworking/cni/pkg/version"
)

func cmdAdd(args *skel.CmdArgs) error {
    // 实现添加网络逻辑
    return nil
}

func cmdDel(args *skel.CmdArgs) error {
    // 实现删除网络逻辑
    return nil
}

func main() {
    skel.PluginMain(cmdAdd, cmdDel, version.All)
}
```

#### 2. 关键功能实现
```go
// 创建网络接口
func setupVeth(netns ns.NetNS, ifName string) (*current.Interface, *current.Interface, error) {
    hostInterface := &current.Interface{}
    containerInterface := &current.Interface{}
    
    err := netns.Do(func(hostNS ns.NetNS) error {
        // 创建 veth 对
        hostVeth, containerVeth, err := ip.SetupVeth(ifName, 1500, hostNS)
        if err != nil {
            return err
        }
        
        hostInterface.Name = hostVeth.Name
        containerInterface.Name = containerVeth.Name
        return nil
    })
    return hostInterface, containerInterface, err
}
```

### CNI 调试和故障排查
#### 1. 配置验证
```bash
# 检查 CNI 配置
cat /etc/cni/net.d/10-bridge.conf

# 验证 CNI 插件
CNI_PATH=/opt/cni/bin cnitool add mynet /var/run/netns/test

# 查看 CNI 日志
journalctl -u kubelet | grep cni
```

#### 2. 网络调试
```bash
# 检查网络接口
ip link show

# 查看路由表
ip route

# 检查 iptables 规则
iptables-save | grep CNI

# 使用 tcpdump 抓包
tcpdump -i cni0
```

#### 3. 常见问题
1. IP 地址分配失败
```bash
# 检查 IPAM 数据
ls /var/lib/cni/networks/

# 清理 IPAM 数据
rm -rf /var/lib/cni/networks/*
```

2. 网络接口创建失败
```bash
# 检查系统日志
dmesg | grep veth

# 验证内核模块
lsmod | grep bridge
```

3. 路由问题
```bash
# 检查节点路由
ip route show

# 验证 Pod 路由
nsenter -t <container-pid> -n ip route
```