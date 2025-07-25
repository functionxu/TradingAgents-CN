"""
市场分析师智能体
移植自tradingagents，负责技术分析和市场趋势分析
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..base.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class MarketAnalyst(BaseAgent):
    """
    市场分析师智能体
    专注于技术分析、价格趋势分析和市场情绪分析
    """
    
    def __init__(self, llm_client=None, data_client=None):
        super().__init__(
            name="MarketAnalyst",
            description="专业的市场分析师，擅长技术分析和市场趋势预测",
            llm_client=llm_client,
            data_client=data_client
        )
        self.prompt_template = None
        self.analysis_tools = []
    
    async def _setup_tools(self):
        """设置市场分析工具"""
        self.logger.info("🔧 设置市场分析工具...")
        
        # 这里会设置各种技术分析工具
        self.analysis_tools = [
            "stock_data_tool",      # 股票数据获取
            "technical_indicators", # 技术指标计算
            "price_analysis",       # 价格分析
            "volume_analysis",      # 成交量分析
            "news_sentiment"        # 新闻情绪分析
        ]
        
        self.logger.info(f"✅ 已设置 {len(self.analysis_tools)} 个分析工具")
    
    async def _load_prompts(self):
        """加载市场分析提示词模板"""
        self.prompt_template = """
你是一位专业的股票市场分析师，具有丰富的技术分析经验。

请对股票 {symbol} 进行全面的市场技术分析，包括：

## 分析要求：
1. **技术指标分析**：RSI、MACD、布林带、移动平均线等
2. **价格趋势分析**：支撑位、阻力位、趋势线分析
3. **成交量分析**：量价关系、成交量趋势
4. **市场情绪分析**：结合新闻和市场数据
5. **短期和中期预测**：基于技术分析的价格预测

## 数据基础：
{market_data}

## 新闻情绪：
{news_sentiment}

## 输出格式：
请提供详细的技术分析报告，包含具体的数据支撑和专业判断。
报告应该客观、专业，基于真实数据进行分析。

## 投资建议：
最后给出明确的投资建议：买入/持有/卖出，并说明理由。
"""
    
    async def analyze(self, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行市场技术分析

        Args:
            symbol: 股票代码
            context: 分析上下文，包含日期、市场信息等

        Returns:
            市场分析结果
        """
        self._log_analysis_start(symbol)

        # 检查前提条件
        self._check_prerequisites()

        try:
            # 1. 获取市场数据
            market_data = await self._get_market_data(symbol, context)
            
            # 2. 获取新闻情绪数据
            news_sentiment = await self._get_news_sentiment(symbol, context)
            
            # 3. 执行技术分析
            technical_analysis = await self._perform_technical_analysis(market_data)
            
            # 4. 生成AI分析报告
            ai_analysis = await self._generate_ai_analysis(
                symbol, market_data, news_sentiment, technical_analysis
            )
            
            # 5. 整合分析结果
            result = {
                "analysis_type": "market_analysis",
                "symbol": symbol,
                "analyst": self.name,
                "timestamp": datetime.now().isoformat(),
                "market_data_summary": market_data.get("summary", ""),
                "technical_indicators": technical_analysis,
                "news_sentiment": news_sentiment,
                "ai_analysis": ai_analysis,
                "recommendation": self._extract_recommendation(ai_analysis),
                "confidence_score": self._calculate_confidence(technical_analysis, news_sentiment)
            }
            
            self._log_analysis_complete(symbol, f"推荐: {result['recommendation']}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [{self.name}] 分析失败: {symbol} - {e}")
            return {
                "analysis_type": "market_analysis",
                "symbol": symbol,
                "analyst": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_market_data(self, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取市场数据"""
        if not self.data_client:
            error_msg = "数据客户端未配置，无法获取市场数据。请检查数据服务连接。"
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

        try:
            # 调用数据服务获取股票数据
            data = await self.data_client.get_stock_data(
                symbol=symbol,
                start_date=context.get("start_date"),
                end_date=context.get("end_date", datetime.now().strftime("%Y-%m-%d"))
            )

            if not data or "error" in data:
                error_msg = f"数据服务返回错误或空数据: {data.get('error', '未知错误')}"
                self.logger.error(f"❌ {error_msg}")
                raise RuntimeError(error_msg)

            return data

        except Exception as e:
            error_msg = f"获取市场数据失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    async def _get_news_sentiment(self, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取新闻情绪数据"""
        if not self.data_client:
            error_msg = "数据客户端未配置，无法获取新闻情绪数据。请检查数据服务连接。"
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

        try:
            # 调用数据服务获取新闻数据
            news_data = await self.data_client.get_news_sentiment(symbol)

            if not news_data or "error" in news_data:
                error_msg = f"新闻情绪数据获取失败: {news_data.get('error', '未知错误')}"
                self.logger.error(f"❌ {error_msg}")
                raise RuntimeError(error_msg)

            return news_data

        except Exception as e:
            error_msg = f"获取新闻情绪数据失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    async def _perform_technical_analysis(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行技术分析"""
        if not market_data or "error" in market_data:
            error_msg = f"市场数据无效，无法执行技术分析: {market_data.get('error', '数据为空')}"
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

        try:
            # 检查必要的数据字段
            required_fields = ["current_price", "volume"]
            missing_fields = [field for field in required_fields if field not in market_data]

            if missing_fields:
                error_msg = f"市场数据缺少必要字段: {missing_fields}"
                self.logger.error(f"❌ {error_msg}")
                raise RuntimeError(error_msg)

            # TODO: 实现真实的技术指标计算
            # 这里需要集成技术分析库（如TA-Lib）来计算真实指标
            error_msg = "技术分析功能尚未实现，需要集成技术分析库（如TA-Lib）"
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

        except Exception as e:
            error_msg = f"技术分析执行失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    async def _generate_ai_analysis(self, symbol: str, market_data: Dict,
                                  news_sentiment: Dict, technical_analysis: Dict) -> str:
        """生成AI分析报告"""
        if not self.llm_client:
            error_msg = "LLM客户端未配置，无法生成AI分析报告。请检查LLM服务连接。"
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

        try:
            # 准备提示词
            if not self.prompt_template:
                error_msg = "提示词模板未加载，无法生成AI分析。"
                self.logger.error(f"❌ {error_msg}")
                raise RuntimeError(error_msg)

            prompt = self.prompt_template.format(
                symbol=symbol,
                market_data=str(market_data),
                news_sentiment=str(news_sentiment)
            )

            # 调用LLM服务
            response = await self.llm_client.generate(
                prompt=prompt,
                context={"technical_analysis": technical_analysis}
            )

            if not response or "error" in response:
                error_msg = f"LLM服务返回错误: {response.get('error', '未知错误')}"
                self.logger.error(f"❌ {error_msg}")
                raise RuntimeError(error_msg)

            content = response.get("content")
            if not content:
                error_msg = "LLM服务返回空内容"
                self.logger.error(f"❌ {error_msg}")
                raise RuntimeError(error_msg)

            return content

### 投资建议
基于当前技术分析和市场情绪，建议: 谨慎持有
"""
        except Exception as e:
            self.logger.error(f"❌ AI分析生成失败: {e}")
            return f"AI分析生成失败: {str(e)}"
    
    def _extract_recommendation(self, ai_analysis: str) -> str:
        """从AI分析中提取投资建议"""
        try:
            # 简单的关键词提取
            if "买入" in ai_analysis or "建议买入" in ai_analysis:
                return "买入"
            elif "卖出" in ai_analysis or "建议卖出" in ai_analysis:
                return "卖出"
            else:
                return "持有"
        except:
            return "持有"
    
    def _calculate_confidence(self, technical_analysis: Dict, news_sentiment: Dict) -> float:
        """计算分析置信度"""
        try:
            # 基于技术指标和新闻情绪计算置信度
            base_confidence = 0.7
            
            # 技术指标调整
            rsi = technical_analysis.get("rsi", 50)
            if 30 <= rsi <= 70:  # RSI在正常范围
                base_confidence += 0.1
            
            # 新闻情绪调整
            sentiment_score = news_sentiment.get("sentiment_score", 0.5)
            if abs(sentiment_score - 0.5) > 0.2:  # 情绪明确
                base_confidence += 0.1
            
            return min(base_confidence, 1.0)
        except:
            return 0.7
