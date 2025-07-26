#!/usr/bin/env python3
"""
Data Service 快速测试
用于快速验证服务基本功能
"""

import asyncio
import httpx
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8002"

async def quick_test():
    """快速测试主要功能"""
    print("🚀 Data Service 快速测试")
    print("="*50)
    
    async with httpx.AsyncClient(timeout=30) as client:
        tests = []
        
        # 1. 健康检查
        print("1. 健康检查...")
        try:
            start = time.time()
            response = await client.get(f"{BASE_URL}/health")
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 服务健康 - {data.get('status')} ({duration:.2f}s)")
                tests.append(True)
            else:
                print(f"   ❌ 健康检查失败 - HTTP {response.status_code}")
                tests.append(False)
        except Exception as e:
            print(f"   ❌ 连接失败 - {str(e)}")
            tests.append(False)
        
        # 2. 股票信息
        print("2. 股票信息获取...")
        try:
            start = time.time()
            response = await client.get(f"{BASE_URL}/api/stock/info/000001")
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    stock_info = data.get("data", {})
                    print(f"   ✅ 获取成功 - {stock_info.get('name', 'Unknown')} ({duration:.2f}s)")
                    tests.append(True)
                else:
                    print(f"   ❌ API失败 - {data.get('message')}")
                    tests.append(False)
            else:
                print(f"   ❌ HTTP错误 - {response.status_code}")
                tests.append(False)
        except Exception as e:
            print(f"   ❌ 请求失败 - {str(e)}")
            tests.append(False)
        
        # 3. 股票数据
        print("3. 股票历史数据...")
        try:
            start = time.time()
            payload = {
                "symbol": "000001",
                "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d")
            }
            response = await client.post(
                f"{BASE_URL}/api/stock/data",
                json=payload,
                headers={"X-Analysis-ID": "quick-test-001"}
            )
            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    stock_data = data.get("data", {})
                    count = len(stock_data.get("close_prices", []))
                    print(f"   ✅ 获取成功 - {count}个数据点 ({duration:.2f}s)")
                    tests.append(True)
                else:
                    print(f"   ❌ API失败 - {data.get('message')}")
                    tests.append(False)
            elif response.status_code == 408:
                print(f"   ⏰ 请求超时 ({duration:.2f}s)")
                tests.append(False)
            elif response.status_code == 500:
                # 获取详细错误信息
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "未知错误")
                    print(f"   ❌ 服务器错误 - {error_detail}")
                except:
                    print(f"   ❌ 服务器错误 - HTTP 500")
                tests.append(False)
            else:
                print(f"   ❌ HTTP错误 - {response.status_code}")
                # 尝试获取错误详情
                try:
                    error_data = response.json()
                    print(f"      详情: {error_data.get('detail', '无详情')}")
                except:
                    pass
                tests.append(False)
        except Exception as e:
            print(f"   ❌ 请求失败 - {str(e)}")
            tests.append(False)
        
        # 4. 股票新闻获取
        print("4. 股票新闻获取...")
        try:
            start = time.time()
            response = await client.get(f"{BASE_URL}/api/stock/news/000001")
            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    news_data = data.get("data", [])
                    print(f"   ✅ 新闻获取成功 - 找到{len(news_data)}条新闻 ({duration:.2f}s)")
                    tests.append(True)
                else:
                    print(f"   ❌ API失败 - {data.get('message')}")
                    tests.append(False)
            else:
                print(f"   ❌ HTTP错误 - {response.status_code}")
                tests.append(False)
        except Exception as e:
            print(f"   ❌ 请求失败 - {str(e)}")
            tests.append(False)
        
        # 5. 分析ID追踪
        print("5. 分析ID追踪...")
        try:
            start = time.time()
            analysis_id = f"quick-test-{int(time.time())}"
            response = await client.get(
                f"{BASE_URL}/api/stock/info/000001",
                headers={"X-Analysis-ID": analysis_id}
            )
            duration = time.time() - start
            
            if response.status_code == 200:
                print(f"   ✅ 分析ID传递成功 - {analysis_id} ({duration:.2f}s)")
                tests.append(True)
            else:
                print(f"   ❌ HTTP错误 - {response.status_code}")
                tests.append(False)
        except Exception as e:
            print(f"   ❌ 请求失败 - {str(e)}")
            tests.append(False)
        
        # 测试摘要
        print("\n" + "="*50)
        passed = sum(tests)
        total = len(tests)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📊 快速测试结果:")
        print(f"   通过: {passed}/{total}")
        print(f"   成功率: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 所有测试通过！Data Service 运行正常！")
        elif success_rate >= 80:
            print("⚠️ 大部分功能正常，但有一些问题")
        else:
            print("❌ 多个功能异常，请检查服务状态")
        
        return success_rate >= 80

if __name__ == "__main__":
    asyncio.run(quick_test())
