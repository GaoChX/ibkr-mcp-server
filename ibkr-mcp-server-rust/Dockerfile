# 多阶段构建 - 优化镜像大小
FROM rust:1.75-slim as builder

WORKDIR /app

# 复制依赖文件
COPY Cargo.toml Cargo.lock ./

# 创建虚拟 main.rs 以缓存依赖
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# 复制源代码
COPY src ./src

# 构建应用（会使用缓存的依赖）
RUN cargo build --release

# 运行时镜像
FROM debian:bookworm-slim

# 安装运行时依赖
RUN apt-get update && \
    apt-get install -y ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 从构建阶段复制二进制文件
COPY --from=builder /app/target/release/ibkr-mcp-server /usr/local/bin/ibkr-mcp-server

# 复制配置文件
COPY .env.example .env

# 创建非 root 用户
RUN useradd -m -u 1000 ibkr && \
    chown -R ibkr:ibkr /app

USER ibkr

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 暴露端口
EXPOSE 8080

# 启动应用
CMD ["ibkr-mcp-server"]
