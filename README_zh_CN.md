# IBKR MCP Server

一个基于 FastMCP 2.0 和 MCP StreamableHTTP 的 Interactive Brokers (IBKR) MCP 服务器实现，提供账户管理、交易操作和市场数据查询功能。

## 功能特性

- 🔗 **连接管理**: 与 IBKR TWS/Gateway 的稳定连接
- 📊 **账户信息**: 查询账户摘要、持仓和余额
- 💹 **交易操作**: 下单、撤单、查询订单状态
- 📈 **市场数据**: 实时和历史市场数据获取
- 🛡️ **类型安全**: 使用 Pydantic 进行数据验证
- ⚡ **异步架构**: 高性能异步 I/O 操作
- 📝 **丰富日志**: 结构化日志记录
- 🔧 **配置灵活**: 支持环境变量和配置文件

## 安装

### 从源码安装

```bash
git clone https://github.com/yourusername/ibkr-mcp-server.git
cd ibkr-mcp-server
pip install -e .
```

### 开发环境设置

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 设置预提交钩子
pre-commit install
```

## 快速开始

### 1. 配置环境

```bash
# 创建配置文件
ibkr-mcp-server config --init

# 编辑 .env 文件
# 设置 IBKR 连接参数
```

### 2. 测试连接

```bash
# 测试 IBKR 连接
ibkr-mcp-server test --host 127.0.0.1 --port 4002
```

### 3. 启动服务器

```bash
# 启动服务器
ibkr-mcp-server serve

# 或使用自定义参数
ibkr-mcp-server serve --host 0.0.0.0 --port 8080 --debug
```

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MCP__HOST` | `0.0.0.0` | MCP 服务器监听地址 |
| `MCP__PORT` | `8080` | MCP 服务器端口 |
| `IBKR__HOST` | `127.0.0.1` | IBKR TWS/Gateway 地址 |
| `IBKR__PORT` | `4002` | IBKR TWS/Gateway 端口 |
| `IBKR__CLIENT_ID` | `1` | IBKR 客户端 ID |
| `IBKR__READONLY` | `false` | 只读模式 |
| `LOGGING__LEVEL` | `INFO` | 日志级别 |

### 配置文件示例

```env
# MCP 服务器设置
MCP__HOST=0.0.0.0
MCP__PORT=8080

# IBKR 连接设置
IBKR__HOST=127.0.0.1
IBKR__PORT=4002
IBKR__CLIENT_ID=1
IBKR__READONLY=false

# 日志设置
LOGGING__LEVEL=INFO
```

## MCP 工具

### 账户管理

- `get_account_summary`: 获取账户摘要信息
- `get_positions`: 获取持仓信息

### 交易操作

- `place_order`: 下单
- `cancel_order`: 撤单
- `get_open_orders`: 获取开放订单

### 市场数据

- `get_market_data`: 获取实时市场数据
- `get_historical_data`: 获取历史数据

### 连接管理

- `connection_status`: 检查连接状态
- `reconnect`: 重新连接

## 使用示例

### 下单示例

```python
# 通过 MCP 工具下单
{
    "tool": "place_order",
    "arguments": {
        "symbol": "AAPL",
        "sec_type": "STK",
        "action": "BUY",
        "quantity": 100,
        "order_type": "LMT",
        "limit_price": 150.0
    }
}
```

### 获取持仓

```python
# 获取账户持仓
{
    "tool": "get_positions",
    "arguments": {}
}
```

### 获取历史数据

```python
# 获取历史数据
{
    "tool": "get_historical_data",
    "arguments": {
        "symbol": "AAPL",
        "duration": "1 D",
        "bar_size": "1 min"
    }
}
```

## 架构设计

```
┌─────────────────────┐
│   MCP Client        │
└─────────┬───────────┘
          │ HTTP/WebSocket
┌─────────┴───────────┐
│   FastMCP Server    │
├─────────────────────┤
│   IBKR MCP Server   │
├─────────────────────┤
│   IBKR Client       │
└─────────┬───────────┘
          │ TWS API
┌─────────┴───────────┐
│   TWS/Gateway       │
└─────────────────────┘
```

## 开发指南

### 项目结构

```
src/ibkr_mcp_server/
├── __init__.py          # 包初始化
├── server.py            # MCP 服务器实现
├── client.py            # IBKR 客户端包装
├── models.py            # 数据模型
├── config.py            # 配置管理
├── exceptions.py        # 异常定义
└── cli.py              # 命令行界面
```

### 代码规范

- 使用 `black` 进行代码格式化
- 使用 `isort` 进行导入排序
- 使用 `flake8` 进行代码检查
- 使用 `mypy` 进行类型检查

### 测试

```bash
# 运行测试
pytest

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 部署

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install .

EXPOSE 8080

CMD ["ibkr-mcp-server", "serve"]
```

### Systemd 服务

```ini
[Unit]
Description=IBKR MCP Server
After=network.target

[Service]
Type=simple
User=ibkr
WorkingDirectory=/opt/ibkr-mcp-server
Environment=PYTHONPATH=/opt/ibkr-mcp-server
ExecStart=/usr/local/bin/ibkr-mcp-server serve
Restart=always

[Install]
WantedBy=multi-user.target
```

## 注意事项

1. **TWS/Gateway**: 确保 IBKR TWS 或 Gateway 正在运行并开启 API 连接
2. **端口配置**: 确保 TWS/Gateway API 端口与配置一致
3. **权限**: 确保账户具有相应的交易权限
4. **风险管理**: 在生产环境中使用时请注意风险控制

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交 Pull Request 和 Issue！

## 支持

如有问题，请提交 [Issue](https://github.com/yourusername/ibkr-mcp-server/issues) 