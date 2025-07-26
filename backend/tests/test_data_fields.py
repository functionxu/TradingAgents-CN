#!/usr/bin/env python3
"""
测试Data Service返回的数据是否包含Analysis Engine需要的字段
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8002"

async def test_data_fields():
    """测试数据字段"""
    print("🔍 测试Data Service返回的数据字段")
    
    payload = {
        "symbol": "000001",
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/stock/data",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                stock_data = data["data"]
                
                print("✅ 请求成功")
                print(f"📊 股票代码: {stock_data.get('symbol')}")
                print(f"📊 数据点数量: {len(stock_data.get('close_prices', []))}")
                
                # 检查Analysis Engine需要的字段
                required_fields = ["current_price", "volume"]
                print(f"\n🔍 检查Analysis Engine需要的字段:")
                
                for field in required_fields:
                    if field in stock_data:
                        value = stock_data[field]
                        print(f"  ✅ {field}: {value} (类型: {type(value).__name__})")
                    else:
                        print(f"  ❌ {field}: 缺失")
                
                # 检查其他字段
                print(f"\n📋 所有可用字段:")
                for key, value in stock_data.items():
                    if key not in ["raw_data"]:  # 跳过原始数据
                        if isinstance(value, list):
                            print(f"  📊 {key}: 列表 (长度: {len(value)})")
                        else:
                            print(f"  📊 {key}: {value}")
                
                return True
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"📊 响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_data_fields())
    if success:
        print("\n🎉 数据字段测试通过！")
    else:
        print("\n❌ 数据字段测试失败！")
