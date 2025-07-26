# Data Service 测试套件

## 📋 概述

这是 Data Service 的完整测试套件，包含功能测试、性能测试、集成测试和边界情况测试。

## 🧪 测试文件说明

### 1. `test_data_service.py` - 功能测试
**全面的功能测试，覆盖所有API端点**

- ✅ 健康检查 (`/health`)
- ✅ 股票信息获取 (`/api/stock/info/{symbol}`)
- ✅ 股票历史数据 (`/api/stock/data`)
- ✅ 股票搜索 (`/api/stock/search`)
- ✅ 市场数据 (`/api/market/data`)
- ✅ 缓存功能测试
- ✅ 错误处理测试
- ✅ 分析ID追踪测试

### 2. `test_data_service_performance.py` - 性能测试
**测试服务的性能和并发能力**

- ⚡ 并发测试 (多个同时请求)
- 🔥 负载测试 (持续时间内的请求)
- 💪 压力测试 (逐步增加并发数)
- 📊 响应时间统计
- 📈 QPS (每秒请求数) 测量

### 3. `run_data_service_tests.py` - 测试运行器
**统一运行所有测试并生成报告**

- 🔍 服务可用性检查
- 🧪 功能测试执行
- ⚡ 性能测试执行
- 🔗 集成测试执行
- 🎯 边界情况测试
- 📄 测试报告生成

### 4. `quick_test_data_service.py` - 快速测试
**快速验证服务基本功能**

- 🚀 5分钟内完成
- 🎯 核心功能验证
- 📊 简单的成功率统计

## 🚀 使用方法

### 前提条件

1. **启动 Data Service**
   ```bash
   cd backend/data-service
   python -m app.main
   ```

2. **安装测试依赖**
   ```bash
   pip install httpx pytest asyncio
   ```

### 运行测试

#### 1. 快速测试 (推荐开始)
```bash
cd backend/tests
python quick_test_data_service.py
```

#### 2. 完整功能测试
```bash
cd backend/tests
python test_data_service.py
```

#### 3. 性能测试
```bash
cd backend/tests
python test_data_service_performance.py
```

#### 4. 全面测试 (包含报告)
```bash
cd backend/tests
python run_data_service_tests.py
```

## 📊 测试结果解读

### 功能测试结果
```
✅ PASS 健康检查: 服务健康，版本: 1.0.0 (0.05s)
✅ PASS 股票信息获取 (000001): 获取成功: 平安银行 - 银行 (2.15s)
✅ PASS 股票历史数据 (000001, 7天): 获取成功: 7个数据点 (3.42s)
❌ FAIL 股票搜索 (平安): 请求超时 (30.00s)
```

### 性能测试结果
```
📊 并发测试 - /api/stock/info/000001
   ✅ 成功率: 100.0% (10/10)
   ⏱️ 平均响应时间: 1.234s
   📊 QPS: 8.1
```

### 测试报告
运行完整测试后会生成 JSON 格式的详细报告：
```json
{
  "test_run_info": {
    "start_time": "2025-07-25T22:00:00",
    "end_time": "2025-07-25T22:15:00",
    "duration": 900.0
  },
  "test_results": {
    "功能测试": true,
    "性能测试": true,
    "集成测试": false
  },
  "summary": {
    "total_test_suites": 4,
    "passed_suites": 3,
    "failed_suites": 1
  }
}
```

## 🎯 测试覆盖范围

### API 端点覆盖
- [x] `GET /health` - 健康检查
- [x] `GET /api/stock/info/{symbol}` - 股票信息
- [x] `POST /api/stock/data` - 股票历史数据
- [x] `GET /api/stock/search` - 股票搜索
- [x] `GET /api/market/data` - 市场数据

### 功能特性覆盖
- [x] 分析ID追踪 (`X-Analysis-ID` 头部)
- [x] Redis 缓存功能
- [x] MongoDB 数据存储
- [x] 错误处理和状态码
- [x] 超时控制
- [x] 数据源降级

### 测试场景覆盖
- [x] 正常情况测试
- [x] 异常情况测试
- [x] 边界值测试
- [x] 并发测试
- [x] 负载测试
- [x] 压力测试

## 🔧 配置选项

### 测试配置
```python
# 在测试文件中修改这些常量
BASE_URL = "http://localhost:8002"  # Data Service 地址
TEST_TIMEOUT = 30                   # 请求超时时间
CONCURRENT_REQUESTS = 10            # 并发请求数
PERFORMANCE_TEST_DURATION = 30      # 性能测试持续时间
```

### 环境变量
```bash
# 可选：设置测试环境变量
export DATA_SERVICE_URL="http://localhost:8002"
export TEST_TIMEOUT="30"
export ENABLE_PERFORMANCE_TESTS="true"
```

## 🐛 故障排除

### 常见问题

1. **连接失败**
   ```
   ❌ 连接失败: Connection refused
   ```
   **解决**: 确保 Data Service 已启动并运行在正确端口

2. **请求超时**
   ```
   ❌ 请求超时 (30.00s)
   ```
   **解决**: 检查网络连接，增加超时时间，或检查数据源配置

3. **API 返回失败**
   ```
   ❌ API返回失败: 未找到股票数据
   ```
   **解决**: 检查股票代码是否正确，数据源是否可用

4. **缓存测试失败**
   ```
   ❌ 缓存可能未生效
   ```
   **解决**: 检查 Redis 连接，确保缓存配置正确

### 调试技巧

1. **查看详细日志**
   ```bash
   # 启动 Data Service 时查看日志
   cd backend/data-service
   python -m app.main
   ```

2. **单独测试特定功能**
   ```python
   # 在 Python 中单独测试
   import asyncio
   from test_data_service import DataServiceTester
   
   async def debug_test():
       async with DataServiceTester() as tester:
           await tester.test_stock_info("000001")
   
   asyncio.run(debug_test())
   ```

3. **检查服务状态**
   ```bash
   curl http://localhost:8002/health
   ```

## 📈 性能基准

### 预期性能指标
- **健康检查**: < 100ms, QPS > 100
- **股票信息**: < 2s, QPS > 10
- **股票数据**: < 5s, QPS > 5
- **搜索功能**: < 3s, QPS > 8

### 并发能力
- **轻负载**: 10 并发, 成功率 > 95%
- **中负载**: 20 并发, 成功率 > 90%
- **重负载**: 50 并发, 成功率 > 80%

## 🔄 持续集成

### GitHub Actions 集成
```yaml
# .github/workflows/data-service-tests.yml
name: Data Service Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Start Data Service
        run: cd backend/data-service && python -m app.main &
      - name: Run tests
        run: cd tests && python run_data_service_tests.py
```

## 📞 支持

如果测试过程中遇到问题：

1. 检查 Data Service 日志
2. 确认所有依赖服务 (Redis, MongoDB) 正常运行
3. 验证网络连接和防火墙设置
4. 查看测试报告中的详细错误信息

---

**注意**: 这些测试需要真实的网络连接来访问数据源 (Tushare, AKShare 等)。在网络受限的环境中，某些测试可能会失败。
