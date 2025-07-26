# TradingAgents 微服务测试套件

这个测试套件用于测试 TradingAgents 微服务架构的所有组件，包括 API Gateway、Analysis Engine 和 Data Service。

## 📋 测试文件说明

### 1. `quick_api_test.py` - 快速 API 测试
- **用途**: 快速测试所有微服务的基本功能
- **特点**: 轻量级，运行时间短（1-2分钟）
- **测试内容**:
  - 服务健康检查
  - 股票信息查询
  - 基本面数据查询
  - 股票新闻查询
  - 数据源状态
  - 模型配置

### 2. `test_microservices_integration.py` - 集成测试
- **用途**: 完整的微服务集成测试
- **特点**: 功能全面，包含分析工作流测试
- **测试内容**:
  - 所有快速测试项目
  - 完整的股票分析工作流
  - 分析进度监控
  - 详细的测试报告

### 3. `run_tests.py` - 测试运行器
- **用途**: 统一的测试入口
- **支持参数**:
  - `--type quick`: 只运行快速测试
  - `--type integration`: 只运行集成测试
  - `--type all`: 运行所有测试

## 🚀 使用方法

### 前提条件

1. **启动微服务**:
   ```bash
   # 启动基础服务
   cd backend
   docker-compose -f docker-compose.local.yml up -d
   
   # 启动应用服务（需要在虚拟环境中）
   # 终端1: Data Service
   cd data-service
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
   
   # 终端2: Analysis Engine  
   cd analysis-engine
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   
   # 终端3: API Gateway
   cd api-gateway
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **安装测试依赖**:
   ```bash
   pip install -r backend/tests/requirements.txt
   ```

### 运行测试

#### 方法1: 使用测试运行器（推荐）

```bash
# 快速测试（推荐首次使用）
python backend/tests/run_tests.py --type quick

# 集成测试（包含分析工作流，耗时较长）
python backend/tests/run_tests.py --type integration

# 运行所有测试
python backend/tests/run_tests.py --type all
```

#### 方法2: 直接运行测试文件

```bash
# 快速测试
python backend/tests/quick_api_test.py

# 集成测试
python backend/tests/test_microservices_integration.py
```

## 📊 测试报告

测试完成后会生成 JSON 格式的测试报告：

- **快速测试报告**: `backend/tests/quick_test_report_YYYYMMDD_HHMMSS.json`
- **集成测试报告**: `backend/tests/test_report_YYYYMMDD_HHMMSS.json`

报告包含：
- 测试总结（总数、通过数、失败数、成功率）
- 详细的测试结果
- 响应时间统计
- 时间戳信息

## 🔧 测试配置

### 服务端点配置

默认的服务端点：
- **API Gateway**: http://localhost:8000
- **Analysis Engine**: http://localhost:8001
- **Data Service**: http://localhost:8002

如需修改，请编辑测试文件中的 `base_urls` 配置。

### 测试数据

默认测试使用的股票代码：
- **A股**: 000858 (五粮液)
- **美股**: AAPL (苹果)

可以在测试文件中修改这些默认值。

## 🐛 故障排除

### 常见问题

1. **连接失败**:
   - 确保所有微服务都已启动
   - 检查端口是否被占用
   - 确认防火墙设置

2. **测试超时**:
   - 检查网络连接
   - 确认数据源 API 密钥配置正确
   - 增加超时时间设置

3. **分析工作流失败**:
   - 检查 LLM 配置（DeepSeek API 密钥）
   - 确认数据源连接正常
   - 查看服务日志获取详细错误信息

### 调试建议

1. **查看服务日志**:
   ```bash
   # 查看 Docker 服务日志
   docker-compose -f docker-compose.local.yml logs
   
   # 查看应用服务日志（在各自的终端中）
   ```

2. **手动测试 API**:
   ```bash
   # 健康检查
   curl http://localhost:8000/health
   curl http://localhost:8001/health  
   curl http://localhost:8002/health
   
   # 股票信息
   curl http://localhost:8000/api/stock/info/000858
   ```

3. **检查服务状态**:
   ```bash
   # 检查端口占用
   netstat -ano | findstr :8000
   netstat -ano | findstr :8001
   netstat -ano | findstr :8002
   ```

## 📝 扩展测试

如需添加新的测试用例：

1. 在相应的测试类中添加新的测试方法
2. 遵循现有的命名约定：`test_功能名称`
3. 使用 `log_test_result` 方法记录测试结果
4. 更新此 README 文档

## 🆕 Data Service 专项测试套件

### 📋 新增测试文件

1. **`test_data_service.py`** - Data Service全面功能测试
   - ✅ 健康检查、股票信息、历史数据、新闻获取
   - ✅ 缓存功能、错误处理、分析ID追踪测试

2. **`test_data_service_performance.py`** - Data Service性能测试
   - ⚡ 并发测试、负载测试、压力测试
   - 📊 响应时间统计、QPS测量

3. **`run_data_service_tests.py`** - Data Service统一测试运行器
   - 🔍 服务可用性检查、集成测试、边界情况测试
   - 📄 自动生成JSON测试报告

4. **`quick_test_data_service.py`** - Data Service快速测试
   - 🚀 5分钟内完成核心功能验证

5. **`debug_data_service.py`** - Data Service调试测试
   - 🔍 详细的请求响应调试信息

6. **`test_post_request.py`** - POST请求专项测试
   - 🎯 专门测试POST /api/stock/data接口

7. **`test_analysis_engine_concurrency.py`** - Analysis Engine并发测试
   - ⚡ 测试多股票同时分析的并发性能
   - 📊 并发加速比和性能评估
   - 🔍 并发问题诊断和错误分析

### 🚀 Data Service测试快速开始

```bash
# 快速验证Data Service功能
cd backend/tests
python quick_test_data_service.py

# 运行完整测试套件
python run_data_service_tests.py
```

### ⚡ Analysis Engine并发测试

```bash
# 测试Analysis Engine并发性能
cd backend/tests
python test_analysis_engine_concurrency.py
```

详细使用说明请参考：
- [Data Service测试文档](README_data_service_tests.md)
- [并发测试指南](README_concurrency_testing.md)

## 🎯 最佳实践

1. **定期运行测试**: 在代码变更后运行快速测试
2. **CI/CD 集成**: 将测试集成到持续集成流程中
3. **监控测试结果**: 关注测试成功率和响应时间趋势
4. **及时修复失败**: 测试失败时及时调查和修复问题
5. **使用专项测试**: 针对特定服务使用对应的专项测试套件
