# IBKR MCP Server - 下一步实施指南

## 当前状态

✅ **Phase 1 完成**: 项目架构、基础模块、HTTP 服务器
🔄 **Phase 2 进行中**: IBKR API 实际集成

## Phase 2 详细实施步骤

### 1. 理解 ibapi Crate 架构

`ibapi` crate 是一个事件驱动的异步库，主要组件：

- **Client**: 主要的 API 客户端
- **订阅模式**: 使用回调处理 API 响应
- **模块**:
  - `accounts`: 账户相关
  - `orders`: 订单管理
  - `market_data`: 市场数据
  - `contracts`: 合约定义

### 2. 连接管理实现

需要实现实际的 IBKR 连接逻辑：

```rust
use ibapi::Client as IBClient;

pub struct IBKRClient {
    config: IBKRConfig,
    client: Arc<RwLock<Option<IBClient>>>,
}

impl IBKRClient {
    pub async fn connect(&self) -> Result<()> {
        let mut client = IBClient::connect(
            &self.config.host,
            self.config.port as u16,
            self.config.client_id,
        ).await?;
        
        // 等待连接确认
        tokio::time::sleep(Duration::from_secs(1)).await;
        
        let mut client_guard = self.client.write().await;
        *client_guard = Some(client);
        
        Ok(())
    }
}
```

### 3. 账户摘要实现

使用订阅模式获取账户信息：

```rust
pub async fn get_account_summary(&self) -> Result<Vec<AccountSummary>> {
    let client_guard = self.client.read().await;
    let client = client_guard.as_ref()
        .ok_or(IBKRMCPError::NotConnected)?;
    
    // 创建订阅
    let mut subscription = client.account_summary(
        AccountSummaryTags::default()
    ).await?;
    
    // 收集结果
    let mut summaries = Vec::new();
    while let Some(summary) = subscription.next().await {
        summaries.push(summary?);
    }
    
    Ok(summaries)
}
```

### 4. 持仓信息实现

```rust
pub async fn get_positions(&self) -> Result<Vec<Position>> {
    let client_guard = self.client.read().await;
    let client = client_guard.as_ref()
        .ok_or(IBKRMCPError::NotConnected)?;
    
    let mut subscription = client.positions().await?;
    
    let mut positions = Vec::new();
    while let Some(pos) = subscription.next().await {
        let pos = pos?;
        positions.push(Position {
            account: pos.account,
            contract: convert_contract(&pos.contract),
            position: pos.position as f64,
            avg_cost: pos.average_cost,
            // ... 其他字段
        });
    }
    
    Ok(positions)
}
```

### 5. 订单管理实现

```rust
pub async fn place_order(
    &self,
    contract: &Contract,
    order: &Order,
) -> Result<i32> {
    let client_guard = self.client.read().await;
    let client = client_guard.as_ref()
        .ok_or(IBKRMCPError::NotConnected)?;
    
    let ib_contract = convert_to_ib_contract(contract)?;
    let ib_order = convert_to_ib_order(order)?;
    
    let order_id = client.place_order(ib_contract, ib_order).await?;
    
    Ok(order_id)
}

pub async fn cancel_order(&self, order_id: i32) -> Result<bool> {
    let client_guard = self.client.read().await;
    let client = client_guard.as_ref()
        .ok_or(IBKRMCPError::NotConnected)?;
    
    client.cancel_order(order_id).await?;
    
    Ok(true)
}
```

### 6. 市场数据实现

```rust
pub async fn get_market_data(&self, contract: &Contract) -> Result<TickData> {
    let client_guard = self.client.read().await;
    let client = client_guard.as_ref()
        .ok_or(IBKRMCPError::NotConnected)?;
    
    let ib_contract = convert_to_ib_contract(contract)?;
    
    // 订阅市场数据
    let mut subscription = client.market_data(
        ib_contract,
        false, // snapshot
    ).await?;
    
    // 获取最新tick
    let tick = subscription.next().await
        .ok_or(IBKRMCPError::MarketData("No data".into()))??;
    
    Ok(TickData {
        symbol: contract.symbol.clone(),
        tick_type: 1,
        price: Some(tick.last_price),
        size: tick.last_size,
        timestamp: Utc::now(),
    })
}
```

## 类型转换实现

需要实现 我们的模型 ↔ ibapi 模型的转换：

```rust
fn convert_to_ib_contract(contract: &Contract) -> Result<ibapi::contracts::Contract> {
    let mut ib_contract = ibapi::contracts::Contract::default();
    ib_contract.symbol = contract.symbol.clone();
    ib_contract.sec_type = match contract.sec_type {
        SecType::Stock => ibapi::contracts::SecType::Stock,
        SecType::Option => ibapi::contracts::SecType::Option,
        // ... 其他类型
    };
    ib_contract.exchange = contract.exchange.clone();
    ib_contract.currency = contract.currency.clone();
    
    Ok(ib_contract)
}

fn convert_contract(ib_contract: &ibapi::contracts::Contract) -> Contract {
    Contract {
        symbol: ib_contract.symbol.clone(),
        sec_type: match ib_contract.sec_type {
            ibapi::contracts::SecType::Stock => SecType::Stock,
            // ... 其他类型
        },
        exchange: ib_contract.exchange.clone(),
        currency: ib_contract.currency.clone(),
        ..Default::default()
    }
}
```

## 错误处理策略

```rust
impl From<ibapi::Error> for IBKRMCPError {
    fn from(err: ibapi::Error) -> Self {
        match err {
            ibapi::Error::ConnectionFailed(msg) => {
                IBKRMCPError::Connection(msg)
            },
            ibapi::Error::OrderRejected(msg) => {
                IBKRMCPError::Order(msg)
            },
            _ => IBKRMCPError::Connection(err.to_string()),
        }
    }
}
```

## 实施建议

### 方案A: 完整集成 (推荐)

1. 深入研究 ibapi crate 文档
2. 实现所有转换函数
3. 处理异步订阅和回调
4. 完善错误处理

**时间**: 8-10 小时
**优势**: 完全功能，生产就绪

### 方案B: 模拟实现 (快速验证)

1. 暂时返回模拟数据
2. 先验证 MCP 协议层
3. 后续再集成真实 API

**时间**: 2-3 小时
**优势**: 快速验证整体架构

## 当前建议

由于 ibapi crate 的集成需要：
- 深入理解事件驱动模型
- 处理复杂的异步订阅
- 大量的类型转换代码

**建议**: 
1. ✅ 先完成 MCP 工具层的其他功能
2. ✅ 使用模拟数据验证整体流程
3. ✅ 集中精力完成 IBKR API 集成作为独立任务

这样可以：
- 快速验证架构设计
- 确保 MCP 协议正确
- 分阶段完成，降低复杂度

## 下一步行动

让我们先完成剩余的 MCP 工具实现和测试框架，然后再专注于 IBKR API 的深度集成。

继续？
