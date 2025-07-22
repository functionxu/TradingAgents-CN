# TradingAgents 后端微服务测试指南

## 📋 概述

本目录包含TradingAgents后端微服务系统的完整测试工具和文档，用于验证系统的功能性、稳定性和性能。

## 📁 文件结构

```
backend/
├── docs/test/
│   ├── README.md                           # 本文件
│   ├── microservices-test-plan.md          # 详细测试计划
│   └── test_report_YYYYMMDD_HHMMSS.json   # 测试报告（自动生成）
└── test/
    ├── test_microservices.py              # Python完整测试脚本
    ├── test_microservices.ps1             # PowerShell快速测试脚本
    └── run_tests.bat                       # Windows测试启动器
```

## 🚀 快速开始

### 方法1: 使用启动器（推荐）

```bash
# Windows - 进入backend/test目录
cd backend/test
run_tests.bat

# 然后选择测试类型:
# 1. Python完整测试 (推荐)
# 2. PowerShell快速测试  
# 3. 仅健康检查
# 4. 仅数据服务测试
# 5. 仅LLM服务测试
# 6. 仅网关测试
```

### 方法2: 直接运行Python脚本

```bash
# 进入backend/test目录
cd backend/test

# 完整测试
python test_microservices.py
```

### 方法3: 直接运行PowerShell脚本

```powershell
# 进入backend/test目录
cd backend/test

# 完整测试
powershell -ExecutionPolicy Bypass -File test_microservices.ps1

# 仅健康检查
powershell -ExecutionPolicy Bypass -File test_microservices.ps1 -TestType health

# 仅数据服务测试
powershell -ExecutionPolicy Bypass -File test_microservices.ps1 -TestType data
```

## 🧪 测试类型

### 1. 健康检查测试 (health)
- 验证所有微服务的基本可用性
- 检查服务响应时间
- 验证数据库和Redis连接

### 2. 数据服务测试 (data)
- 股票信息查询功能
- 缓存机制验证
- 强制刷新功能
- 数据准确性验证

### 3. LLM服务测试 (llm)
- 模型可用性检查
- 聊天完成接口测试
- 使用统计功能

### 4. 网关测试 (gateway)
- API路由功能
- 参数传递验证
- 错误处理测试

### 5. 分析引擎测试 (analysis)
- 分析任务启动
- 进度查询
- 结果获取

### 6. 集成测试 (integration)
- 端到端工作流测试
- 多服务协作验证
- 数据一致性检查

## 📊 测试报告

测试完成后，会在 `backend/docs/test/` 目录下生成JSON格式的测试报告：

```json
{
  "test_summary": {
    "total_tests": 25,
    "passed_tests": 23,
    "failed_tests": 2,
    "pass_rate": "92.0%",
    "test_time": "2025-07-22T23:45:30"
  },
  "test_results": [
    {
      "test_name": "Health-data_service",
      "passed": true,
      "message": "服务正常 (156ms)",
      "details": {...},
      "timestamp": "2025-07-22T23:45:30"
    }
  ]
}
```

## 🔧 环境要求

### 前置条件
1. **Python 3.10+** 环境
2. **所有微服务正常运行**:
   - API Gateway (8000)
   - Analysis Engine (8001)
   - Data Service (8002)
   - LLM Service (8004)
   - Agent Service (8008)

3. **基础设施服务**:
   - MongoDB (27017)
   - Redis (6379)

### 环境变量
确保以下环境变量已配置：
```bash
DEEPSEEK_API_KEY=your_deepseek_key
DASHSCOPE_API_KEY=your_dashscope_key
TUSHARE_TOKEN=your_tushare_token
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379
```

## 🎯 测试用例说明

### TC001: 系统健康检查
- **目标**: 验证所有服务正常运行
- **验证点**: HTTP 200响应、响应时间 < 2秒
- **测试数据**: 无

### TC002: 股票信息查询
- **目标**: 验证股票数据获取功能
- **验证点**: 数据完整性、准确性、响应时间
- **测试数据**: 000001(平安银行), 600519(贵州茅台), 000002(万科A)

### TC003: 缓存机制验证
- **目标**: 验证Redis缓存功能
- **验证点**: 缓存命中、响应时间优化、数据一致性
- **测试数据**: 同TC002

### TC004: LLM服务功能
- **目标**: 验证AI模型服务
- **验证点**: 模型可用性、聊天响应、使用统计
- **测试数据**: 标准测试提示词

### TC005: API网关路由
- **目标**: 验证请求路由和参数传递
- **验证点**: 路由正确性、参数传递、错误处理
- **测试数据**: 股票查询请求

## 🚨 故障排除

### 常见问题

1. **连接失败**
   ```
   ❌ data_service 连接失败: Connection refused
   ```
   **解决**: 检查对应服务是否启动，端口是否正确

2. **API密钥错误**
   ```
   ❌ LLM聊天测试失败: Unauthorized
   ```
   **解决**: 检查环境变量中的API密钥配置

3. **数据库连接失败**
   ```
   ❌ MongoDB 连接失败
   ```
   **解决**: 确保MongoDB服务运行在localhost:27017

4. **缓存测试失败**
   ```
   ❌ 缓存机制异常
   ```
   **解决**: 检查Redis服务状态，清除缓存后重试

### 调试技巧

1. **查看详细日志**:
   ```bash
   # 启用详细日志
   set LOG_LEVEL=DEBUG
   python test_microservices.py
   ```

2. **单独测试服务**:
   ```bash
   curl http://localhost:8002/health
   ```

3. **检查服务状态**:
   ```bash
   # 检查端口占用
   netstat -an | findstr :8002
   ```

## 📈 性能基准

### 响应时间基准
- **健康检查**: < 100ms
- **股票信息查询**: < 2000ms
- **缓存命中**: < 200ms
- **LLM聊天**: < 10000ms

### 成功率基准
- **数据准确性**: > 95%
- **缓存命中率**: > 80%
- **服务可用性**: > 99%

## 🔄 持续集成

### 自动化测试建议
1. **每次代码提交**: 运行健康检查测试
2. **每日构建**: 运行完整测试套件
3. **发布前**: 运行性能和集成测试

### 监控集成
- 将测试结果集成到监控系统
- 设置测试失败告警
- 跟踪性能趋势

## 📝 贡献指南

### 添加新测试用例
1. 在 `test_microservices.py` 中添加测试函数
2. 更新 `microservices-test-plan.md` 文档
3. 在PowerShell脚本中添加对应功能

### 测试用例命名规范
- 格式: `test_<功能>_<场景>`
- 示例: `test_stock_info_valid_symbol`

### 结果记录规范
```python
self.record_result(
    test_name="TestName-Identifier",
    passed=True/False,
    message="简短描述",
    details={"key": "value"}
)
```

## 📞 支持

如有问题或建议，请：
1. 查看测试报告中的详细错误信息
2. 检查服务日志文件
3. 参考故障排除部分
4. 提交Issue到项目仓库
