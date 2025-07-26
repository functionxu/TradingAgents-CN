#!/usr/bin/env python3
"""
清除缓存并测试新的数据字段
"""

import asyncio
import httpx
import redis
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8002"

async def clear_cache_and_test():
    """清除缓存并测试"""
    print("🧹 清除Redis缓存并测试新字段")
    
    # 1. 连接Redis并清除相关缓存
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # 查找股票数据相关的缓存键
        cache_keys = r.keys("stock_data:000001:*")
        if cache_keys:
            print(f"🔍 找到 {len(cache_keys)} 个缓存键")
            for key in cache_keys:
                r.delete(key)
                print(f"🗑️ 删除缓存键: {key}")
        else:
            print("🔍 没有找到相关缓存键")
            
    except Exception as e:
        print(f"⚠️ Redis操作失败: {e}")
    
    # 2. 发送请求获取新数据
    payload = {
        "symbol": "000001",
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    print(f"\n📡 发送POST请求获取新数据...")
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/stock/data",
                json=payload,
                headers={"X-Analysis-ID": "cache-clear-test"}
            )
            
            if response.status_code == 200:
                data = response.json()
                stock_data = data["data"]
                
                print("✅ 请求成功")
                print(f"📊 股票代码: {stock_data.get('symbol')}")
                
                # 检查Analysis Engine需要的字段
                required_fields = ["current_price", "volume"]
                print(f"\n🔍 检查Analysis Engine需要的字段:")
                
                all_present = True
                for field in required_fields:
                    if field in stock_data:
                        value = stock_data[field]
                        print(f"  ✅ {field}: {value} (类型: {type(value).__name__})")
                    else:
                        print(f"  ❌ {field}: 缺失")
                        all_present = False
                
                if all_present:
                    print(f"\n🎉 所有必要字段都存在！")
                    
                    # 验证字段值的合理性
                    current_price = stock_data.get("current_price", 0)
                    volume = stock_data.get("volume", 0)
                    
                    if current_price > 0:
                        print(f"✅ current_price 值合理: {current_price}")
                    else:
                        print(f"⚠️ current_price 值异常: {current_price}")
                        
                    if volume > 0:
                        print(f"✅ volume 值合理: {volume}")
                    else:
                        print(f"⚠️ volume 值异常: {volume}")
                        
                else:
                    print(f"\n❌ 仍然缺少必要字段，可能需要重启Data Service")
                
                # 显示完整的数据结构
                print(f"\n📋 完整数据结构:")
                for key, value in stock_data.items():
                    if key == "raw_data":
                        print(f"  📊 {key}: [原始数据，长度: {len(str(value))}]")
                    elif isinstance(value, list):
                        print(f"  📊 {key}: 列表 (长度: {len(value)})")
                        if value:  # 如果列表不为空，显示第一个和最后一个元素
                            print(f"      首个: {value[0]}, 最后: {value[-1]}")
                    else:
                        print(f"  📊 {key}: {value}")
                
                return all_present
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"📊 响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            return False

if __name__ == "__main__":
    success = asyncio.run(clear_cache_and_test())
    if success:
        print("\n🎉 缓存清除和字段测试成功！")
    else:
        print("\n❌ 测试失败，可能需要重启Data Service！")
