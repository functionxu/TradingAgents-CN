"""
智能体节点实现
将智能体包装为图节点，用于LangGraph执行
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from .graph_state import GraphState
from ..agents.analysts.market_analyst import MarketAnalyst
from ..agents.analysts.fundamentals_analyst import FundamentalsAnalyst
from ..agents.analysts.news_analyst import NewsAnalyst
from ..agents.analysts.social_analyst import SocialAnalyst
from ..agents.researchers.bull_researcher import BullResearcher
from ..agents.researchers.bear_researcher import BearResearcher
from ..agents.researchers.research_manager import ResearchManager
from ..agents.traders.trader import Trader
from ..agents.managers.risk_manager import RiskManager

logger = logging.getLogger(__name__)

class AgentNodes:
    """智能体节点管理器"""

    def __init__(self, llm_client=None, data_client=None):
        # 客户端工具
        self.llm_client = llm_client
        self.data_client = data_client

        # 分析师智能体
        self.market_analyst: Optional[MarketAnalyst] = None
        self.fundamentals_analyst: Optional[FundamentalsAnalyst] = None
        self.news_analyst: Optional[NewsAnalyst] = None
        self.social_analyst: Optional[SocialAnalyst] = None

        # 研究员智能体
        self.bull_researcher: Optional[BullResearcher] = None
        self.bear_researcher: Optional[BearResearcher] = None
        self.research_manager: Optional[ResearchManager] = None

        # 交易员智能体
        self.trader: Optional[Trader] = None

        # 管理者智能体
        self.risk_manager: Optional[RiskManager] = None

        self.initialized = False
    
    async def initialize(self):
        """初始化所有智能体"""
        try:
            logger.info("🤖 初始化智能体节点...")
            
            # 初始化分析师 - 传递必要的客户端
            logger.info("🔧 初始化分析师智能体...")
            self.market_analyst = MarketAnalyst(
                llm_client=self.llm_client,
                data_client=self.data_client
            )
            self.fundamentals_analyst = FundamentalsAnalyst(
                llm_client=self.llm_client,
                data_client=self.data_client
            )
            self.news_analyst = NewsAnalyst(
                llm_client=self.llm_client,
                data_client=self.data_client
            )
            self.social_analyst = SocialAnalyst(
                llm_client=self.llm_client,
                data_client=self.data_client
            )

            # 初始化研究员
            logger.info("🔧 初始化研究员智能体...")
            self.bull_researcher = BullResearcher(
                llm_client=self.llm_client,
                data_client=self.data_client
            )
            self.bear_researcher = BearResearcher(
                llm_client=self.llm_client,
                data_client=self.data_client
            )
            self.research_manager = ResearchManager(
                llm_client=self.llm_client,
                data_client=self.data_client
            )

            # 初始化交易员
            logger.info("🔧 初始化交易员智能体...")
            self.trader = Trader(
                llm_client=self.llm_client,
                data_client=self.data_client
            )

            # 初始化管理者
            logger.info("🔧 初始化管理者智能体...")
            self.risk_manager = RiskManager(
                llm_client=self.llm_client,
                data_client=self.data_client
            )
            
            # 加载提示词模板
            logger.info("🔧 加载智能体提示词模板...")
            await self._load_prompts()

            # 验证智能体初始化
            await self._validate_agents()

            self.initialized = True
            logger.info("✅ 智能体节点初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 智能体节点初始化失败: {e}")
            raise
    
    async def _load_prompts(self):
        """加载所有智能体的提示词模板"""
        try:
            agents = [
                self.market_analyst, self.fundamentals_analyst,
                self.news_analyst, self.social_analyst,
                self.bull_researcher, self.bear_researcher,
                self.research_manager, self.trader, self.risk_manager
            ]
            
            for agent in agents:
                if agent and hasattr(agent, '_load_prompts'):
                    await agent._load_prompts()
                    
        except Exception as e:
            logger.warning(f"⚠️ 提示词加载失败: {e}")

    async def _validate_agents(self):
        """验证智能体初始化状态"""
        try:
            logger.info("🔍 验证智能体初始化状态...")

            agents = {
                "market_analyst": self.market_analyst,
                "fundamentals_analyst": self.fundamentals_analyst,
                "news_analyst": self.news_analyst,
                "social_analyst": self.social_analyst,
                "bull_researcher": self.bull_researcher,
                "bear_researcher": self.bear_researcher,
                "research_manager": self.research_manager,
                "trader": self.trader,
                "risk_manager": self.risk_manager
            }

            for name, agent in agents.items():
                if agent is None:
                    logger.error(f"❌ 智能体未初始化: {name}")
                else:
                    logger.info(f"✅ 智能体已初始化: {name} ({agent.__class__.__name__})")

                    # 检查智能体的基本属性
                    if hasattr(agent, 'name'):
                        logger.info(f"   - 名称: {agent.name}")
                    if hasattr(agent, 'llm_client'):
                        logger.info(f"   - LLM客户端: {agent.llm_client is not None}")
                    if hasattr(agent, 'data_client'):
                        logger.info(f"   - 数据客户端: {agent.data_client is not None}")

            logger.info("✅ 智能体验证完成")

        except Exception as e:
            logger.error(f"❌ 智能体验证失败: {e}")

    def get_analyst_node(self, analyst_type: str):
        """获取分析师节点函数"""
        analyst_map = {
            "market": self.market_analyst_node,
            "fundamentals": self.fundamentals_analyst_node,
            "news": self.news_analyst_node,
            "social": self.social_analyst_node
        }
        node_func = analyst_map.get(analyst_type)
        logger.info(f"🔍 获取分析师节点: {analyst_type} -> {node_func}")
        return node_func
    
    async def market_analyst_node(self, state: GraphState) -> GraphState:
        """市场分析师节点"""
        try:
            logger.info(f"📈 市场分析师分析: {state['symbol']}")
            
            if not self.market_analyst:
                raise ValueError("市场分析师未初始化")
            
            # 执行分析
            result = await self.market_analyst.analyze(
                symbol=state["symbol"],
                context=state
            )
            
            # 更新状态
            state["technical_report"] = result
            state["current_step"] = "market_analysis_complete"
            
            logger.info(f"✅ 市场分析完成: {state['symbol']}")
            return state
            
        except Exception as e:
            logger.error(f"❌ 市场分析失败: {e}")
            state["errors"] = state.get("errors", []) + [f"市场分析失败: {str(e)}"]
            return state
    
    async def fundamentals_analyst_node(self, state: GraphState) -> GraphState:
        """基本面分析师节点"""
        try:
            logger.info(f"📊 基本面分析师分析: {state['symbol']}")
            
            if not self.fundamentals_analyst:
                raise ValueError("基本面分析师未初始化")
            
            result = await self.fundamentals_analyst.analyze(
                symbol=state["symbol"],
                context=state
            )
            
            state["fundamentals_report"] = result
            state["current_step"] = "fundamentals_analysis_complete"
            
            logger.info(f"✅ 基本面分析完成: {state['symbol']}")
            return state
            
        except Exception as e:
            logger.error(f"❌ 基本面分析失败: {e}")
            state["errors"] = state.get("errors", []) + [f"基本面分析失败: {str(e)}"]
            return state
    
    async def news_analyst_node(self, state: GraphState) -> GraphState:
        """新闻分析师节点"""
        try:
            logger.info(f"📰 新闻分析师分析: {state['symbol']}")
            
            if not self.news_analyst:
                raise ValueError("新闻分析师未初始化")
            
            result = await self.news_analyst.analyze(
                symbol=state["symbol"],
                context=state
            )
            
            state["news_report"] = result
            state["current_step"] = "news_analysis_complete"
            
            logger.info(f"✅ 新闻分析完成: {state['symbol']}")
            return state
            
        except Exception as e:
            logger.error(f"❌ 新闻分析失败: {e}")
            state["errors"] = state.get("errors", []) + [f"新闻分析失败: {str(e)}"]
            return state
    
    async def social_analyst_node(self, state: GraphState) -> GraphState:
        """社交媒体分析师节点"""
        try:
            logger.info(f"💬 社交媒体分析师分析: {state['symbol']}")
            
            if not self.social_analyst:
                raise ValueError("社交媒体分析师未初始化")
            
            result = await self.social_analyst.analyze(
                symbol=state["symbol"],
                context=state
            )
            
            state["social_report"] = result
            state["current_step"] = "social_analysis_complete"
            
            logger.info(f"✅ 社交媒体分析完成: {state['symbol']}")
            return state
            
        except Exception as e:
            logger.error(f"❌ 社交媒体分析失败: {e}")
            state["errors"] = state.get("errors", []) + [f"社交媒体分析失败: {str(e)}"]
            return state
    
    async def bull_researcher_node(self, state: GraphState) -> GraphState:
        """看涨研究员节点"""
        try:
            logger.info(f"🐂 看涨研究员分析: {state['symbol']}")
            
            if not self.bull_researcher:
                raise ValueError("看涨研究员未初始化")
            
            result = await self.bull_researcher.analyze(
                symbol=state["symbol"],
                context=state
            )
            
            state["bull_opinion"] = result
            state["current_step"] = "bull_research_complete"
            
            logger.info(f"✅ 看涨研究完成: {state['symbol']}")
            return state
            
        except Exception as e:
            logger.error(f"❌ 看涨研究失败: {e}")
            state["errors"] = state.get("errors", []) + [f"看涨研究失败: {str(e)}"]
            return state
    
    async def bear_researcher_node(self, state: GraphState) -> GraphState:
        """看跌研究员节点"""
        try:
            logger.info(f"🐻 看跌研究员分析: {state['symbol']}")
            
            if not self.bear_researcher:
                raise ValueError("看跌研究员未初始化")
            
            result = await self.bear_researcher.analyze(
                symbol=state["symbol"],
                context=state
            )
            
            state["bear_opinion"] = result
            state["current_step"] = "bear_research_complete"
            
            logger.info(f"✅ 看跌研究完成: {state['symbol']}")
            return state
            
        except Exception as e:
            logger.error(f"❌ 看跌研究失败: {e}")
            state["errors"] = state.get("errors", []) + [f"看跌研究失败: {str(e)}"]
            return state
    
    async def research_manager_node(self, state: GraphState) -> GraphState:
        """研究经理节点"""
        try:
            logger.info(f"👔 研究经理决策: {state['symbol']}")
            
            if not self.research_manager:
                raise ValueError("研究经理未初始化")
            
            result = await self.research_manager.analyze(
                symbol=state["symbol"],
                context=state
            )
            
            state["research_decision"] = result
            state["current_step"] = "research_decision_complete"
            
            logger.info(f"✅ 研究决策完成: {state['symbol']}")
            return state
            
        except Exception as e:
            logger.error(f"❌ 研究决策失败: {e}")
            state["errors"] = state.get("errors", []) + [f"研究决策失败: {str(e)}"]
            return state

    async def trader_node(self, state: GraphState) -> GraphState:
        """交易员节点"""
        try:
            logger.info(f"💼 交易员制定策略: {state['symbol']}")

            if not self.trader:
                raise ValueError("交易员未初始化")

            result = await self.trader.analyze(
                symbol=state["symbol"],
                context=state
            )

            state["investment_plan"] = result
            state["current_step"] = "trading_strategy_complete"

            logger.info(f"✅ 交易策略完成: {state['symbol']}")
            return state

        except Exception as e:
            logger.error(f"❌ 交易策略失败: {e}")
            state["errors"] = state.get("errors", []) + [f"交易策略失败: {str(e)}"]
            return state

    async def risk_manager_node(self, state: GraphState) -> GraphState:
        """风险管理经理节点"""
        try:
            logger.info(f"⚖️ 风险管理经理最终决策: {state['symbol']}")

            if not self.risk_manager:
                raise ValueError("风险管理经理未初始化")

            result = await self.risk_manager.analyze(
                symbol=state["symbol"],
                context=state
            )

            state["final_decision"] = result
            state["current_step"] = "final_decision_complete"

            logger.info(f"✅ 最终决策完成: {state['symbol']}")
            return state

        except Exception as e:
            logger.error(f"❌ 最终决策失败: {e}")
            state["errors"] = state.get("errors", []) + [f"最终决策失败: {str(e)}"]
            return state

    # 兼容性方法 - 为了支持旧的节点名称
    async def risky_analyst_node(self, state: GraphState) -> GraphState:
        """风险分析师节点 (兼容性方法)"""
        logger.info("⚠️ 使用兼容性风险分析师节点，建议使用新的智能体架构")
        return await self.bear_researcher_node(state)

    async def safe_analyst_node(self, state: GraphState) -> GraphState:
        """安全分析师节点 (兼容性方法)"""
        logger.info("⚠️ 使用兼容性安全分析师节点，建议使用新的智能体架构")
        return await self.bull_researcher_node(state)

    async def neutral_analyst_node(self, state: GraphState) -> GraphState:
        """中性分析师节点 (兼容性方法)"""
        logger.info("⚠️ 使用兼容性中性分析师节点，建议使用新的智能体架构")
        # 创建一个中性的分析结果
        try:
            state["neutral_opinion"] = {
                "analysis_type": "neutral_analysis",
                "symbol": state["symbol"],
                "analyst": "NeutralAnalyst",
                "recommendation": "HOLD",
                "confidence": 0.5,
                "reasoning": "中性观点：建议观望，等待更明确的市场信号",
                "timestamp": state.get("timestamp", "")
            }
            state["current_step"] = "neutral_analysis_complete"
            logger.info(f"✅ 中性分析完成: {state['symbol']}")
            return state
        except Exception as e:
            logger.error(f"❌ 中性分析失败: {e}")
            state["errors"] = state.get("errors", []) + [f"中性分析失败: {str(e)}"]
            return state

    async def cleanup(self):
        """清理智能体资源"""
        try:
            logger.info("🧹 清理智能体节点资源...")

            # 清理所有智能体
            agents = [
                self.market_analyst, self.fundamentals_analyst,
                self.news_analyst, self.social_analyst,
                self.bull_researcher, self.bear_researcher,
                self.research_manager, self.trader, self.risk_manager
            ]

            for agent in agents:
                if agent and hasattr(agent, 'cleanup'):
                    try:
                        await agent.cleanup()
                    except Exception as e:
                        logger.warning(f"⚠️ 智能体清理失败: {e}")

            # 重置状态
            self.market_analyst = None
            self.fundamentals_analyst = None
            self.news_analyst = None
            self.social_analyst = None
            self.bull_researcher = None
            self.bear_researcher = None
            self.research_manager = None
            self.trader = None
            self.risk_manager = None
            self.initialized = False

            logger.info("✅ 智能体节点资源清理完成")

        except Exception as e:
            logger.error(f"❌ 智能体节点清理失败: {e}")

    def get_agent_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "initialized": self.initialized,
            "agents": {
                "market_analyst": self.market_analyst is not None,
                "fundamentals_analyst": self.fundamentals_analyst is not None,
                "news_analyst": self.news_analyst is not None,
                "social_analyst": self.social_analyst is not None,
                "bull_researcher": self.bull_researcher is not None,
                "bear_researcher": self.bear_researcher is not None,
                "research_manager": self.research_manager is not None,
                "trader": self.trader is not None,
                "risk_manager": self.risk_manager is not None
            }
        }
