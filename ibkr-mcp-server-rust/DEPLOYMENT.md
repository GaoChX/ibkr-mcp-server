# IBKR MCP Server (Rust) 部署指南

## 🚀 快速开始

### 本地运行

```bash
# 1. 克隆项目
git clone <repository>
cd ibkr-mcp-server-rust

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置 IBKR 连接参数

# 3. 运行
cargo run --release
```

### Docker 部署

```bash
# 方式一: 使用脚本
./docker-run.sh

# 方式二: 手动构建和运行
docker build -t ibkr-mcp-server-rust .
docker run -d -p 8080:8080 --env-file .env ibkr-mcp-server-rust

# 方式三: 使用 docker-compose
docker-compose up -d
```

## 📋 环境变量配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `IBKR__HOST` | 127.0.0.1 | IBKR TWS/Gateway 地址 |
| `IBKR__PORT` | 4002 | IBKR 端口 (4002=纸盘, 7497=实盘) |
| `IBKR__CLIENT_ID` | 1 | 客户端ID |
| `IBKR__READONLY` | false | 只读模式 |
| `IBKR__MCP__HOST` | 0.0.0.0 | MCP 服务器监听地址 |
| `IBKR__MCP__PORT` | 8080 | MCP 服务器端口 |
| `IBKR__LOGGING__LEVEL` | info | 日志级别 |
| `IBKR__ENVIRONMENT` | development | 环境标识 |

## 🔧 开发

### 运行测试

```bash
# 所有测试
cargo test

# 集成测试
cargo test --test integration_tests

# 带输出
cargo test -- --nocapture
```

### 代码检查

```bash
# 格式化
cargo fmt

# Lint
cargo clippy

# 构建文档
cargo doc --no-deps --open
```

### 性能测试

```bash
# Release 构建
cargo build --release

# 运行 benchmark (如果有)
cargo bench
```

## 🐳 Docker

### 构建优化

多阶段构建，最终镜像 < 50MB：

```dockerfile
FROM rust:1.75-slim as builder
# ... 构建
FROM debian:bookworm-slim
# ... 运行
```

### 健康检查

```bash
# Docker 内部健康检查
curl -f http://localhost:8080/health || exit 1

# k8s liveness probe
httpGet:
  path: /health
  port: 8080
```

### 资源限制

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

## ☸️ Kubernetes 部署

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ibkr-mcp-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ibkr-mcp-server
  template:
    metadata:
      labels:
        app: ibkr-mcp-server
    spec:
      containers:
      - name: server
        image: your-registry/ibkr-mcp-server:latest
        ports:
        - containerPort: 8080
        env:
        - name: IBKR__HOST
          valueFrom:
            configMapKeyRef:
              name: ibkr-config
              key: host
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /mcp/status
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ibkr-mcp-service
spec:
  selector:
    app: ibkr-mcp-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

## 🔐 安全建议

1. **不要在生产环境暴露 HTTP 端点**
   - 使用反向代理 (Nginx/Traefik)
   - 启用 TLS/HTTPS
   - 添加认证中间件

2. **环境变量安全**
   - 使用 Secret 管理敏感信息
   - 不要提交 .env 到版本控制

3. **网络隔离**
   - 使用私有网络连接 IBKR
   - 限制入站流量

## 📊 监控

### Prometheus 指标

未来可添加:
```rust
use prometheus::{Registry, Counter, Histogram};

// 请求计数
let requests = Counter::new("http_requests_total", "Total requests")?;

// 延迟直方图
let latency = Histogram::new("request_duration_seconds", "Request latency")?;
```

### 日志聚合

使用 tracing-subscriber 的 JSON 格式：

```bash
IBKR__LOGGING__FORMAT=json cargo run
```

适配 ELK/Loki 等日志系统。

## 🔄 CI/CD

GitHub Actions workflow 已配置：

- ✅ 代码格式检查 (rustfmt)
- ✅ Lint (clippy)
- ✅ 测试运行
- ✅ Release 构建
- ✅ Docker 镜像推送

### 手动触发

```bash
# 触发 CI
git push origin main

# 构建特定版本
git tag v1.0.0
git push origin v1.0.0
```

## 🐛 故障排查

### 常见问题

**1. 连接 IBKR 失败**
```
Error: IBKR connection error
```
解决：
- 检查 TWS/Gateway 是否运行
- 验证端口和 client_id
- 确认 API 设置已启用

**2. 端口被占用**
```
Error: Address already in use
```
解决：
```bash
# 查找占用进程
lsof -i :8080
# 杀掉进程或更改端口
```

**3. Docker 构建慢**
解决：
- 使用 BuildKit: `DOCKER_BUILDKIT=1 docker build .`
- 清理缓存: `docker system prune -a`

### 查看日志

```bash
# Cargo run
RUST_LOG=debug cargo run

# Docker
docker logs -f ibkr-mcp-server

# Docker Compose
docker-compose logs -f
```

## 📈 性能优化

### 编译优化

```toml
[profile.release]
opt-level = 3        # 最大优化
lto = true          # Link-time optimization
codegen-units = 1   # 单编译单元
strip = true        # 移除符号
```

### 运行时优化

```bash
# 增加 worker 线程
TOKIO_WORKER_THREADS=8 cargo run

# 调整栈大小
RUST_MIN_STACK=8388608 cargo run
```

## 📚 更多资源

- [Rust Documentation](https://doc.rust-lang.org/)
- [Tokio Guide](https://tokio.rs/tokio/tutorial)
- [Axum Documentation](https://docs.rs/axum/)
- [IBKR API Docs](https://interactivebrokers.github.io/tws-api/)

## 🤝 贡献

欢迎贡献！请参考贡献指南。

## 📄 许可证

MIT License
