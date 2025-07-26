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
        """获取市场数据 - 使用Data Service API"""
        if not self.data_client:
            error_msg = "数据客户端未配置，无法获取市场数据。请检查数据服务连接。"
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

        try:
            self.logger.info(f"📊 [数据获取] 开始获取市场数据: {symbol}")

            # 使用Data Service API获取结构化数据
            data = await self.data_client.get_stock_data(
                symbol=symbol,
                start_date=context.get("start_date"),
                end_date=context.get("end_date", datetime.now().strftime("%Y-%m-%d"))
            )

            self.logger.info(f"📊 [数据获取] Data Service响应: {type(data)}")

            # 检查数据是否有效
            if not data:
                error_msg = f"数据服务返回空数据"
                self.logger.error(f"❌ {error_msg}")
                raise RuntimeError(error_msg)

            # 如果data是字符串（旧接口），需要解析
            if isinstance(data, str):
                if "❌" in data or "error" in data.lower():
                    error_msg = f"数据服务返回错误: {data}"
                    self.logger.error(f"❌ {error_msg}")
                    raise RuntimeError(error_msg)

                # 旧接口返回字符串，需要转换为结构化数据
                self.logger.warning(f"⚠️ 收到字符串格式数据，尝试解析...")
                return self._parse_string_data_to_structured(data, symbol)

            # 如果data是字典（新接口），需要提取data字段
            elif isinstance(data, dict):
                if "error" in data:
                    error_msg = f"数据服务返回错误: {data.get('error', '未知错误')}"
                    self.logger.error(f"❌ {error_msg}")
                    raise RuntimeError(error_msg)

                # 检查是否是Data Service的标准响应格式
                if "success" in data and "data" in data:
                    if data.get("success"):
                        actual_data = data["data"]
                        self.logger.info(f"✅ 收到Data Service响应，提取数据字段: {list(actual_data.keys())}")
                        return actual_data
                    else:
                        error_msg = f"数据服务返回失败: {data.get('message', '未知错误')}"
                        self.logger.error(f"❌ {error_msg}")
                        raise RuntimeError(error_msg)
                else:
                    # 直接的数据字典
                    self.logger.info(f"✅ 收到直接数据字典，字段: {list(data.keys())}")
                    return data

            else:
                error_msg = f"数据服务返回未知格式: {type(data)}"
                self.logger.error(f"❌ {error_msg}")
                raise RuntimeError(error_msg)

        except Exception as e:
            error_msg = f"获取市场数据失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

    def _parse_string_data_to_structured(self, data_str: str, symbol: str) -> Dict[str, Any]:
        """将字符串格式的数据解析为结构化数据"""
        try:
            self.logger.info(f"🔄 [数据解析] 解析字符串数据为结构化格式")

            # 尝试从字符串中提取价格和成交量信息
            import re

            # 查找价格信息
            price_pattern = r'(?:价格|Price|收盘价|Close)[:：]\s*([0-9]+\.?[0-9]*)'
            price_match = re.search(price_pattern, data_str, re.IGNORECASE)
            current_price = float(price_match.group(1)) if price_match else 0.0

            # 查找成交量信息
            volume_pattern = r'(?:成交量|Volume|交易量)[:：]\s*([0-9,]+)'
            volume_match = re.search(volume_pattern, data_str, re.IGNORECASE)
            volume = int(volume_match.group(1).replace(',', '')) if volume_match else 0

            # 构造结构化数据
            structured_data = {
                "symbol": symbol,
                "current_price": current_price,
                "volume": volume,
                "raw_data": data_str,
                "data_source": "parsed_from_string"
            }

            self.logger.info(f"✅ [数据解析] 解析完成: current_price={current_price}, volume={volume}")
            return structured_data

        except Exception as e:
            self.logger.error(f"❌ [数据解析] 解析失败: {str(e)}")
            # 返回默认结构，避免分析完全失败
            return {
                "symbol": symbol,
                "current_price": 0.0,
                "volume": 0,
                "raw_data": data_str,
                "data_source": "parse_failed",
                "error": str(e)
            }

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

            # 实现技术指标计算
            self.logger.info(f"🔧 [技术分析] 开始计算技术指标...")

            # 提取价格数据
            close_prices = market_data.get("close_prices", [])
            volumes = market_data.get("volumes", [])

            if not close_prices or len(close_prices) < 5:
                error_msg = f"价格数据不足，无法计算技术指标。需要至少5个数据点，当前: {len(close_prices)}"
                self.logger.error(f"❌ {error_msg}")
                raise RuntimeError(error_msg)

            # 计算技术指标
            indicators = self._calculate_technical_indicators(close_prices, volumes)

            # 生成技术分析结果
            analysis_result = {
                "symbol": market_data.get("symbol"),
                "current_price": market_data.get("current_price"),
                "volume": market_data.get("volume"),
                "indicators": indicators,
                "signals": self._generate_trading_signals(indicators),
                "trend_analysis": self._analyze_trend(close_prices),
                "support_resistance": self._find_support_resistance(close_prices),
                "analysis_summary": self._generate_analysis_summary(indicators, close_prices)
            }

            self.logger.info(f"✅ [技术分析] 技术指标计算完成")
            return analysis_result

        except Exception as e:
            error_msg = f"技术分析执行失败: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

    def _calculate_technical_indicators(self, close_prices: list, volumes: list) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            import pandas as pd
            import numpy as np

            # 转换为pandas Series
            prices = pd.Series(close_prices)
            vols = pd.Series(volumes) if volumes else pd.Series([0] * len(close_prices))

            indicators = {}

            # 移动平均线
            if len(prices) >= 5:
                indicators['MA5'] = float(prices.rolling(5).mean().iloc[-1])
            if len(prices) >= 10:
                indicators['MA10'] = float(prices.rolling(10).mean().iloc[-1])
            if len(prices) >= 20:
                indicators['MA20'] = float(prices.rolling(20).mean().iloc[-1])

            # RSI (相对强弱指数)
            if len(prices) >= 14:
                delta = prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators['RSI'] = float(rsi.iloc[-1])

            # MACD
            if len(prices) >= 26:
                exp1 = prices.ewm(span=12).mean()
                exp2 = prices.ewm(span=26).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9).mean()
                indicators['MACD'] = float(macd.iloc[-1])
                indicators['MACD_Signal'] = float(signal.iloc[-1])
                indicators['MACD_Histogram'] = float((macd - signal).iloc[-1])

            # 布林带
            if len(prices) >= 20:
                sma = prices.rolling(20).mean()
                std = prices.rolling(20).std()
                indicators['BB_Upper'] = float((sma + 2 * std).iloc[-1])
                indicators['BB_Middle'] = float(sma.iloc[-1])
                indicators['BB_Lower'] = float((sma - 2 * std).iloc[-1])

            # 成交量移动平均
            if len(vols) >= 20:
                indicators['Volume_MA20'] = float(vols.rolling(20).mean().iloc[-1])

            self.logger.info(f"📊 [技术指标] 计算完成: {list(indicators.keys())}")
            return indicators

        except Exception as e:
            self.logger.error(f"❌ [技术指标] 计算失败: {str(e)}")
            return {}

    def _generate_trading_signals(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """生成交易信号"""
        signals = {
            "buy_signals": [],
            "sell_signals": [],
            "neutral_signals": [],
            "overall_signal": "neutral",
            "confidence": 0.5
        }

        try:
            # RSI信号
            rsi = indicators.get('RSI')
            if rsi is not None:
                if rsi < 30:
                    signals["buy_signals"].append(f"RSI超卖({rsi:.1f})")
                elif rsi > 70:
                    signals["sell_signals"].append(f"RSI超买({rsi:.1f})")
                else:
                    signals["neutral_signals"].append(f"RSI正常({rsi:.1f})")

            # MACD信号
            macd = indicators.get('MACD')
            macd_signal = indicators.get('MACD_Signal')
            if macd is not None and macd_signal is not None:
                if macd > macd_signal:
                    signals["buy_signals"].append("MACD金叉")
                else:
                    signals["sell_signals"].append("MACD死叉")

            # 移动平均线信号
            ma5 = indicators.get('MA5')
            ma20 = indicators.get('MA20')
            if ma5 is not None and ma20 is not None:
                if ma5 > ma20:
                    signals["buy_signals"].append("短期均线上穿长期均线")
                else:
                    signals["sell_signals"].append("短期均线下穿长期均线")

            # 布林带信号
            bb_upper = indicators.get('BB_Upper')
            bb_lower = indicators.get('BB_Lower')
            current_price = indicators.get('current_price')
            if bb_upper and bb_lower and current_price:
                if current_price > bb_upper:
                    signals["sell_signals"].append("价格突破布林带上轨")
                elif current_price < bb_lower:
                    signals["buy_signals"].append("价格跌破布林带下轨")

            # 计算综合信号
            buy_count = len(signals["buy_signals"])
            sell_count = len(signals["sell_signals"])

            if buy_count > sell_count:
                signals["overall_signal"] = "buy"
                signals["confidence"] = min(0.9, 0.5 + (buy_count - sell_count) * 0.1)
            elif sell_count > buy_count:
                signals["overall_signal"] = "sell"
                signals["confidence"] = min(0.9, 0.5 + (sell_count - buy_count) * 0.1)

            return signals

        except Exception as e:
            self.logger.error(f"❌ [交易信号] 生成失败: {str(e)}")
            return signals

    def _analyze_trend(self, close_prices: list) -> Dict[str, Any]:
        """分析价格趋势"""
        try:
            import pandas as pd
            import numpy as np

            prices = pd.Series(close_prices)
            trend_analysis = {
                "direction": "neutral",
                "strength": 0.5,
                "duration": 0,
                "description": ""
            }

            if len(prices) < 5:
                return trend_analysis

            # 计算短期和长期趋势
            short_trend = prices.tail(5).pct_change().mean()
            long_trend = prices.pct_change().mean() if len(prices) >= 10 else short_trend

            # 判断趋势方向
            if short_trend > 0.01:  # 上涨超过1%
                trend_analysis["direction"] = "uptrend"
                trend_analysis["strength"] = min(1.0, abs(short_trend) * 10)
                trend_analysis["description"] = "价格呈上升趋势"
            elif short_trend < -0.01:  # 下跌超过1%
                trend_analysis["direction"] = "downtrend"
                trend_analysis["strength"] = min(1.0, abs(short_trend) * 10)
                trend_analysis["description"] = "价格呈下降趋势"
            else:
                trend_analysis["direction"] = "sideways"
                trend_analysis["strength"] = 0.3
                trend_analysis["description"] = "价格横盘整理"

            return trend_analysis

        except Exception as e:
            self.logger.error(f"❌ [趋势分析] 失败: {str(e)}")
            return {"direction": "neutral", "strength": 0.5, "duration": 0, "description": "趋势分析失败"}

    def _find_support_resistance(self, close_prices: list) -> Dict[str, Any]:
        """寻找支撑和阻力位"""
        try:
            import pandas as pd
            import numpy as np

            prices = pd.Series(close_prices)
            support_resistance = {
                "support_levels": [],
                "resistance_levels": [],
                "current_level": "neutral"
            }

            if len(prices) < 10:
                return support_resistance

            # 寻找局部高点和低点
            highs = []
            lows = []

            for i in range(2, len(prices) - 2):
                # 局部高点
                if (prices.iloc[i] > prices.iloc[i-1] and prices.iloc[i] > prices.iloc[i-2] and
                    prices.iloc[i] > prices.iloc[i+1] and prices.iloc[i] > prices.iloc[i+2]):
                    highs.append(float(prices.iloc[i]))

                # 局部低点
                if (prices.iloc[i] < prices.iloc[i-1] and prices.iloc[i] < prices.iloc[i-2] and
                    prices.iloc[i] < prices.iloc[i+1] and prices.iloc[i] < prices.iloc[i+2]):
                    lows.append(float(prices.iloc[i]))

            # 计算支撑和阻力位
            current_price = float(prices.iloc[-1])

            # 阻力位（高于当前价格的局部高点）
            resistance_levels = [h for h in highs if h > current_price]
            if resistance_levels:
                support_resistance["resistance_levels"] = sorted(resistance_levels)[:3]  # 取最近的3个

            # 支撑位（低于当前价格的局部低点）
            support_levels = [l for l in lows if l < current_price]
            if support_levels:
                support_resistance["support_levels"] = sorted(support_levels, reverse=True)[:3]  # 取最近的3个

            # 判断当前位置
            if support_resistance["resistance_levels"] and support_resistance["support_levels"]:
                nearest_resistance = min(support_resistance["resistance_levels"])
                nearest_support = max(support_resistance["support_levels"])

                resistance_distance = (nearest_resistance - current_price) / current_price
                support_distance = (current_price - nearest_support) / current_price

                if resistance_distance < 0.02:  # 接近阻力位
                    support_resistance["current_level"] = "near_resistance"
                elif support_distance < 0.02:  # 接近支撑位
                    support_resistance["current_level"] = "near_support"

            return support_resistance

        except Exception as e:
            self.logger.error(f"❌ [支撑阻力] 分析失败: {str(e)}")
            return {"support_levels": [], "resistance_levels": [], "current_level": "neutral"}

    def _generate_analysis_summary(self, indicators: Dict[str, Any], close_prices: list) -> str:
        """生成分析摘要"""
        try:
            summary_parts = []

            # 价格信息
            if close_prices:
                current_price = close_prices[-1]
                if len(close_prices) > 1:
                    price_change = current_price - close_prices[-2]
                    price_change_pct = (price_change / close_prices[-2]) * 100
                    summary_parts.append(f"当前价格: {current_price:.2f}, 涨跌: {price_change_pct:+.2f}%")

            # RSI分析
            rsi = indicators.get('RSI')
            if rsi is not None:
                if rsi < 30:
                    summary_parts.append(f"RSI({rsi:.1f})显示超卖状态")
                elif rsi > 70:
                    summary_parts.append(f"RSI({rsi:.1f})显示超买状态")
                else:
                    summary_parts.append(f"RSI({rsi:.1f})处于正常区间")

            # MACD分析
            macd = indicators.get('MACD')
            macd_signal = indicators.get('MACD_Signal')
            if macd is not None and macd_signal is not None:
                if macd > macd_signal:
                    summary_parts.append("MACD呈现多头排列")
                else:
                    summary_parts.append("MACD呈现空头排列")

            # 移动平均线分析
            ma5 = indicators.get('MA5')
            ma20 = indicators.get('MA20')
            if ma5 is not None and ma20 is not None:
                if ma5 > ma20:
                    summary_parts.append("短期均线上穿长期均线，趋势向好")
                else:
                    summary_parts.append("短期均线下穿长期均线，趋势偏弱")

            return "; ".join(summary_parts) if summary_parts else "技术分析完成"

        except Exception as e:
            self.logger.error(f"❌ [分析摘要] 生成失败: {str(e)}")
            return "技术分析摘要生成失败"

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
