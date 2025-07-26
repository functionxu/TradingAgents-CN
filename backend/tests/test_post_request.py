#!/usr/bin/env python3
"""
测试POST请求是否能到达处理函数
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8002"

async def test_post_request():
    """测试POST请求"""
    print("🔍 测试POST /api/stock/data 请求")
    
    payload = {
        "symbol": "000001",
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    print(f"📊 请求载荷: {json.dumps(payload, indent=2)}")
    
    async with httpx.AsyncClient(timeout=35) as client:
        try:
            print("🔄 开始发送POST请求...")
            start_time = asyncio.get_event_loop().time()
            
            response = await client.post(
                f"{BASE_URL}/api/stock/data",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Analysis-ID": "test-post-request"
                }
            )
            
            duration = asyncio.get_event_loop().time() - start_time
            
            print(f"⏱️ 请求耗时: {duration:.3f}秒")
            print(f"📊 状态码: {response.status_code}")
            print(f"📊 响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 请求成功")
                print(f"📊 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            else:
                print(f"❌ 请求失败")
                try:
                    error_data = response.json()
                    print(f"📊 错误数据: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"📊 响应文本: {response.text}")
                    
        except asyncio.TimeoutError:
            print(f"⏰ 请求超时")
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_post_request())
