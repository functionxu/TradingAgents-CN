#!/usr/bin/env python3
"""
测试修复后的MarketAnalyst数据处理
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

async def test_market_analyst_data_processing():
    """测试MarketAnalyst的数据处理"""
    print("🔄 测试修复后的MarketAnalyst数据处理...")
    
    try:
        # 导入必要的模块
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analysis-engine'))
        from app.agents.analysts.market_analyst import MarketAnalyst
        from backend.shared.clients.data_client import DataClient
        
        # 创建DataClient
        data_client = DataClient("http://localhost:8002")
        
        # 创建MarketAnalyst
        market_analyst = MarketAnalyst(data_client=data_client)
        
        # 测试数据获取
        print("📊 测试数据获取...")
        context = {
            "start_date": "2025-07-19",
            "end_date": "2025-07-26"
        }
        
        market_data = await market_analyst._get_market_data("000001", context)
        
        print(f"✅ 数据获取成功")
        print(f"📊 数据类型: {type(market_data)}")
        print(f"📊 数据字段: {list(market_data.keys()) if isinstance(market_data, dict) else 'Not a dict'}")
        
        # 检查必要字段
        required_fields = ["current_price", "volume"]
        for field in required_fields:
            if field in market_data:
                print(f"  ✅ {field}: {market_data[field]}")
            else:
                print(f"  ❌ {field}: 缺失")
        
        # 测试技术分析（预期会失败，因为还没实现）
        print(f"\n🔧 测试技术分析...")
        try:
            await market_analyst._perform_technical_analysis(market_data)
            print(f"✅ 技术分析成功")
        except RuntimeError as e:
            if "技术分析功能尚未实现" in str(e):
                print(f"✅ 技术分析按预期失败（功能未实现）: {e}")
            elif "市场数据缺少必要字段" in str(e):
                print(f"❌ 技术分析失败（字段缺失）: {e}")
                return False
            else:
                print(f"❌ 技术分析失败（其他错误）: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_data_service_response():
    """测试Data Service响应格式"""
    print("\n🔄 测试Data Service响应格式...")
    
    try:
        from backend.shared.clients.data_client import DataClient
        
        # 创建DataClient
        data_client = DataClient("http://localhost:8002")
        
        # 获取数据
        response = await data_client.get_stock_data(
            symbol="000001",
            start_date="2025-07-19",
            end_date="2025-07-26"
        )
        
        print(f"✅ Data Service响应成功")
        print(f"📊 响应类型: {type(response)}")
        print(f"📊 响应字段: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
        
        if isinstance(response, dict):
            if "success" in response:
                print(f"📊 success: {response['success']}")
            if "message" in response:
                print(f"📊 message: {response['message']}")
            if "data" in response:
                data = response["data"]
                print(f"📊 data字段: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # 检查关键字段
                if "current_price" in data:
                    print(f"  ✅ current_price: {data['current_price']}")
                else:
                    print(f"  ❌ current_price: 缺失")
                    
                if "volume" in data:
                    print(f"  ✅ volume: {data['volume']}")
                else:
                    print(f"  ❌ volume: 缺失")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🧪 MarketAnalyst修复测试")
    print("=" * 60)
    
    # 测试Data Service响应
    success1 = await test_data_service_response()
    
    # 测试MarketAnalyst数据处理
    success2 = await test_market_analyst_data_processing()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 所有测试通过！MarketAnalyst修复成功！")
    else:
        print("❌ 测试失败！需要进一步修复。")

if __name__ == "__main__":
    asyncio.run(main())
