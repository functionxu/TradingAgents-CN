"""
智能体管理器
负责智能体的注册、发现、生命周期管理和负载均衡
"""

import asyncio
from typing import Dict, List, Any, Optional, Type
from datetime import datetime, timedelta
from collections import defaultdict

from backend.shared.utils.logger import get_service_logger
from backend.shared.database.mongodb import MongoDBManager
import redis.asyncio as redis

from .base_agent import BaseAgent, AgentType, AgentStatus, TaskType, TaskContext, TaskResult
from .analysts.fundamentals_analyst import FundamentalsAnalyst
from .analysts.market_analyst import MarketAnalyst
from .analysts.news_analyst import NewsAnalyst
from .analysts.social_media_analyst import SocialMediaAnalyst
from .researchers.bull_researcher import BullResearcher
from .researchers.bear_researcher import BearResearcher
from .managers.research_manager import ResearchManager
from .managers.risk_manager import RiskManager
from .traders.trader import Trader
from .risk_assessors.risky_debator import RiskyDebator
from .risk_assessors.safe_debator import SafeDebator
from .risk_assessors.neutral_debator import NeutralDebator

logger = get_service_logger("agent-service.agent_manager")


class AgentManager:
    """智能体管理器"""
    
    def __init__(
        self,
        db_manager: MongoDBManager,
        redis_client: redis.Redis,
        state_manager: Any
    ):
        self.db_manager = db_manager
        self.redis_client = redis_client
        self.state_manager = state_manager
        
        # 智能体注册表
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_types: Dict[AgentType, List[BaseAgent]] = defaultdict(list)
        
        # 智能体类型映射
        self.agent_classes: Dict[AgentType, Type[BaseAgent]] = {
            AgentType.FUNDAMENTALS_ANALYST: FundamentalsAnalyst,
            AgentType.MARKET_ANALYST: MarketAnalyst,
            AgentType.NEWS_ANALYST: NewsAnalyst,
            AgentType.SOCIAL_MEDIA_ANALYST: SocialMediaAnalyst,
            AgentType.BULL_RESEARCHER: BullResearcher,
            AgentType.BEAR_RESEARCHER: BearResearcher,
            AgentType.RESEARCH_MANAGER: ResearchManager,
            AgentType.RISK_MANAGER: RiskManager,
            AgentType.TRADER: Trader,
            AgentType.RISKY_DEBATOR: RiskyDebator,
            AgentType.SAFE_DEBATOR: SafeDebator,
            AgentType.NEUTRAL_DEBATOR: NeutralDebator,
        }
        
        # 负载均衡策略
        self.load_balancer = LoadBalancer()
        
        # 健康检查任务
        self.health_check_task: Optional[asyncio.Task] = None
        self.health_check_interval = 60  # 秒
        
        logger.info("🏗️ 智能体管理器初始化")
    
    async def initialize(self):
        """初始化智能体管理器"""
        try:
            # 创建默认智能体实例
            await self._create_default_agents()
            
            # 启动健康检查
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info(f"✅ 智能体管理器初始化完成，注册了{len(self.agents)}个智能体")
            
        except Exception as e:
            logger.error(f"❌ 智能体管理器初始化失败: {e}")
            raise
    
    async def _create_default_agents(self):
        """创建默认智能体实例"""
        # 为每种类型创建一个默认实例
        for agent_type, agent_class in self.agent_classes.items():
            try:
                agent = agent_class(agent_type=agent_type)
                await self.register_agent(agent)
                logger.info(f"✅ 创建默认智能体: {agent_type.value}")
            except Exception as e:
                logger.error(f"❌ 创建智能体失败 {agent_type.value}: {e}")
    
    async def register_agent(self, agent: BaseAgent) -> bool:
        """注册智能体"""
        try:
            # 添加详细调试日志
            logger.info(f"🔍 开始注册智能体: {agent.agent_type.value} (ID: {agent.agent_id})")

            # 检查是否已存在
            if agent.agent_id in self.agents:
                logger.warning(f"⚠️ 智能体已存在: {agent.agent_id}")
                return False

            # 注册到本地注册表
            logger.info(f"🔍 注册到本地注册表: {agent.agent_type.value}")
            self.agents[agent.agent_id] = agent

            logger.info(f"🔍 添加到类型列表: {agent.agent_type.value}")
            self.agent_types[agent.agent_type].append(agent)

            logger.info(f"🔍 当前 {agent.agent_type.value} 类型智能体数量: {len(self.agent_types[agent.agent_type])}")

            # 注册到Redis（用于分布式发现）
            logger.info(f"🔍 注册到Redis: {agent.agent_type.value}")
            await self._register_to_redis(agent)

            # 保存到数据库
            logger.info(f"🔍 保存到数据库: {agent.agent_type.value}")
            await self._save_agent_to_db(agent)

            logger.info(f"✅ 智能体注册成功: {agent.agent_type.value} (ID: {agent.agent_id})")
            return True

        except Exception as e:
            logger.error(f"❌ 智能体注册失败: {e}")
            import traceback
            logger.error(f"❌ 详细错误信息: {traceback.format_exc()}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"⚠️ 智能体不存在: {agent_id}")
                return False
            
            agent = self.agents[agent_id]
            
            # 从本地注册表移除
            del self.agents[agent_id]
            self.agent_types[agent.agent_type].remove(agent)
            
            # 从Redis移除
            await self._unregister_from_redis(agent)
            
            # 从数据库移除
            await self._remove_agent_from_db(agent_id)
            
            logger.info(f"✅ 智能体注销成功: {agent.agent_type.value} (ID: {agent_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 智能体注销失败: {e}")
            return False
    
    async def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取智能体"""
        return self.agents.get(agent_id)
    
    async def get_agents_by_type(self, agent_type: AgentType) -> List[BaseAgent]:
        """根据类型获取智能体"""
        logger.info(f"🔍 查询智能体类型: {agent_type.value}")

        # 直接通过值查找，避免枚举对象比较问题
        agents = []
        for key, value_list in self.agent_types.items():
            if key.value == agent_type.value:
                agents = value_list
                logger.info(f"🔍 找到 {len(agents)} 个 {agent_type.value} 智能体")
                break

        if not agents:
            logger.warning(f"⚠️ 未找到类型为 {agent_type.value} 的智能体")
            logger.info(f"🔍 可用智能体类型: {[key.value for key in self.agent_types.keys()]}")

        return agents
    
    async def get_available_agent(
        self,
        agent_type: AgentType,
        task_type: TaskType,
        market: str = "US"
    ) -> Optional[BaseAgent]:
        """获取可用的智能体"""
        # 添加详细调试日志
        logger.info(f"🔍 查找智能体: agent_type={agent_type}, agent_type.value={agent_type.value}")

        agents = await self.get_agents_by_type(agent_type)
        logger.info(f"🔍 找到 {len(agents)} 个 {agent_type.value} 类型的智能体")

        # 过滤可用的智能体
        available_agents = []
        for agent in agents:
            is_idle = agent.status == AgentStatus.IDLE
            can_handle = agent.can_handle_task(task_type, market)

            logger.info(f"🔍 智能体 {agent.agent_id[:8]}: idle={is_idle}, can_handle={can_handle}")
            if not can_handle:
                logger.info(f"🔍 智能体能力: {[cap.name for cap in agent.capabilities]}")
                logger.info(f"🔍 支持市场: {[cap.supported_markets for cap in agent.capabilities]}")
                logger.info(f"🔍 请求任务类型: {task_type}, 请求市场: {market}")

            if is_idle and can_handle:
                available_agents.append(agent)

        logger.info(f"🔍 其中 {len(available_agents)} 个智能体可用")

        if not available_agents:
            logger.warning(f"⚠️ 没有可用的智能体: {agent_type.value}")
            # 添加更多调试信息
            logger.info(f"🔍 所有智能体状态:")
            for agent in agents:
                logger.info(f"  - {agent.agent_type.value} (ID: {agent.agent_id}): status={agent.status}")
            return None

        # 使用负载均衡选择智能体
        selected_agent = self.load_balancer.select_agent(available_agents)

        logger.info(f"🎯 选择智能体: {selected_agent.agent_type.value} (ID: {selected_agent.agent_id})")
        return selected_agent
    
    async def execute_task(
        self,
        agent_type: AgentType,
        task_type: TaskType,
        context: TaskContext
    ) -> TaskResult:
        """执行任务"""
        try:
            # 添加详细调试日志
            logger.info(f"🔍 执行任务开始: agent_type={agent_type}, task_type={task_type}")
            logger.info(f"🔍 agent_type.value={agent_type.value}, type={type(agent_type)}")

            # 获取可用智能体
            agent = await self.get_available_agent(agent_type, task_type, context.market)
            if not agent:
                logger.error(f"🔍 获取智能体失败: agent_type={agent_type}, agent_type.value={agent_type.value}")
                raise Exception(f"没有可用的智能体: {agent_type.value}")

            logger.info(f"🔍 获取到智能体: {agent.agent_type.value}")

            # 执行任务
            result = await agent.execute_task(context)

            # 记录任务结果
            await self._record_task_result(result)

            return result

        except Exception as e:
            logger.error(f"❌ 任务执行失败: {e}")
            # 返回错误结果
            return TaskResult(
                task_id=context.task_id,
                agent_id="unknown",
                agent_type=agent_type,
                status="error",
                result={},
                error=str(e)
            )
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        total_agents = len(self.agents)
        active_agents = len([a for a in self.agents.values() if a.status != AgentStatus.OFFLINE])
        busy_agents = len([a for a in self.agents.values() if a.status == AgentStatus.BUSY])
        error_agents = len([a for a in self.agents.values() if a.status == AgentStatus.ERROR])
        
        # 按类型统计
        type_stats = {}
        for agent_type in AgentType:
            agents = self.agent_types.get(agent_type, [])
            type_stats[agent_type.value] = {
                "total": len(agents),
                "active": len([a for a in agents if a.status != AgentStatus.OFFLINE]),
                "busy": len([a for a in agents if a.status == AgentStatus.BUSY])
            }
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "busy_agents": busy_agents,
            "error_agents": error_agents,
            "idle_agents": active_agents - busy_agents,
            "type_statistics": type_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查所有智能体
            healthy_count = 0
            for agent in self.agents.values():
                if await agent.health_check():
                    healthy_count += 1
            
            health_ratio = healthy_count / len(self.agents) if self.agents else 0
            
            logger.info(f"🏥 健康检查完成: {healthy_count}/{len(self.agents)} 智能体健康")
            
            return health_ratio > 0.8  # 80%以上健康才算系统健康
            
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return False
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self.health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 健康检查循环错误: {e}")
    
    async def _register_to_redis(self, agent: BaseAgent):
        """注册到Redis"""
        try:
            key = f"agent:{agent.agent_id}"
            value = {
                "agent_type": agent.agent_type.value,
                "status": agent.status.value,
                "created_at": agent.created_at.isoformat(),
                "last_heartbeat": agent.last_heartbeat.isoformat()
            }
            await self.redis_client.hset(key, mapping=value)
            await self.redis_client.expire(key, 3600)  # 1小时过期
        except Exception as e:
            logger.error(f"❌ Redis注册失败: {e}")
    
    async def _unregister_from_redis(self, agent: BaseAgent):
        """从Redis注销"""
        try:
            key = f"agent:{agent.agent_id}"
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"❌ Redis注销失败: {e}")
    
    async def _save_agent_to_db(self, agent: BaseAgent):
        """保存到数据库"""
        try:
            if self.db_manager.is_connected():
                collection = self.db_manager.get_collection("agents")
                await collection.insert_one(agent.get_status())
        except Exception as e:
            logger.error(f"❌ 数据库保存失败: {e}")
    
    async def _remove_agent_from_db(self, agent_id: str):
        """从数据库移除"""
        try:
            if self.db_manager.is_connected():
                collection = self.db_manager.get_collection("agents")
                await collection.delete_one({"agent_id": agent_id})
        except Exception as e:
            logger.error(f"❌ 数据库移除失败: {e}")
    
    async def _record_task_result(self, result: TaskResult):
        """记录任务结果"""
        try:
            if self.db_manager.is_connected():
                collection = self.db_manager.get_collection("task_results")
                await collection.insert_one(result.to_dict())
        except Exception as e:
            logger.error(f"❌ 任务结果记录失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 取消健康检查任务
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # 注销所有智能体
            for agent_id in list(self.agents.keys()):
                await self.unregister_agent(agent_id)
            
            logger.info("✅ 智能体管理器清理完成")
            
        except Exception as e:
            logger.error(f"❌ 智能体管理器清理失败: {e}")


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self.round_robin_counters: Dict[AgentType, int] = defaultdict(int)
    
    def select_agent(self, agents: List[BaseAgent]) -> BaseAgent:
        """选择智能体"""
        if not agents:
            raise ValueError("没有可用的智能体")
        
        if len(agents) == 1:
            return agents[0]
        
        if self.strategy == "round_robin":
            return self._round_robin_select(agents)
        elif self.strategy == "least_busy":
            return self._least_busy_select(agents)
        elif self.strategy == "best_performance":
            return self._best_performance_select(agents)
        else:
            return agents[0]  # 默认选择第一个
    
    def _round_robin_select(self, agents: List[BaseAgent]) -> BaseAgent:
        """轮询选择"""
        agent_type = agents[0].agent_type
        index = self.round_robin_counters[agent_type] % len(agents)
        self.round_robin_counters[agent_type] += 1
        return agents[index]
    
    def _least_busy_select(self, agents: List[BaseAgent]) -> BaseAgent:
        """选择最不繁忙的智能体"""
        return min(agents, key=lambda a: len(a.current_tasks))
    
    def _best_performance_select(self, agents: List[BaseAgent]) -> BaseAgent:
        """选择性能最好的智能体"""
        return max(agents, key=lambda a: a.metrics.success_rate)
