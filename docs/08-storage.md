# 8. Kubernetes 存储

## 存储概念
### 持久卷（PV）
- 集群级别的存储资源
- 生命周期独立于 Pod
- 支持多种存储类型
- 容量和访问模式

### 持久卷声明（PVC）
- 用户存储请求
- 与 PV 的绑定关系
- 命名空间级别资源
- 动态供应支持

### 存储类（StorageClass）
- 存储资源的抽象
- 动态供应配置
- 不同服务质量
- 回收策略

## 存储类型
### 本地存储
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-pv
spec:
  capacity:
    storage: 100Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: local-storage
  local:
    path: /mnt/disks/vol1
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - node-1
```

### 网络存储
- NFS 配置
- Ceph 集成
- 云存储对接

## 动态供应
### StorageClass 配置
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp2
reclaimPolicy: Delete
allowVolumeExpansion: true
```

### 自动供应流程
- PVC 创建
- StorageClass 选择
- PV 自动创建
- 存储绑定

## 数据备份与恢复
### 备份策略
- 定期快照
- 增量备份
- 跨区域复制
- 数据验证

### 恢复流程
- 快照恢复
- 数据迁移
- 一致性检查
- 应用恢复

### 最佳实践
- 容量规划
- 性能优化
- 高可用配置
- 安全防护 