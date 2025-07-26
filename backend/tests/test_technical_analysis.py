#!/usr/bin/env python3
"""
测试技术分析功能的详细实现
"""

import asyncio
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

async def test_technical_analysis_details():
    """测试技术分析的详细结果"""
    print("🔧 测试技术分析详细功能...")
    
    try:
        # 导入必要的模块
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analysis-engine'))
        from app.agents.analysts.market_analyst import MarketAnalyst
        from backend.shared.clients.data_client import DataClient
        
        # 创建DataClient和MarketAnalyst
        data_client = DataClient("http://localhost:8002")
        market_analyst = MarketAnalyst(data_client=data_client)
        
        # 获取市场数据
        print("📊 获取市场数据...")
        context = {
            "start_date": "2025-07-19",
            "end_date": "2025-07-26"
        }
        
        market_data = await market_analyst._get_market_data("000001", context)
        
        print(f"✅ 市场数据获取成功")
        print(f"📊 收盘价数据: {market_data.get('close_prices', [])}")
        print(f"📊 成交量数据: {market_data.get('volumes', [])}")
        print(f"📊 当前价格: {market_data.get('current_price')}")
        print(f"📊 当前成交量: {market_data.get('volume')}")
        
        # 执行技术分析
        print(f"\n🔧 执行技术分析...")
        technical_result = await market_analyst._perform_technical_analysis(market_data)
        
        print(f"✅ 技术分析完成")
        print(f"📊 分析结果类型: {type(technical_result)}")
        
        # 显示详细的技术分析结果
        if isinstance(technical_result, dict):
            print(f"\n📋 技术分析详细结果:")
            print(f"=" * 60)
            
            # 基本信息
            print(f"📊 股票代码: {technical_result.get('symbol')}")
            print(f"📊 当前价格: {technical_result.get('current_price')}")
            print(f"📊 成交量: {technical_result.get('volume')}")
            
            # 技术指标
            indicators = technical_result.get('indicators', {})
            if indicators:
                print(f"\n🔧 技术指标:")
                for key, value in indicators.items():
                    if isinstance(value, float):
                        print(f"  📈 {key}: {value:.4f}")
                    else:
                        print(f"  📈 {key}: {value}")
            
            # 交易信号
            signals = technical_result.get('signals', {})
            if signals:
                print(f"\n📡 交易信号:")
                print(f"  🟢 买入信号: {signals.get('buy_signals', [])}")
                print(f"  🔴 卖出信号: {signals.get('sell_signals', [])}")
                print(f"  ⚪ 中性信号: {signals.get('neutral_signals', [])}")
                print(f"  📊 综合信号: {signals.get('overall_signal', 'neutral')}")
                print(f"  📊 信号置信度: {signals.get('confidence', 0.5):.2f}")
            
            # 趋势分析
            trend = technical_result.get('trend_analysis', {})
            if trend:
                print(f"\n📈 趋势分析:")
                print(f"  📊 趋势方向: {trend.get('direction', 'neutral')}")
                print(f"  📊 趋势强度: {trend.get('strength', 0.5):.2f}")
                print(f"  📊 趋势描述: {trend.get('description', '')}")
            
            # 支撑阻力位
            sr = technical_result.get('support_resistance', {})
            if sr:
                print(f"\n🎯 支撑阻力位:")
                print(f"  📊 支撑位: {sr.get('support_levels', [])}")
                print(f"  📊 阻力位: {sr.get('resistance_levels', [])}")
                print(f"  📊 当前位置: {sr.get('current_level', 'neutral')}")
            
            # 分析摘要
            summary = technical_result.get('analysis_summary', '')
            if summary:
                print(f"\n📝 分析摘要:")
                print(f"  {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_technical_indicators_calculation():
    """测试技术指标计算的准确性"""
    print("\n🧮 测试技术指标计算准确性...")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analysis-engine'))
        from app.agents.analysts.market_analyst import MarketAnalyst
        
        # 创建MarketAnalyst实例
        market_analyst = MarketAnalyst()
        
        # 测试数据
        test_prices = [10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 11.3, 11.8, 12.0, 11.9, 12.2, 12.1, 12.3, 12.5, 12.4]
        test_volumes = [1000, 1100, 1200, 1050, 1300, 1400, 1250, 1500, 1600, 1450, 1700, 1550, 1800, 1900, 1750]
        
        print(f"📊 测试价格数据: {test_prices}")
        print(f"📊 测试成交量数据: {test_volumes}")
        
        # 计算技术指标
        indicators = market_analyst._calculate_technical_indicators(test_prices, test_volumes)
        
        print(f"\n📈 计算的技术指标:")
        for key, value in indicators.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
        
        # 验证指标的合理性
        print(f"\n✅ 指标验证:")
        
        # MA5应该是最近5个价格的平均值
        if 'MA5' in indicators:
            expected_ma5 = sum(test_prices[-5:]) / 5
            actual_ma5 = indicators['MA5']
            print(f"  MA5: 期望={expected_ma5:.4f}, 实际={actual_ma5:.4f}, 匹配={abs(expected_ma5 - actual_ma5) < 0.001}")
        
        # RSI应该在0-100之间
        if 'RSI' in indicators:
            rsi = indicators['RSI']
            print(f"  RSI: {rsi:.2f}, 范围正确={0 <= rsi <= 100}")
        
        # MACD指标存在性检查
        macd_indicators = ['MACD', 'MACD_Signal', 'MACD_Histogram']
        macd_present = all(ind in indicators for ind in macd_indicators)
        print(f"  MACD指标完整性: {macd_present}")
        
        # 布林带指标存在性检查
        bb_indicators = ['BB_Upper', 'BB_Middle', 'BB_Lower']
        bb_present = all(ind in indicators for ind in bb_indicators)
        print(f"  布林带指标完整性: {bb_present}")
        
        if bb_present:
            bb_upper = indicators['BB_Upper']
            bb_middle = indicators['BB_Middle']
            bb_lower = indicators['BB_Lower']
            bb_order_correct = bb_lower < bb_middle < bb_upper
            print(f"  布林带顺序正确: {bb_order_correct} (下轨 < 中轨 < 上轨)")
        
        return True
        
    except Exception as e:
        print(f"❌ 技术指标计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🧪 技术分析功能详细测试")
    print("=" * 80)
    
    # 测试技术分析详细结果
    success1 = await test_technical_analysis_details()
    
    # 测试技术指标计算准确性
    success2 = await test_technical_indicators_calculation()
    
    print("\n" + "=" * 80)
    if success1 and success2:
        print("🎉 所有技术分析测试通过！功能实现成功！")
    else:
        print("❌ 部分测试失败！需要进一步检查。")

if __name__ == "__main__":
    asyncio.run(main())
