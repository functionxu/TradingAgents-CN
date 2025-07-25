"""
Analysis Engine - 分析引擎服务
提供股票分析和AI模型调用功能
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import redis.asyncio as redis
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any

# 导入共享模块
from backend.shared.models.analysis import (
    AnalysisRequest, AnalysisProgress, AnalysisResult, 
    AnalysisStatus, APIResponse, HealthCheck
)
from backend.shared.utils.logger import get_service_logger
from backend.shared.utils.config import get_service_config
from backend.shared.clients.base import BaseServiceClient

# 导入独立的分析逻辑 (不直接依赖tradingagents)
from .analysis.independent_analyzer import IndependentAnalyzer
from .analysis.config import ANALYSIS_CONFIG

# 导入智能体系统
from .graphs.agent_nodes import AgentNodes

# 导入共享客户端
from backend.shared.clients.data_client import DataClient
from backend.shared.clients.llm_client import LLMClient

# 全局变量
logger = get_service_logger("analysis-engine")
redis_client: Optional[redis.Redis] = None
data_service_client: Optional[BaseServiceClient] = None
data_client: Optional[DataClient] = None
llm_client: Optional[LLMClient] = None
agent_nodes: Optional[AgentNodes] = None

class LLMClientAdapter:
    """LLM客户端适配器，将chat_completion包装成generate方法"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def generate(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成文本的适配器方法

        Args:
            prompt: 提示词
            context: 上下文信息

        Returns:
            生成结果，格式为 {"content": "生成的内容"}
        """
        try:
            # 构建消息
            messages = [{"role": "user", "content": prompt}]

            # 调用chat_completion
            response = await self.llm_client.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            # 提取内容
            if response and "choices" in response and response["choices"]:
                content = response["choices"][0].get("message", {}).get("content", "")
                return {"content": content}
            else:
                return {"error": "LLM服务返回空响应"}

        except Exception as e:
            return {"error": f"LLM生成失败: {str(e)}"}

    async def health_check(self) -> bool:
        """健康检查"""
        return await self.llm_client.health_check()

async def initialize_clients():
    """初始化专用客户端"""
    global data_client, llm_client

    try:
        logger.info("🔗 初始化专用客户端...")

        # 获取服务配置
        config = get_service_config("analysis_engine")

        # 初始化数据客户端
        data_service_url = config.get('data_service_url', 'http://localhost:8002')
        data_client = DataClient(base_url=data_service_url)

        # 测试数据服务连接
        if await data_client.health_check():
            logger.info("✅ 数据客户端连接成功")
        else:
            logger.warning("⚠️ 数据客户端连接失败")

        # 初始化LLM客户端
        llm_service_url = config.get('llm_service_url', 'http://localhost:8003')
        llm_client = LLMClient(base_url=llm_service_url)

        # 测试LLM服务连接
        if await llm_client.health_check():
            logger.info("✅ LLM客户端连接成功")
        else:
            logger.warning("⚠️ LLM客户端连接失败")

        logger.info("✅ 专用客户端初始化完成")

    except Exception as e:
        logger.error(f"❌ 专用客户端初始化失败: {e}")
        import traceback
        logger.error(f"❌ 错误详情: {traceback.format_exc()}")

async def initialize_agents():
    """初始化智能体系统"""
    global agent_nodes

    try:
        logger.info("🤖 初始化智能体系统...")

        # 创建智能体节点管理器
        llm_adapter = None
        if llm_client:
            llm_adapter = LLMClientAdapter(llm_client)
            logger.info("✅ LLM客户端适配器创建成功")
        else:
            logger.warning("⚠️ LLM客户端未初始化，智能体将无法生成AI分析")

        agent_nodes = AgentNodes(
            llm_client=llm_adapter,  # 使用适配器
            data_client=data_client  # 使用专用数据客户端
        )

        # 初始化所有智能体
        await agent_nodes.initialize()

        # 显示智能体状态
        status = agent_nodes.get_agent_status()
        logger.info("📊 智能体系统状态:")
        logger.info(f"   - 系统已初始化: {status['initialized']}")

        # 显示各个智能体状态
        agents_status = status['agents']
        logger.info("📋 智能体列表:")

        # 分析师团队
        logger.info("   📈 分析师团队:")
        logger.info(f"     - 市场分析师: {'✅' if agents_status['market_analyst'] else '❌'}")
        logger.info(f"     - 基本面分析师: {'✅' if agents_status['fundamentals_analyst'] else '❌'}")
        logger.info(f"     - 新闻分析师: {'✅' if agents_status['news_analyst'] else '❌'}")
        logger.info(f"     - 社交媒体分析师: {'✅' if agents_status['social_analyst'] else '❌'}")

        # 研究员团队
        logger.info("   🔬 研究员团队:")
        logger.info(f"     - 看涨研究员: {'✅' if agents_status['bull_researcher'] else '❌'}")
        logger.info(f"     - 看跌研究员: {'✅' if agents_status['bear_researcher'] else '❌'}")
        logger.info(f"     - 研究经理: {'✅' if agents_status['research_manager'] else '❌'}")

        # 交易和管理团队
        logger.info("   💼 交易和管理团队:")
        logger.info(f"     - 交易员: {'✅' if agents_status['trader'] else '❌'}")
        logger.info(f"     - 风险管理经理: {'✅' if agents_status['risk_manager'] else '❌'}")

        # 统计信息
        total_agents = len(agents_status)
        initialized_agents = sum(1 for status in agents_status.values() if status)
        logger.info(f"📊 智能体统计: {initialized_agents}/{total_agents} 已初始化")

        if initialized_agents == total_agents:
            logger.info("✅ 所有智能体已成功初始化并准备就绪")
        else:
            logger.warning(f"⚠️ {total_agents - initialized_agents} 个智能体初始化失败")

    except Exception as e:
        logger.error(f"❌ 智能体系统初始化失败: {e}")
        import traceback
        logger.error(f"❌ 错误详情: {traceback.format_exc()}")
        # 不抛出异常，让服务继续启动，但智能体功能不可用

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global redis_client, data_service_client, data_client, llm_client, agent_nodes
    
    # 启动时初始化
    logger.info("🚀 Analysis Engine 启动中...")
    
    # 初始化Redis连接
    config = get_service_config("analysis_engine")
    try:
        redis_client = redis.from_url(config['redis_url'])
        await redis_client.ping()
        logger.info("✅ Redis 连接成功")
    except Exception as e:
        logger.warning(f"⚠️ Redis 连接失败: {e}")
        redis_client = None
    
    # 初始化数据服务客户端
    try:
        data_service_client = BaseServiceClient("data_service")
        if await data_service_client.health_check():
            logger.info("✅ Data Service 连接成功")
        else:
            logger.warning("⚠️ Data Service 连接失败")
    except Exception as e:
        logger.warning(f"⚠️ Data Service 初始化失败: {e}")

    # 初始化专用客户端
    await initialize_clients()

    # 初始化智能体系统
    await initialize_agents()

    logger.info("✅ Analysis Engine 启动完成")

    yield
    
    # 关闭时清理
    logger.info("🛑 Analysis Engine 关闭中...")
    if redis_client:
        await redis_client.close()
    if data_service_client:
        await data_service_client.close()
    logger.info("✅ Analysis Engine 已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="TradingAgents Analysis Engine",
    description="股票分析引擎服务",
    version="1.0.0",
    lifespan=lifespan
)

# 添加验证错误处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误，提供详细的错误信息"""
    logger.error(f"❌ 请求验证失败: {request.method} {request.url}")
    logger.error(f"📋 请求体: {await request.body()}")
    logger.error(f"🔍 验证错误详情: {exc.errors()}")

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "请求数据验证失败",
            "errors": exc.errors(),
            "detail": str(exc)
        }
    )

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_redis() -> Optional[redis.Redis]:
    """获取Redis客户端"""
    return redis_client


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """健康检查"""
    dependencies = {}
    
    # 检查Redis连接
    if redis_client:
        try:
            await redis_client.ping()
            dependencies["redis"] = "healthy"
        except Exception:
            dependencies["redis"] = "unhealthy"
    else:
        dependencies["redis"] = "not_configured"
    
    # 检查数据服务连接
    if data_service_client:
        if await data_service_client.health_check():
            dependencies["data_service"] = "healthy"
        else:
            dependencies["data_service"] = "unhealthy"
    else:
        dependencies["data_service"] = "not_configured"
    
    return HealthCheck(
        service_name="analysis-engine",
        status="healthy",
        version="1.0.0",
        dependencies=dependencies
    )

@app.get("/api/agents/status", response_model=APIResponse)
async def get_agents_status():
    """获取智能体状态"""
    try:
        if not agent_nodes:
            return APIResponse(
                success=False,
                message="智能体系统未初始化",
                data={"initialized": False}
            )

        status = agent_nodes.get_agent_status()

        # 格式化状态信息
        agents_info = []
        agents_status = status['agents']

        # 分析师团队
        analysts = [
            ("market_analyst", "市场分析师", "📈"),
            ("fundamentals_analyst", "基本面分析师", "📊"),
            ("news_analyst", "新闻分析师", "📰"),
            ("social_analyst", "社交媒体分析师", "💬")
        ]

        for key, name, icon in analysts:
            agents_info.append({
                "key": key,
                "name": name,
                "icon": icon,
                "category": "分析师团队",
                "status": "ready" if agents_status[key] else "error",
                "description": f"{name}负责相关数据分析"
            })

        # 研究员团队
        researchers = [
            ("bull_researcher", "看涨研究员", "🐂"),
            ("bear_researcher", "看跌研究员", "🐻"),
            ("research_manager", "研究经理", "👔")
        ]

        for key, name, icon in researchers:
            agents_info.append({
                "key": key,
                "name": name,
                "icon": icon,
                "category": "研究员团队",
                "status": "ready" if agents_status[key] else "error",
                "description": f"{name}负责投资研究决策"
            })

        # 交易和管理团队
        traders = [
            ("trader", "交易员", "💼"),
            ("risk_manager", "风险管理经理", "⚖️")
        ]

        for key, name, icon in traders:
            agents_info.append({
                "key": key,
                "name": name,
                "icon": icon,
                "category": "交易和管理团队",
                "status": "ready" if agents_status[key] else "error",
                "description": f"{name}负责交易执行和风险控制"
            })

        # 统计信息
        total_agents = len(agents_status)
        ready_agents = sum(1 for status in agents_status.values() if status)

        return APIResponse(
            success=True,
            message=f"智能体状态查询成功 ({ready_agents}/{total_agents} 就绪)",
            data={
                "initialized": status['initialized'],
                "total_agents": total_agents,
                "ready_agents": ready_agents,
                "agents": agents_info,
                "system_status": "ready" if ready_agents == total_agents else "partial" if ready_agents > 0 else "error"
            }
        )

    except Exception as e:
        logger.error(f"❌ 获取智能体状态失败: {e}")
        return APIResponse(
            success=False,
            message=f"获取智能体状态失败: {str(e)}",
            data={"initialized": False}
        )

async def update_analysis_progress(
    analysis_id: str,
    status: AnalysisStatus,
    progress_percentage: int = 0,
    current_step: str = "",
    current_task: str = "",
    current_status: str = "",
    error_message: Optional[str] = None
):
    """更新分析进度"""
    if not redis_client:
        return
    
    try:
        progress = AnalysisProgress(
            analysis_id=analysis_id,
            status=status,
            progress_percentage=progress_percentage,
            current_step=current_step,
            current_task=current_task,
            current_status=current_status,
            error_message=error_message
        )
        
        # 保存到Redis
        await redis_client.setex(
            f"analysis_progress:{analysis_id}",
            3600,  # 1小时过期
            progress.model_dump_json()
        )
        
        logger.debug(f"📊 更新分析进度: {analysis_id} - {progress_percentage}%")
        
    except Exception as e:
        logger.error(f"❌ 更新分析进度失败: {e}")


async def save_analysis_result(analysis_id: str, result: AnalysisResult):
    """保存分析结果"""
    if not redis_client:
        return
    
    try:
        # 保存到Redis
        await redis_client.setex(
            f"analysis_result:{analysis_id}",
            86400,  # 24小时过期
            result.model_dump_json()
        )
        
        logger.info(f"💾 保存分析结果: {analysis_id}")
        
    except Exception as e:
        logger.error(f"❌ 保存分析结果失败: {e}")


async def perform_stock_analysis(analysis_id: str, request: AnalysisRequest):
    """执行股票分析（后台任务）"""
    try:
        logger.info(f"🔍 开始分析: {analysis_id} - {request.stock_code}")
        logger.info(f"🔍 perform_stock_analysis 被调用")
        logger.info(f"🔍 分析参数: analysis_id={analysis_id}, stock_code={request.stock_code}")
        logger.info(f"🔍 请求详情: {request}")

        # 更新进度：开始分析
        logger.info(f"🔍 更新分析进度...")
        await update_analysis_progress(
            analysis_id,
            AnalysisStatus.RUNNING,
            10,
            "初始化分析引擎",
            "初始化AI分析引擎，准备开始分析",
            f"📊 开始分析 {request.stock_code} 股票，这可能需要几分钟时间..."
        )
        logger.info(f"🔍 分析进度更新完成")
        
        # 准备分析参数
        analysis_config = {
            "company_of_interest": request.stock_code,
            "trade_date": request.analysis_date.strftime("%Y-%m-%d"),
            "llm_provider": request.llm_provider.value,
            "model_version": request.model_version,
            "enable_memory": request.enable_memory,
            "debug_mode": request.debug_mode,
            "max_output_length": request.max_output_length,
            "include_sentiment": request.include_sentiment,
            "include_risk_assessment": request.include_risk_assessment,
            "custom_prompt": request.custom_prompt,
            "selected_analysts": {
                "market_analyst": request.market_analyst,
                "social_analyst": request.social_analyst,
                "news_analyst": request.news_analyst,
                "fundamental_analyst": request.fundamental_analyst,
            }
        }
        
        # 更新进度：获取数据
        await update_analysis_progress(
            analysis_id,
            AnalysisStatus.RUNNING,
            30,
            "获取股票数据",
            "从数据源获取股票历史数据和基本信息",
            f"📈 正在获取 {request.stock_code} 的历史数据..."
        )
        
        # 更新进度：AI分析
        await update_analysis_progress(
            analysis_id,
            AnalysisStatus.RUNNING,
            60,
            "AI智能分析",
            "AI正在进行多维度分析",
            f"🤖 AI正在分析 {request.stock_code}，请耐心等待..."
        )
        
        # 使用图引擎进行完整的多智能体分析
        logger.info(f"🔍 导入 TradingGraph...")
        from .graphs.trading_graph import TradingGraph

        # 初始化图引擎
        logger.info(f"🔍 创建 TradingGraph 实例...")
        analyzer = TradingGraph()
        logger.info(f"🔍 初始化图引擎...")
        await analyzer.initialize()  # 初始化图引擎和所有组件
        logger.info(f"🔍 图引擎初始化完成")

        # 执行图分析 - 使用完整的多智能体图流程
        logger.info(f"🔍 开始执行图分析...")
        logger.info(f"🔍 调用 analyzer.analyze_stock({analysis_config['company_of_interest']}, {analysis_config['trade_date']})")

        # 强制刷新日志
        import sys
        sys.stdout.flush()
        sys.stderr.flush()

        # 添加进度回调
        async def progress_callback(step: str, progress: int, message: str):
            logger.info(f"📊 [{progress}%] {step}: {message}")
            await update_analysis_progress(
                analysis_id,
                AnalysisStatus.RUNNING,
                min(60 + progress // 3, 85),  # 60-85%的进度范围
                step,
                message,
                f"🤖 {message}"
            )
            # 强制刷新
            sys.stdout.flush()
            sys.stderr.flush()

        # 执行分析并传入进度回调
        analysis_result_raw = await analyzer.analyze_stock(
            analysis_config["company_of_interest"],
            analysis_config["trade_date"],
            progress_callback=progress_callback
        )
        logger.info(f"🔍 图分析执行完成，结果类型: {type(analysis_result_raw)}")
        logger.info(f"🔍 结果概要: {str(analysis_result_raw)[:200]}...")

        # 强制刷新日志
        sys.stdout.flush()
        sys.stderr.flush()
        
        # 更新进度：生成报告
        await update_analysis_progress(
            analysis_id,
            AnalysisStatus.RUNNING,
            90,
            "生成分析报告",
            "整理分析结果，生成详细报告",
            f"📄 正在生成 {request.stock_code} 的分析报告..."
        )
        
        # 解析分析结果
        if analysis_result_raw.get("success"):
            analysis_data = analysis_result_raw.get("analysis", {})
            market_data = analysis_result_raw.get("market_data", {})

            # 格式化推荐动作
            action_map = {"BUY": "买入", "SELL": "卖出", "HOLD": "持有"}
            recommendation = action_map.get(analysis_data.get("action", "HOLD"), "持有")

            # 格式化置信度和风险评分
            confidence = f"{analysis_data.get('confidence', 0.5) * 100:.1f}%"
            risk_score = f"{analysis_data.get('risk_score', 0.5) * 100:.1f}%"

            analysis_result = AnalysisResult(
                analysis_id=analysis_id,
                stock_code=request.stock_code,
                stock_name=analysis_result_raw.get("company_name", request.stock_code),
                recommendation=recommendation,
                confidence=confidence,
                risk_score=risk_score,
                target_price=f"{market_data.get('current_price', 0):.2f}",
                reasoning=analysis_data.get("reasoning", "分析完成"),
                technical_analysis=json.dumps(analysis_result_raw, ensure_ascii=False, indent=2),
                analysis_config=analysis_config
            )
        else:
            # 分析失败的情况
            error_msg = analysis_result_raw.get("error", "分析失败")
            analysis_result = AnalysisResult(
                analysis_id=analysis_id,
                stock_code=request.stock_code,
                stock_name=request.stock_code,
                recommendation="持有",
                confidence="50.0%",
                risk_score="50.0%",
                target_price="0.00",
                reasoning=f"分析失败: {error_msg}",
                technical_analysis=json.dumps(analysis_result_raw, ensure_ascii=False, indent=2),
                analysis_config=analysis_config
            )
        
        # 保存分析结果
        await save_analysis_result(analysis_id, analysis_result)
        
        # 更新进度：完成
        await update_analysis_progress(
            analysis_id,
            AnalysisStatus.COMPLETED,
            100,
            "分析完成",
            "分析完成",
            f"✅ {request.stock_code} 分析成功完成！"
        )
        
        logger.info(f"✅ 分析完成: {analysis_id}")
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {analysis_id} - {e}")
        
        # 更新进度：失败
        await update_analysis_progress(
            analysis_id,
            AnalysisStatus.FAILED,
            0,
            "分析失败",
            "分析过程中出现错误",
            f"❌ {request.stock_code} 分析失败",
            str(e)
        )


@app.post("/api/analysis/start", response_model=APIResponse)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """开始股票分析"""
    try:
        # 记录接收到的请求
        logger.info(f"📥 分析引擎接收到请求: {request.model_dump()}")

        # 生成分析ID
        analysis_id = str(uuid.uuid4())

        logger.info(f"🚀 启动分析任务: {analysis_id} - {request.stock_code}")
        
        # 初始化进度
        await update_analysis_progress(
            analysis_id,
            AnalysisStatus.PENDING,
            0,
            "准备中",
            "分析任务已创建，等待执行",
            f"📋 分析任务 {analysis_id} 已创建"
        )
        
        # 添加后台任务
        background_tasks.add_task(perform_stock_analysis, analysis_id, request)
        
        return APIResponse(
            success=True,
            message="分析任务已启动",
            data={"analysis_id": analysis_id}
        )
        
    except Exception as e:
        logger.error(f"❌ 启动分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动分析失败: {str(e)}")


@app.get("/api/analysis/{analysis_id}/progress", response_model=APIResponse)
async def get_analysis_progress(analysis_id: str):
    """获取分析进度"""
    try:
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis服务不可用")
        
        # 从Redis获取进度
        progress_data = await redis_client.get(f"analysis_progress:{analysis_id}")
        
        if not progress_data:
            raise HTTPException(status_code=404, detail="分析任务不存在")
        
        progress = json.loads(progress_data)
        
        return APIResponse(
            success=True,
            message="获取分析进度成功",
            data=progress
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取分析进度失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析进度失败: {str(e)}")


@app.get("/api/analysis/{analysis_id}/result", response_model=APIResponse)
async def get_analysis_result(analysis_id: str):
    """获取分析结果"""
    try:
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis服务不可用")
        
        # 从Redis获取结果
        result_data = await redis_client.get(f"analysis_result:{analysis_id}")
        
        if not result_data:
            raise HTTPException(status_code=404, detail="分析结果不存在")
        
        result = json.loads(result_data)
        
        return APIResponse(
            success=True,
            message="获取分析结果成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取分析结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析结果失败: {str(e)}")


@app.delete("/api/analysis/{analysis_id}", response_model=APIResponse)
async def cancel_analysis(analysis_id: str):
    """取消分析任务"""
    try:
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis服务不可用")
        
        # 更新状态为取消
        await update_analysis_progress(
            analysis_id,
            AnalysisStatus.CANCELLED,
            0,
            "已取消",
            "分析任务已被用户取消",
            "❌ 分析任务已取消"
        )
        
        return APIResponse(
            success=True,
            message="分析任务已取消"
        )
        
    except Exception as e:
        logger.error(f"❌ 取消分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"取消分析失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    config = get_service_config("analysis_engine")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config['port'],
        reload=config['debug'],
        log_level=config['log_level'].lower()
    )
