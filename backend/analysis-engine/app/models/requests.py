"""
请求模型定义
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class AnalysisRequest(BaseModel):
    """分析请求模型"""

    stock_code: str = Field(..., description="股票代码")
    analysis_type: str = Field(
        default="comprehensive",
        description="分析类型: fundamentals, technical, comprehensive, debate"
    )

    # 分析师配置
    analysts: Optional[List[str]] = Field(
        default=["market", "fundamentals", "news", "social"],
        description="选择的分析师列表: market, fundamentals, news, social"
    )

    # 研究深度配置
    research_depth: Optional[int] = Field(
        default=3,
        description="研究深度: 1-快速, 2-基础, 3-标准, 4-深度, 5-全面"
    )

    # LLM配置
    llm_provider: Optional[str] = Field(
        default="dashscope",
        description="LLM提供商: dashscope, deepseek, google"
    )

    llm_model: Optional[str] = Field(
        default="qwen-plus-latest",
        description="LLM模型名称"
    )

    # 市场类型
    market_type: Optional[str] = Field(
        default="A股",
        description="市场类型: A股, 美股, 港股"
    )

    # 分析日期
    analysis_date: Optional[str] = Field(
        default=None,
        description="分析日期，格式: YYYY-MM-DD"
    )

    # 其他参数
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="其他分析参数"
    )
    
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
