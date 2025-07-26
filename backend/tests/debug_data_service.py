#!/usr/bin/env python3
"""
Data Service 调试测试
用于详细调试服务问题
"""

import asyncio
import httpx
import time
import traceback
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8002"

async def debug_test():
    """调试测试主要功能"""
    print("🔍 Data Service 调试测试")
    print("="*50)
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # 1. 健康检查
        print("1. 健康检查...")
        try:
            start = time.time()
            response = await client.get(f"{BASE_URL}/health")
            duration = time.time() - start
            
            print(f"   状态码: {response.status_code}")
            print(f"   响应时间: {duration:.2f}s")
            print(f"   响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   响应内容: {data}")
                print(f"   ✅ 服务健康")
            else:
                print(f"   ❌ 健康检查失败")
                
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            print(f"   异常详情: {traceback.format_exc()}")
        
        # 2. 股票信息
        print("\n2. 股票信息获取...")
        try:
            start = time.time()
            response = await client.get(f"{BASE_URL}/api/stock/info/000001")
            duration = time.time() - start
            
            print(f"   状态码: {response.status_code}")
            print(f"   响应时间: {duration:.2f}s")
            print(f"   响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   响应内容: {data}")
                if data.get("success"):
                    stock_info = data.get("data", {})
                    print(f"   ✅ 获取成功: {stock_info.get('name', 'Unknown')}")
                else:
                    print(f"   ❌ API失败: {data.get('message')}")
            else:
                print(f"   ❌ HTTP错误")
                try:
                    error_data = response.json()
                    print(f"   错误详情: {error_data}")
                except:
                    print(f"   响应文本: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            print(f"   异常详情: {traceback.format_exc()}")
        
        # 3. 股票数据
        print("\n3. 股票历史数据...")
        try:
            start = time.time()
            payload = {
                "symbol": "000001",
                "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d")
            }
            print(f"   请求载荷: {payload}")
            
            response = await client.post(
                f"{BASE_URL}/api/stock/data",
                json=payload,
                headers={"X-Analysis-ID": "debug-test-001"}
            )
            duration = time.time() - start
            
            print(f"   状态码: {response.status_code}")
            print(f"   响应时间: {duration:.2f}s")
            print(f"   响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   响应内容: {data}")
                if data.get("success"):
                    stock_data = data.get("data", {})
                    count = len(stock_data.get("close_prices", []))
                    print(f"   ✅ 获取成功: {count}个数据点")
                else:
                    print(f"   ❌ API失败: {data.get('message')}")
            else:
                print(f"   ❌ HTTP错误")
                try:
                    error_data = response.json()
                    print(f"   错误详情: {error_data}")
                except:
                    print(f"   响应文本: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            print(f"   异常详情: {traceback.format_exc()}")
        
        # 4. 股票新闻
        print("\n4. 股票新闻获取...")
        try:
            start = time.time()
            response = await client.get(f"{BASE_URL}/api/stock/news/000001")
            duration = time.time() - start
            
            print(f"   状态码: {response.status_code}")
            print(f"   响应时间: {duration:.2f}s")
            print(f"   响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   响应内容: {data}")
                if data.get("success"):
                    news_data = data.get("data", [])
                    print(f"   ✅ 新闻获取成功: {len(news_data)}条新闻")
                else:
                    print(f"   ❌ API失败: {data.get('message')}")
            else:
                print(f"   ❌ HTTP错误")
                try:
                    error_data = response.json()
                    print(f"   错误详情: {error_data}")
                except:
                    print(f"   响应文本: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            print(f"   异常详情: {traceback.format_exc()}")
        
        # 5. 分析ID追踪
        print("\n5. 分析ID追踪...")
        try:
            start = time.time()
            analysis_id = f"debug-test-{int(time.time())}"
            response = await client.get(
                f"{BASE_URL}/api/stock/info/000001",
                headers={"X-Analysis-ID": analysis_id}
            )
            duration = time.time() - start
            
            print(f"   分析ID: {analysis_id}")
            print(f"   状态码: {response.status_code}")
            print(f"   响应时间: {duration:.2f}s")
            print(f"   响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   响应内容: {data}")
                print(f"   ✅ 分析ID传递成功")
            else:
                print(f"   ❌ HTTP错误")
                try:
                    error_data = response.json()
                    print(f"   错误详情: {error_data}")
                except:
                    print(f"   响应文本: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            print(f"   异常详情: {traceback.format_exc()}")
        
        # 6. 测试其他端点
        print("\n6. 其他端点测试...")
        
        endpoints = [
            ("GET", "/api/data-sources/status", "数据源状态"),
            ("GET", "/api/data-sources/stats", "数据源统计"),
            ("GET", "/api/local-data/summary", "本地数据摘要"),
            ("GET", "/api/admin/statistics", "管理统计"),
        ]
        
        for method, endpoint, name in endpoints:
            try:
                print(f"\n   测试 {name} ({method} {endpoint})...")
                start = time.time()
                
                if method == "GET":
                    response = await client.get(f"{BASE_URL}{endpoint}")
                elif method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}", json={})
                
                duration = time.time() - start
                
                print(f"      状态码: {response.status_code}")
                print(f"      响应时间: {duration:.2f}s")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"      ✅ 成功: {name}")
                    print(f"      响应摘要: {str(data)[:100]}...")
                else:
                    print(f"      ❌ 失败: {name}")
                    try:
                        error_data = response.json()
                        print(f"      错误: {error_data.get('detail', '无详情')}")
                    except:
                        print(f"      响应文本: {response.text[:100]}...")
                        
            except Exception as e:
                print(f"      ❌ 异常: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_test())
