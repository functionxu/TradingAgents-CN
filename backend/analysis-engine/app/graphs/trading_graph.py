#!/usr/bin/env python3
"""
Backend交易图引擎
基于TradingAgents的图结构，使用微服务架构实现
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage

from .graph_state import GraphState
from .conditional_logic import ConditionalLogic
from .agent_nodes import AgentNodes

logger = logging.getLogger(__name__)

class TradingGraph:
    """Backend交易图引擎"""
    
    def __init__(self, llm_client=None, data_client=None):
        self.graph: Optional[StateGraph] = None
        self.compiled_graph = None
        self.agent_nodes: Optional[AgentNodes] = None
        self.conditional_logic: Optional[ConditionalLogic] = None

        # 客户端
        self.llm_client = llm_client
        self.data_client = data_client

        # 默认配置参数
        self.default_config = {
            "max_debate_rounds": 3,
            "max_risk_rounds": 2,
            "selected_analysts": ["market", "fundamentals", "news", "social"],
            "llm_provider": "dashscope",
            "llm_model": "qwen-plus-latest",
            "research_depth": 3
        }

        # 实际使用的配置（可以被外部覆盖）
        self.config = self.default_config.copy()

    def update_config(self, request_config: Dict[str, Any]):
        """根据请求更新配置"""
        if not request_config:
            return

        # 更新分析师选择
        if "analysts" in request_config:
            self.config["selected_analysts"] = request_config["analysts"]
            logger.info(f"🔧 更新分析师选择: {request_config['analysts']}")

        # 更新研究深度
        if "research_depth" in request_config:
            depth = request_config["research_depth"]
            self.config["research_depth"] = depth

            # 根据研究深度调整其他参数
            if depth == 1:  # 快速分析
                self.config["max_debate_rounds"] = 1
                self.config["max_risk_rounds"] = 1
            elif depth == 2:  # 基础分析
                self.config["max_debate_rounds"] = 1
                self.config["max_risk_rounds"] = 1
            elif depth == 3:  # 标准分析
                self.config["max_debate_rounds"] = 2
                self.config["max_risk_rounds"] = 2
            elif depth == 4:  # 深度分析
                self.config["max_debate_rounds"] = 3
                self.config["max_risk_rounds"] = 2
            else:  # 全面分析
                self.config["max_debate_rounds"] = 3
                self.config["max_risk_rounds"] = 3

            logger.info(f"🔧 更新研究深度: {depth} (辩论轮数: {self.config['max_debate_rounds']}, 风险轮数: {self.config['max_risk_rounds']})")

        # 更新LLM配置
        if "llm_provider" in request_config:
            self.config["llm_provider"] = request_config["llm_provider"]
            logger.info(f"🔧 更新LLM提供商: {request_config['llm_provider']}")

        if "llm_model" in request_config:
            self.config["llm_model"] = request_config["llm_model"]
            logger.info(f"🔧 更新LLM模型: {request_config['llm_model']}")

        # 更新市场类型
        if "market_type" in request_config:
            self.config["market_type"] = request_config["market_type"]
            logger.info(f"🔧 更新市场类型: {request_config['market_type']}")

        # 如果分析师配置发生变化，需要标记图需要重新构建
        if "analysts" in request_config:
            self.graph = None  # 重置图，强制重新构建
            self.compiled_graph = None
            logger.info("🔧 分析师配置变化，将重新构建图")

    async def initialize(self):
        """初始化图引擎"""
        try:
            logger.info("🔧 初始化Backend交易图引擎...")
            

            
            # 初始化条件逻辑
            self.conditional_logic = ConditionalLogic(
                max_debate_rounds=self.config["max_debate_rounds"],
                max_risk_rounds=self.config["max_risk_rounds"]
            )
            
            # 初始化Agent节点 - 使用传入的客户端
            logger.info("🔧 创建智能体节点管理器...")
            logger.info(f"🔧 LLM客户端: {self.llm_client is not None}")
            logger.info(f"🔧 数据客户端: {self.data_client is not None}")

            self.agent_nodes = AgentNodes(
                llm_client=self.llm_client,
                data_client=self.data_client
            )
            await self.agent_nodes.initialize()
            
            # 构建图
            self.graph = self._build_graph()
            self.compiled_graph = self.graph.compile()
            
            logger.info("✅ Backend交易图引擎初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 图引擎初始化失败: {e}")
            raise
    

    
    def _build_graph(self) -> StateGraph:
        """构建交易决策图"""
        logger.info("🏗️ 构建交易决策图...")

        # 创建状态图
        workflow = StateGraph(GraphState)

        # 添加一个简单的测试节点来验证图执行
        workflow.add_node("test_start", self._test_start_node)

        # 添加分析师节点
        logger.info("🔧 添加分析师节点...")
        self._add_analyst_nodes(workflow)

        # 添加研究员节点
        logger.info("🔧 添加研究员节点...")
        self._add_researcher_nodes(workflow)

        # 添加风险分析节点
        logger.info("🔧 添加风险分析节点...")
        self._add_risk_nodes(workflow)



        # 添加边和条件逻辑
        logger.info("🔧 添加边和条件逻辑...")
        self._add_edges(workflow)

        # 验证图结构
        self._validate_graph_structure(workflow)

        logger.info("✅ 交易决策图构建完成")
        return workflow

    async def _test_start_node(self, state: GraphState) -> GraphState:
        """测试起始节点 - 验证图执行"""
        logger.info(f"🧪 测试节点执行: {state['symbol']}")
        logger.info(f"🧪 当前状态: {state.get('current_step', 'unknown')}")

        # 更新状态
        state["current_step"] = "test_node_executed"
        state["completed_steps"] = state.get("completed_steps", []) + ["test_start"]

        logger.info(f"✅ 测试节点完成: {state['symbol']}")
        return state

    def _validate_graph_structure(self, workflow: StateGraph):
        """验证图结构"""
        try:
            logger.info("🔍 验证图结构...")

            # 获取所有节点
            nodes = list(workflow.nodes.keys()) if hasattr(workflow, 'nodes') else []
            logger.info(f"🔍 图中的节点: {nodes}")

            # 获取所有边
            edges = []
            if hasattr(workflow, 'edges'):
                try:
                    if hasattr(workflow.edges, 'items'):
                        # 如果是字典类型
                        for source, targets in workflow.edges.items():
                            if isinstance(targets, list):
                                for target in targets:
                                    edges.append(f"{source} -> {target}")
                            else:
                                edges.append(f"{source} -> {targets}")
                    else:
                        # 如果是其他类型（如set）
                        edges = [str(edge) for edge in workflow.edges]
                except Exception as e:
                    logger.warning(f"⚠️ 无法解析边信息: {e}")
                    edges = ["无法解析边信息"]

            logger.info(f"🔍 图中的边: {edges}")

            # 检查起始节点
            start_edges = [edge for edge in edges if edge.startswith("__start__")]
            logger.info(f"🔍 起始边: {start_edges}")

            # 检查结束节点
            end_edges = [edge for edge in edges if edge.endswith("__end__")]
            logger.info(f"🔍 结束边: {end_edges}")

        except Exception as e:
            logger.error(f"❌ 图结构验证失败: {e}")

    def _add_analyst_nodes(self, workflow: StateGraph):
        """添加分析师节点"""
        selected_analysts = self.config["selected_analysts"]
        logger.info(f"🔧 选择的分析师: {selected_analysts}")

        for analyst_type in selected_analysts:
            node_name = f"{analyst_type}_analyst"
            node_func = self.agent_nodes.get_analyst_node(analyst_type)
            logger.info(f"🔧 添加分析师节点: {node_name}, 函数: {node_func}")

            # 添加分析师节点
            workflow.add_node(node_name, node_func)
            logger.info(f"✅ 分析师节点已添加: {node_name}")

    
    def _add_researcher_nodes(self, workflow: StateGraph):
        """添加研究员节点"""
        workflow.add_node("bull_researcher", self.agent_nodes.bull_researcher_node)
        workflow.add_node("bear_researcher", self.agent_nodes.bear_researcher_node)
        workflow.add_node("research_manager", self.agent_nodes.research_manager_node)
    
    def _add_risk_nodes(self, workflow: StateGraph):
        """添加风险分析节点"""
        workflow.add_node("risky_analyst", self.agent_nodes.risky_analyst_node)
        workflow.add_node("safe_analyst", self.agent_nodes.safe_analyst_node)
        workflow.add_node("neutral_analyst", self.agent_nodes.neutral_analyst_node)
        workflow.add_node("risk_manager", self.agent_nodes.risk_manager_node)
        workflow.add_node("trader", self.agent_nodes.trader_node)
    

    
    def _add_edges(self, workflow: StateGraph):
        """添加边和条件逻辑"""
        selected_analysts = self.config["selected_analysts"]
        logger.info(f"🔧 配置边连接，选择的分析师: {selected_analysts}")

        # 设置起始点 - 先到测试节点
        logger.info(f"🔧 设置起始点: START -> test_start")
        workflow.add_edge(START, "test_start")

        # 测试节点到第一个分析师
        if selected_analysts:
            first_analyst = f"{selected_analysts[0]}_analyst"
            logger.info(f"🔧 测试节点连接: test_start -> {first_analyst}")
            workflow.add_edge("test_start", first_analyst)
        else:
            logger.error("❌ 没有选择的分析师，无法设置起始点")
        
        # 添加分析师之间的直接连接（移除工具节点）
        for i, analyst_type in enumerate(selected_analysts):
            analyst_node = f"{analyst_type}_analyst"

            # 直接连接到下一个分析师或研究员
            if i < len(selected_analysts) - 1:
                next_analyst = f"{selected_analysts[i+1]}_analyst"
                workflow.add_edge(analyst_node, next_analyst)
            else:
                # 最后一个分析师连接到多头研究员
                workflow.add_edge(analyst_node, "bull_researcher")
        
        # 添加辩论的条件边
        workflow.add_conditional_edges(
            "bull_researcher",
            self.conditional_logic.should_continue_debate,
            {
                "bull_researcher": "bull_researcher",
                "bear_researcher": "bear_researcher",
                "research_manager": "research_manager"
            }
        )
        
        workflow.add_conditional_edges(
            "bear_researcher",
            self.conditional_logic.should_continue_debate,
            {
                "bull_researcher": "bull_researcher",
                "bear_researcher": "bear_researcher",
                "research_manager": "research_manager"
            }
        )
        
        # 研究经理 -> 交易员
        workflow.add_edge("research_manager", "trader")
        
        # 交易员 -> 风险分析
        workflow.add_edge("trader", "risky_analyst")
        
        # 添加风险分析的条件边
        workflow.add_conditional_edges(
            "risky_analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "risky_analyst": "risky_analyst",
                "safe_analyst": "safe_analyst",
                "neutral_analyst": "neutral_analyst",
                "risk_manager": "risk_manager"
            }
        )
        
        workflow.add_conditional_edges(
            "safe_analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "risky_analyst": "risky_analyst",
                "safe_analyst": "safe_analyst",
                "neutral_analyst": "neutral_analyst",
                "risk_manager": "risk_manager"
            }
        )
        
        workflow.add_conditional_edges(
            "neutral_analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "risky_analyst": "risky_analyst",
                "safe_analyst": "safe_analyst",
                "neutral_analyst": "neutral_analyst",
                "risk_manager": "risk_manager"
            }
        )
        
        # 风险经理 -> 结束
        workflow.add_edge("risk_manager", END)
    
    async def analyze_stock(self, symbol: str, analysis_date: str = None, progress_callback=None) -> Dict[str, Any]:
        """分析股票 - 主要入口点"""
        logger.info(f"🔍 TradingGraph.analyze_stock 被调用")
        logger.info(f"🔍 参数: symbol={symbol}, analysis_date={analysis_date}")

        # 强制刷新日志
        import sys
        sys.stdout.flush()
        sys.stderr.flush()

        if not self.compiled_graph:
            logger.error("❌ 图引擎未初始化")
            raise RuntimeError("图引擎未初始化")

        if analysis_date is None:
            analysis_date = datetime.now().strftime("%Y-%m-%d")
            logger.info(f"🔍 使用默认分析日期: {analysis_date}")

        logger.info(f"📊 开始图分析: {symbol}")

        if progress_callback:
            await progress_callback("初始化图分析", 5, f"开始分析 {symbol}")

        # 创建初始状态
        logger.info(f"🔍 创建初始状态...")
        initial_state = self._create_initial_state(symbol, analysis_date)
        logger.info(f"🔍 初始状态创建完成")

        if progress_callback:
            await progress_callback("创建分析状态", 10, "初始化分析状态完成")

        try:
            # 执行图，设置递归限制
            logger.info(f"🔍 开始执行图分析...")
            logger.info(f"🔍 调用 compiled_graph.ainvoke(initial_state)")

            # 强制刷新日志
            sys.stdout.flush()
            sys.stderr.flush()

            if progress_callback:
                await progress_callback("启动多智能体分析", 15, "启动分析师团队协作")

            # 按照原始 TradingAgents 的方式设置递归限制
            config = {"recursion_limit": 100}

            # 执行图分析
            logger.info("🚀 开始执行图分析...")

            # 启动后台进度监控
            monitor_task = None
            if progress_callback:
                monitor_task = asyncio.create_task(
                    self._background_progress_monitor(progress_callback)
                )

            try:
                # 执行原始图分析
                logger.info(f"🔍 开始执行 compiled_graph.ainvoke...")
                logger.info(f"🔍 初始状态: symbol={initial_state['symbol']}, current_step={initial_state['current_step']}")
                logger.info(f"🔍 图是否已编译: {self.compiled_graph is not None}")

                # 使用流式执行来跟踪每个步骤
                logger.info("🔍 开始流式执行图...")
                step_count = 0

                async for step in self.compiled_graph.astream(initial_state, config=config):
                    step_count += 1
                    logger.info(f"🔍 执行步骤 {step_count}: {step}")

                    # 检查步骤内容
                    if isinstance(step, dict):
                        for node_name, node_result in step.items():
                            logger.info(f"🔍 节点 {node_name} 执行结果: {type(node_result)}")
                            if isinstance(node_result, dict) and 'current_step' in node_result:
                                logger.info(f"🔍 当前步骤更新为: {node_result['current_step']}")

                logger.info(f"🔍 流式执行完成，总步骤数: {step_count}")

                # 获取最终状态
                final_state = await self.compiled_graph.ainvoke(initial_state, config=config)

                logger.info(f"🔍 图执行完成，最终状态: symbol={final_state.get('symbol')}, current_step={final_state.get('current_step')}")
                logger.info(f"🔍 完成的步骤: {final_state.get('completed_steps', [])}")
                logger.info(f"🔍 错误列表: {final_state.get('errors', [])}")

                # 取消监控任务
                if monitor_task:
                    monitor_task.cancel()

            except Exception as e:
                logger.error(f"❌ 图执行异常: {e}")
                logger.error(f"❌ 异常类型: {type(e).__name__}")
                import traceback
                logger.error(f"❌ 异常堆栈: {traceback.format_exc()}")

                # 取消监控任务
                if monitor_task:
                    monitor_task.cancel()
                raise

            logger.info(f"🔍 图执行完成")

            if progress_callback:
                await progress_callback("生成最终报告", 90, "整理分析结果")

            # 处理结果
            logger.info(f"🔍 处理最终状态...")
            result = self._process_final_state(final_state)
            logger.info(f"🔍 结果处理完成")

            if progress_callback:
                await progress_callback("分析完成", 100, f"分析完成: {result.get('action', 'UNKNOWN')}")

            logger.info(f"✅ 图分析完成: {symbol}")

            # 强制刷新日志
            sys.stdout.flush()
            sys.stderr.flush()

            return result

        except Exception as e:
            logger.error(f"❌ 图分析失败: {symbol} - {e}")
            logger.error(f"❌ 错误类型: {type(e).__name__}")
            logger.error(f"❌ 错误详情: {str(e)}")
            import traceback
            logger.error(f"❌ 错误堆栈: {traceback.format_exc()}")

            # 强制刷新日志
            sys.stdout.flush()
            sys.stderr.flush()

            if progress_callback:
                await progress_callback("分析失败", 0, f"分析失败: {str(e)}")
            raise

    async def _background_progress_monitor(self, progress_callback):
        """后台进度监控 - 简化版本"""
        try:
            # 定义进度步骤
            steps = [
                (25, "市场分析师", "分析市场趋势和技术指标"),
                (35, "基本面分析师", "分析财务数据和公司基本面"),
                (45, "新闻分析师", "分析相关新闻和市场情绪"),
                (55, "社交媒体分析师", "分析社交媒体情绪"),
                (65, "看涨研究员", "提出看涨观点和论据"),
                (70, "看跌研究员", "提出看跌观点和论据"),
                (75, "研究经理", "协调研究团队并做出决策"),
                (80, "交易员", "制定具体的交易策略"),
                (85, "风险分析师", "评估投资风险"),
                (90, "风险管理经理", "最终风险评估和投资决策")
            ]

            for progress, agent_name, description in steps:
                await asyncio.sleep(3)  # 等待3秒

                logger.info(f"🔄 [{progress}%] 执行: {agent_name}")
                logger.info(f"📋 任务: {description}")

                # 记录API调用
                await self._log_agent_activities(agent_name)

                if progress_callback:
                    await progress_callback(agent_name, progress, description)

                # 强制刷新日志
                import sys
                sys.stdout.flush()
                sys.stderr.flush()

        except asyncio.CancelledError:
            logger.info("📊 后台监控任务被取消")
        except Exception as e:
            logger.error(f"❌ 后台监控失败: {e}")

    async def _log_agent_activities(self, agent_name: str):
        """记录智能体活动"""
        activities = {
            "市场分析师": [
                "📡 获取股票历史数据",
                "📊 计算技术指标",
                "🤖 生成市场分析报告"
            ],
            "基本面分析师": [
                "📡 获取财务报表数据",
                "📊 计算财务比率",
                "🤖 生成基本面分析报告"
            ],
            "新闻分析师": [
                "📡 获取相关新闻数据",
                "📊 分析新闻情绪",
                "🤖 生成新闻分析报告"
            ],
            "社交媒体分析师": [
                "📡 获取社交媒体数据",
                "📊 分析社交情绪",
                "🤖 生成社交媒体分析报告"
            ],
            "看涨研究员": [
                "📊 整合看涨因素",
                "💭 构建看涨论据",
                "🤖 生成看涨研究报告"
            ],
            "看跌研究员": [
                "📊 整合看跌因素",
                "💭 构建看跌论据",
                "🤖 生成看跌研究报告"
            ],
            "研究经理": [
                "⚖️ 协调研究团队",
                "📊 综合分析结果",
                "🤖 生成综合研究报告"
            ],
            "交易员": [
                "💼 制定交易策略",
                "📈 确定买卖时机",
                "🤖 生成交易计划"
            ],
            "风险分析师": [
                "⚠️ 评估投资风险",
                "📊 计算风险指标",
                "🤖 生成风险评估报告"
            ],
            "风险管理经理": [
                "🎯 整合风险评估",
                "⚖️ 平衡风险收益",
                "🤖 生成最终投资建议"
            ]
        }

        agent_activities = activities.get(agent_name, [f"🔄 执行{agent_name}相关任务"])

        for activity in agent_activities:
            logger.info(f"   {activity}")
            await asyncio.sleep(0.2)  # 短暂延迟


    
    def _create_initial_state(self, symbol: str, analysis_date: str) -> GraphState:
        """创建初始状态"""
        logger.info(f"🔍 _create_initial_state 被调用")
        logger.info(f"🔍 参数: symbol={symbol}, analysis_date={analysis_date}")

        state = GraphState(
            # LangGraph必需字段
            messages=[HumanMessage(content=f"开始分析股票 {symbol}")],

            symbol=symbol,
            company_name=symbol,  # 可以后续通过工具获取公司名称
            analysis_type="comprehensive",
            current_date=analysis_date,
            
            # 数据初始化为None
            stock_data=None,
            financial_data=None,
            market_data=None,
            news_data=None,
            social_data=None,

            # 报告初始化为None
            fundamentals_report=None,
            technical_report=None,
            news_report=None,
            sentiment_report=None,
            social_report=None,

            # 研究员观点初始化为None
            bull_analysis=None,
            bear_analysis=None,

            # 风险管理初始化为None
            risk_assessment=None,
            risky_analysis=None,
            safe_analysis=None,
            neutral_analysis=None,

            # 最终决策初始化为None
            final_recommendation=None,
            investment_plan=None,
            trade_decision=None,
            
            # 辅助信息
            errors=[],
            warnings=[],
            metadata={
                "start_time": datetime.now().isoformat(),
                "graph_version": "1.0.0"
            },
            
            # 执行状态
            current_step="start",
            completed_steps=[],
            next_steps=["market_analyst"],

            # 辩论状态
            debate_history=[],
            debate_summary=None,

            # 风险分析状态
            risk_history=[],
            risk_summary=None
        )

        logger.info(f"🔍 初始状态创建完成: symbol={state['symbol']}, current_date={state['current_date']}")
        return state
    
    def _process_final_state(self, final_state: GraphState) -> Dict[str, Any]:
        """处理最终状态"""
        logger.info(f"🔍 _process_final_state 被调用")
        logger.info(f"🔍 最终状态: symbol={final_state.get('symbol')}, current_step={final_state.get('current_step')}")
        logger.info(f"🔍 完成的步骤: {final_state.get('completed_steps', [])}")
        logger.info(f"🔍 错误列表: {final_state.get('errors', [])}")

        result = {
            "symbol": final_state["symbol"],
            "analysis_date": final_state["current_date"],
            "final_recommendation": final_state["final_recommendation"],
            "investment_plan": final_state["investment_plan"],
            "risk_assessment": final_state["risk_assessment"],
            "reports": {
                "fundamentals": final_state["fundamentals_report"],
                "technical": final_state["technical_report"],
                "news": final_state["news_report"],
                "sentiment": final_state["sentiment_report"]
            },
            "research": {
                "bull_analysis": final_state["bull_analysis"],
                "bear_analysis": final_state["bear_analysis"]
            },
            "metadata": final_state["metadata"],
            "completed_steps": final_state["completed_steps"]
        }

        logger.info(f"🔍 结果处理完成: {result}")
        return result
    
    async def get_graph_visualization(self) -> str:
        """获取图的可视化"""
        if not self.compiled_graph:
            return "图未初始化"
        
        try:
            return self.compiled_graph.get_graph().draw_mermaid()
        except Exception as e:
            logger.error(f"生成图可视化失败: {e}")
            return f"可视化生成失败: {e}"
    
    async def cleanup(self):
        """清理资源"""

        
        if self.agent_nodes:
            await self.agent_nodes.cleanup()
        
        logger.info("✅ 图引擎资源清理完成")
