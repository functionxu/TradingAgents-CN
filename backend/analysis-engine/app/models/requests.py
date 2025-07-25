"""
请求模型定义
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime

class MarketType(str, Enum):
    """市场类型枚举"""
    A_STOCK = "A股"
    US_STOCK = "美股"
    HK_STOCK = "港股"

class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    DASHSCOPE = "dashscope"
    DEEPSEEK = "deepseek"
    GOOGLE = "google"

class AnalysisRequest(BaseModel):
    """分析请求模型 - 匹配前端发送的格式"""

    # 基本信息
    stock_code: str = Field(..., description="股票代码")
    market_type: MarketType = Field(default=MarketType.A_STOCK, description="市场类型")
    analysis_date: datetime = Field(default_factory=datetime.now, description="分析日期")

    # 研究深度
    research_depth: int = Field(default=3, description="研究深度: 1-快速, 2-基础, 3-标准, 4-深度, 5-全面")

    # 分析师选择 (前端使用布尔值)
    market_analyst: bool = Field(default=True, description="是否启用市场分析师")
    social_analyst: bool = Field(default=False, description="是否启用社交媒体分析师")
    news_analyst: bool = Field(default=False, description="是否启用新闻分析师")
    fundamental_analyst: bool = Field(default=True, description="是否启用基本面分析师")

    # LLM配置
    llm_provider: LLMProvider = Field(default=LLMProvider.DASHSCOPE, description="LLM提供商")
    model_version: str = Field(default="qwen-plus-latest", description="LLM模型版本")

    # 分析配置
    enable_memory: bool = Field(default=True, description="是否启用记忆功能")
    debug_mode: bool = Field(default=False, description="是否启用调试模式")
    max_output_length: int = Field(default=4000, description="最大输出长度")
    include_sentiment: bool = Field(default=True, description="是否包含情绪分析")
    include_risk_assessment: bool = Field(default=True, description="是否包含风险评估")
    custom_prompt: Optional[str] = Field(default=None, description="自定义提示词")

    # 兼容性属性 - 将布尔值转换为分析师列表
    @property
    def analysts(self) -> List[str]:
        """根据布尔值生成分析师列表"""
        selected = []
        if self.market_analyst:
            selected.append("market")
        if self.fundamental_analyst:
            selected.append("fundamentals")
        if self.news_analyst:
            selected.append("news")
        if self.social_analyst:
            selected.append("social")
        return selected

    @property
    def llm_model(self) -> str:
        """LLM模型名称的别名"""
        return self.model_version
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "analysis_type": "comprehensive",
                "parameters": {
                    "enable_fundamentals": True,
                    "enable_technical": True,
                    "enable_debate": True,
                    "model_name": "deepseek-chat"
                }
            }
        }

class ToolCallRequest(BaseModel):
    """工具调用请求模型"""
    
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(..., description="工具参数")
    
    class Config:
        schema_extra = {
            "example": {
                "tool_name": "get_stock_data",
                "parameters": {
                    "symbol": "AAPL",
                    "period": "1y"
                }
            }
        }
