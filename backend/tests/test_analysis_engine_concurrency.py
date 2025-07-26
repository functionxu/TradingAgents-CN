#!/usr/bin/env python3
"""
Analysis Engine 并发测试
测试多个股票分析任务同时执行的情况
"""

import asyncio
import httpx
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

BASE_URL = "http://localhost:8001"  # Analysis Engine URL

class ConcurrencyTester:
    """并发测试器"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        
    async def test_single_analysis(self, stock_code: str, test_id: str) -> Dict[str, Any]:
        """测试单个分析任务"""
        async with httpx.AsyncClient(timeout=300) as client:
            try:
                # 1. 启动分析
                start_time = time.time()
                print(f"🚀 [{test_id}] 启动分析: {stock_code}")
                
                analysis_request = {
                    "stock_code": stock_code,
                    "analysis_date": datetime.now().isoformat(),
                    "market_analyst": True,
                    "fundamental_analyst": True,
                    "news_analyst": False,
                    "social_analyst": False,
                    "research_depth": 3,  # 数字而不是字符串
                    "llm_provider": "dashscope",
                    "model_version": "qwen-plus-latest",  # 修正字段名
                    "market_type": "A股"  # 使用正确的枚举值
                }
                
                response = await client.post(
                    f"{BASE_URL}/api/analysis/start",
                    json=analysis_request
                )
                
                if response.status_code != 200:
                    return {
                        "test_id": test_id,
                        "stock_code": stock_code,
                        "success": False,
                        "error": f"启动失败: {response.status_code}",
                        "duration": time.time() - start_time
                    }
                
                result = response.json()
                analysis_id = result["data"]["analysis_id"]
                print(f"✅ [{test_id}] 分析已启动: {analysis_id}")
                
                # 2. 轮询进度直到完成
                max_wait = 300  # 5分钟超时
                poll_interval = 5  # 5秒轮询一次
                waited = 0
                
                while waited < max_wait:
                    await asyncio.sleep(poll_interval)
                    waited += poll_interval
                    
                    # 获取进度
                    progress_response = await client.get(
                        f"{BASE_URL}/api/analysis/{analysis_id}/progress"
                    )
                    
                    if progress_response.status_code == 200:
                        progress_data = progress_response.json()
                        progress_info = progress_data["data"]
                        status = progress_info["status"]
                        percentage = progress_info["progress_percentage"]
                        
                        print(f"📊 [{test_id}] 进度: {percentage}% - {status}")
                        
                        if status in ["completed", "failed"]:
                            break
                    else:
                        print(f"⚠️ [{test_id}] 获取进度失败: {progress_response.status_code}")
                
                # 3. 获取最终结果
                final_response = await client.get(
                    f"{BASE_URL}/api/analysis/{analysis_id}/result"
                )
                
                duration = time.time() - start_time
                
                if final_response.status_code == 200:
                    final_result = final_response.json()
                    return {
                        "test_id": test_id,
                        "stock_code": stock_code,
                        "analysis_id": analysis_id,
                        "success": True,
                        "duration": duration,
                        "final_status": final_result["data"]["status"] if final_result["success"] else "unknown"
                    }
                else:
                    return {
                        "test_id": test_id,
                        "stock_code": stock_code,
                        "analysis_id": analysis_id,
                        "success": False,
                        "error": f"获取结果失败: {final_response.status_code}",
                        "duration": duration
                    }
                    
            except Exception as e:
                return {
                    "test_id": test_id,
                    "stock_code": stock_code,
                    "success": False,
                    "error": str(e),
                    "duration": time.time() - start_time
                }
    
    async def test_concurrent_analysis(self, stock_codes: List[str]) -> Dict[str, Any]:
        """测试并发分析"""
        print(f"🔄 开始并发测试: {len(stock_codes)} 个股票")
        print(f"📋 股票列表: {stock_codes}")
        
        self.start_time = time.time()
        
        # 创建并发任务
        tasks = []
        for i, stock_code in enumerate(stock_codes):
            test_id = f"test-{i+1:02d}"
            task = self.test_single_analysis(stock_code, test_id)
            tasks.append(task)
        
        # 并发执行所有任务
        print(f"⚡ 启动 {len(tasks)} 个并发任务...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_duration = time.time() - self.start_time
        
        # 统计结果
        successful = 0
        failed = 0
        errors = []
        durations = []
        
        for result in results:
            if isinstance(result, Exception):
                failed += 1
                errors.append(str(result))
            elif result.get("success", False):
                successful += 1
                durations.append(result["duration"])
            else:
                failed += 1
                errors.append(result.get("error", "Unknown error"))
        
        # 计算统计信息
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        
        return {
            "total_tasks": len(stock_codes),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(stock_codes) * 100,
            "total_duration": total_duration,
            "avg_task_duration": avg_duration,
            "max_task_duration": max_duration,
            "min_task_duration": min_duration,
            "errors": errors,
            "detailed_results": [r for r in results if not isinstance(r, Exception)]
        }

async def main():
    """主测试函数"""
    print("🧪 Analysis Engine 并发测试")
    print("=" * 50)
    
    # 测试股票列表
    test_stocks = [
        "000001",  # 平安银行
        "000002",  # 万科A
        "600036",  # 招商银行
        "600519",  # 贵州茅台
        "000858"   # 五粮液
    ]
    
    tester = ConcurrencyTester()
    
    # 1. 健康检查
    print("🔍 检查Analysis Engine健康状态...")
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            health_response = await client.get(f"{BASE_URL}/health")
            if health_response.status_code == 200:
                print("✅ Analysis Engine 健康状态正常")
            else:
                print(f"❌ Analysis Engine 健康检查失败: {health_response.status_code}")
                return
        except Exception as e:
            print(f"❌ 无法连接到Analysis Engine: {e}")
            return
    
    # 2. 并发测试
    print(f"\n🚀 开始并发分析测试...")
    result = await tester.test_concurrent_analysis(test_stocks)
    
    # 3. 输出结果
    print("\n📊 并发测试结果:")
    print("=" * 50)
    print(f"总任务数: {result['total_tasks']}")
    print(f"成功任务: {result['successful']}")
    print(f"失败任务: {result['failed']}")
    print(f"成功率: {result['success_rate']:.1f}%")
    print(f"总耗时: {result['total_duration']:.1f}秒")
    print(f"平均任务耗时: {result['avg_task_duration']:.1f}秒")
    print(f"最长任务耗时: {result['max_task_duration']:.1f}秒")
    print(f"最短任务耗时: {result['min_task_duration']:.1f}秒")
    
    if result['errors']:
        print(f"\n❌ 错误信息:")
        for i, error in enumerate(result['errors'], 1):
            print(f"  {i}. {error}")
    
    # 4. 详细结果
    print(f"\n📋 详细结果:")
    for detail in result['detailed_results']:
        status = "✅" if detail['success'] else "❌"
        print(f"  {status} {detail['test_id']}: {detail['stock_code']} - {detail['duration']:.1f}s")
    
    # 5. 并发性能评估
    print(f"\n🎯 并发性能评估:")
    if result['successful'] > 0:
        theoretical_sequential_time = result['avg_task_duration'] * result['total_tasks']
        speedup = theoretical_sequential_time / result['total_duration']
        print(f"理论顺序执行时间: {theoretical_sequential_time:.1f}秒")
        print(f"实际并发执行时间: {result['total_duration']:.1f}秒")
        print(f"并发加速比: {speedup:.2f}x")
        
        if speedup > 1.5:
            print("✅ 并发性能良好")
        elif speedup > 1.0:
            print("⚠️ 并发性能一般")
        else:
            print("❌ 并发性能较差，可能存在阻塞")
    else:
        print("❌ 无法评估并发性能（所有任务都失败了）")

if __name__ == "__main__":
    asyncio.run(main())
