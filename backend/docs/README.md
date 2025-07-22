# TradingAgents 后端系统 - 完整指南

欢迎使用 TradingAgents 后端微服务系统！这是一个基于 FastAPI + MongoDB + Redis + Celery 的现代化股票分析平台。

## 🚀 快速开始

### ⚡ 一键启动（推荐）

```bash
# Linux/Mac
cd backend
chmod +x scripts/quick-start.sh
./scripts/quick-start.sh

# Windows
cd backend
scripts\quick-start.bat
```

> 💡 **国内用户优化**: 本项目已配置阿里云镜像源，大幅提升下载速度！详见 [国内镜像源配置](docs/CHINA_MIRRORS.md)

### 🐳 Docker Compose 启动

```bash
# 1. 配置环境变量
cp .env.example .env
vim .env  # 填入API密钥

# 2. 启动所有服务
docker-compose up -d

# 3. 验证启动
curl http://localhost:8000/health
```

### 💻 本地开发模式（推荐）

```bash
# 1. 启动基础服务（Docker）
docker-compose -f docker-compose.simple.yml up -d

# 2. 设置环境变量
scripts\setup-env.bat  # Windows
source scripts/setup-env.sh  # Linux/Mac

# 3. 启动应用服务（本地）
cd data-service && python app/main.py
cd analysis-engine && python app/main.py
cd api-gateway && python app/main.py

# 详细说明请查看: LOCAL_DEVELOPMENT.md
```

## 📊 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │ Analysis Engine │
│   (Vue 3)       │◄──►│   (Port 8000)   │◄──►│   (Port 8001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Service  │    │   Task Manager  │    │    MongoDB      │
│   (Port 8002)   │    │   (Port 8003)   │    │   (Port 27017)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Redis       │    │  Celery Worker  │    │     MinIO       │
│   (Port 6379)   │    │  + Celery Beat  │    │ (Port 9000/9001)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🌐 服务访问地址

| 服务 | 地址 | 用途 |
|------|------|------|
| **API Gateway** | http://localhost:8000 | 统一API入口 |
| **API 文档** | http://localhost:8000/docs | 接口文档和测试 |
| **Analysis Engine** | http://localhost:8001 | 股票分析服务 |
| **Data Service** | http://localhost:8002 | 数据获取服务 |
| **Task API** | http://localhost:8003 | 任务管理接口 |
| **Flower 监控** | http://localhost:5555 | 任务执行监控 |
| **MinIO 控制台** | http://localhost:9001 | 对象存储管理 |
| **MongoDB 管理** | http://localhost:8081 | 数据库管理（开发模式） |
| **Redis 管理** | http://localhost:8082 | 缓存管理（开发模式） |

## 📋 核心功能

### 🔍 股票分析
- **多维度分析**: 技术面、基本面、市场情绪、新闻分析
- **AI驱动**: 支持多种LLM模型（DeepSeek、通义千问、GPT等）
- **实时分析**: 异步任务处理，支持进度跟踪
- **历史记录**: 完整的分析历史和结果存储

### 📊 数据管理
- **多数据源**: Tushare、AKShare、BaoStock、FinnHub等
- **智能缓存**: Redis多层缓存策略
- **数据存储**: MongoDB时序集合优化
- **实时更新**: 定时任务自动同步数据

### 🕐 定时任务
- **数据同步**: 每日股票数据、财务数据、新闻数据
- **分析计算**: 技术指标、市场情绪、风险评估
- **系统维护**: 数据清理、缓存刷新、备份归档
- **报告生成**: 每日市场报告、投资组合报告

### 🔧 系统管理
- **健康监控**: 服务状态检查、性能指标
- **日志管理**: 结构化日志、日志归档
- **配置管理**: 环境变量、动态配置
- **错误处理**: 异常捕获、重试机制

## 🧪 测试和验证

### 自动化测试

```bash
# 运行完整系统诊断
python scripts/debug-tools.py

# API接口测试
python scripts/test-api.py

# MongoDB性能测试
python scripts/test-mongodb-performance.py
```

### 手动测试

```bash
# 健康检查
curl http://localhost:8000/health

# 股票信息查询
curl http://localhost:8000/api/stock/info/000858

# 启动分析任务
curl -X POST http://localhost:8000/api/analysis/start \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000858",
    "market_type": "A股",
    "research_depth": 3,
    "market_analyst": true,
    "fundamental_analyst": true
  }'

# 查询任务进度
curl http://localhost:8000/api/analysis/{analysis_id}/progress

# 获取分析结果
curl http://localhost:8000/api/analysis/{analysis_id}/result
```

## 🔧 开发和调试

### 开发模式启动

```bash
# 启动开发模式（支持热重载）
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 启动开发工具
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev-tools up -d
```

### 调试工具

```bash
# 查看服务日志
docker-compose logs -f api-gateway

# 进入容器调试
docker exec -it tradingagents-api-gateway bash

# 数据库操作
docker exec -it tradingagents-mongodb mongosh
docker exec -it tradingagents-redis redis-cli

# 任务监控
open http://localhost:5555  # Flower界面
```

### 性能监控

```bash
# 容器资源使用
docker stats

# 系统性能测试
python scripts/debug-tools.py --action perf

# 数据库性能
python scripts/test-mongodb-performance.py
```

## 📚 文档导航

| 文档 | 描述 |
|------|------|
| **[GETTING_STARTED.md](./GETTING_STARTED.md)** | 详细的启动和配置指南 |
| **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** | 故障排除和问题解决 |
| **[docs/CHINA_MIRRORS.md](./docs/CHINA_MIRRORS.md)** | 国内镜像源配置指南 |
| **[task-scheduler/README.md](./task-scheduler/README.md)** | 定时任务系统文档 |
| **[scripts/](./scripts/)** | 各种工具脚本 |

## 🔑 环境配置

### 必需的API密钥

```bash
# .env 文件配置
DASHSCOPE_API_KEY=your_dashscope_api_key_here    # 阿里百炼（必需）
TUSHARE_TOKEN=your_tushare_token_here            # Tushare数据（必需）
```

### 可选的API密钥

```bash
DEEPSEEK_API_KEY=your_deepseek_api_key_here      # DeepSeek AI
OPENAI_API_KEY=your_openai_api_key_here          # OpenAI GPT
GOOGLE_API_KEY=your_google_api_key_here          # Google Gemini
FINNHUB_API_KEY=your_finnhub_api_key_here        # FinnHub数据
```

## 🚀 生产部署

### Docker Compose 生产模式

```bash
# 使用生产配置
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 配置反向代理（Nginx）
# 配置SSL证书
# 配置监控告警
```

### Kubernetes 部署

```bash
# 准备K8s配置文件
kubectl apply -f k8s/

# 配置Ingress
# 配置持久化存储
# 配置自动扩缩容
```

## 📊 监控和告警

### 内置监控

- **Flower**: Celery任务监控 (http://localhost:5555)
- **健康检查**: 各服务健康状态API
- **性能指标**: API响应时间、资源使用率
- **日志聚合**: 结构化日志输出

### 外部监控（推荐）

- **Prometheus + Grafana**: 指标收集和可视化
- **ELK Stack**: 日志分析和搜索
- **Jaeger**: 分布式链路追踪
- **AlertManager**: 告警通知

## 🔒 安全考虑

### 生产环境安全

1. **API密钥管理**: 使用密钥管理服务
2. **网络安全**: 配置防火墙和VPN
3. **数据加密**: 传输和存储加密
4. **访问控制**: 实现认证和授权
5. **安全审计**: 定期安全扫描

### 数据安全

1. **数据备份**: 定期自动备份
2. **数据恢复**: 备份恢复测试
3. **数据清理**: 敏感数据清理
4. **合规性**: 数据保护法规遵循

## 🤝 贡献指南

### 开发流程

1. **Fork项目** 并创建功能分支
2. **本地开发** 使用开发模式
3. **编写测试** 确保代码质量
4. **提交PR** 详细描述变更
5. **代码审查** 通过后合并

### 代码规范

- **Python**: 遵循PEP 8规范
- **API**: RESTful设计原则
- **文档**: 详细的代码注释
- **测试**: 单元测试和集成测试

## 📞 获取帮助

### 问题排查

1. **查看日志**: `docker-compose logs -f`
2. **运行诊断**: `python scripts/debug-tools.py`
3. **检查配置**: 确认环境变量正确
4. **重启服务**: `docker-compose restart`

### 技术支持

- **文档**: 查看相关文档
- **Issues**: 提交GitHub Issues
- **社区**: 参与社区讨论
- **邮件**: 联系技术支持

---

## 🎉 开始使用

现在您已经了解了 TradingAgents 后端系统的全貌，让我们开始：

1. **🚀 快速启动**: 运行 `./scripts/quick-start.sh`
2. **📖 查看文档**: 访问 http://localhost:8000/docs
3. **🧪 运行测试**: 执行 `python scripts/test-api.py`
4. **🔍 监控系统**: 访问 http://localhost:5555

祝您使用愉快！如有问题，请参考故障排除指南或联系技术支持。
