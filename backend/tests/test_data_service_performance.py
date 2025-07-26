#!/usr/bin/env python3
"""
Data Service 性能测试用例
测试并发性能、响应时间、吞吐量等
"""

import asyncio
import httpx
import time
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 性能测试配置
BASE_URL = "http://localhost:8002"
CONCURRENT_REQUESTS = 10  # 并发请求数
PERFORMANCE_TEST_DURATION = 30  # 性能测试持续时间（秒）

class PerformanceTester:
    """性能测试器"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
        
    async def single_request_test(self, endpoint: str, method: str = "GET", payload: Dict = None) -> Dict[str, Any]:
        """单个请求测试"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if method == "GET":
                    response = await client.get(f"{self.base_url}{endpoint}")
                elif method == "POST":
                    response = await client.post(f"{self.base_url}{endpoint}", json=payload)
                
                duration = time.time() - start_time
                
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "duration": duration,
                    "response_size": len(response.content) if response.content else 0
                }
                
        except Exception as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "status_code": 0,
                "duration": duration,
                "error": str(e),
                "response_size": 0
            }
    
    async def concurrent_test(self, endpoint: str, concurrent_count: int = CONCURRENT_REQUESTS, 
                            method: str = "GET", payload: Dict = None) -> List[Dict[str, Any]]:
        """并发测试"""
        print(f"🔄 并发测试: {concurrent_count}个并发请求到 {endpoint}")
        
        # 创建并发任务
        tasks = []
        for i in range(concurrent_count):
            task = self.single_request_test(endpoint, method, payload)
            tasks.append(task)
        
        # 执行并发请求
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - start_time
        
        # 处理结果
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            else:
                valid_results.append({
                    "success": False,
                    "status_code": 0,
                    "duration": 0,
                    "error": str(result),
                    "response_size": 0
                })
        
        # 计算统计信息
        durations = [r["duration"] for r in valid_results]
        success_count = sum(1 for r in valid_results if r["success"])
        
        stats = {
            "endpoint": endpoint,
            "concurrent_count": concurrent_count,
            "total_duration": total_duration,
            "success_count": success_count,
            "success_rate": success_count / len(valid_results) * 100,
            "avg_duration": statistics.mean(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "median_duration": statistics.median(durations) if durations else 0,
            "requests_per_second": len(valid_results) / total_duration if total_duration > 0 else 0,
            "results": valid_results
        }
        
        print(f"   ✅ 成功率: {stats['success_rate']:.1f}% ({success_count}/{len(valid_results)})")
        print(f"   ⏱️ 平均响应时间: {stats['avg_duration']:.3f}s")
        print(f"   📊 QPS: {stats['requests_per_second']:.1f}")
        
        return stats
    
    async def load_test(self, endpoint: str, duration: int = PERFORMANCE_TEST_DURATION,
                       method: str = "GET", payload: Dict = None) -> Dict[str, Any]:
        """负载测试"""
        print(f"🔥 负载测试: {duration}秒持续请求到 {endpoint}")
        
        start_time = time.time()
        end_time = start_time + duration
        request_count = 0
        success_count = 0
        durations = []
        errors = []
        
        async with httpx.AsyncClient(timeout=30) as client:
            while time.time() < end_time:
                request_start = time.time()
                
                try:
                    if method == "GET":
                        response = await client.get(f"{self.base_url}{endpoint}")
                    elif method == "POST":
                        response = await client.post(f"{self.base_url}{endpoint}", json=payload)
                    
                    request_duration = time.time() - request_start
                    durations.append(request_duration)
                    
                    if response.status_code == 200:
                        success_count += 1
                    
                    request_count += 1
                    
                except Exception as e:
                    request_duration = time.time() - request_start
                    durations.append(request_duration)
                    errors.append(str(e))
                    request_count += 1
                
                # 短暂延迟避免过度负载
                await asyncio.sleep(0.1)
        
        total_duration = time.time() - start_time
        
        stats = {
            "endpoint": endpoint,
            "test_duration": total_duration,
            "request_count": request_count,
            "success_count": success_count,
            "success_rate": success_count / request_count * 100 if request_count > 0 else 0,
            "avg_duration": statistics.mean(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "requests_per_second": request_count / total_duration if total_duration > 0 else 0,
            "errors": errors
        }
        
        print(f"   ✅ 成功率: {stats['success_rate']:.1f}% ({success_count}/{request_count})")
        print(f"   ⏱️ 平均响应时间: {stats['avg_duration']:.3f}s")
        print(f"   📊 QPS: {stats['requests_per_second']:.1f}")
        print(f"   ❌ 错误数: {len(errors)}")
        
        return stats
    
    async def stress_test(self, endpoint: str, max_concurrent: int = 50, step: int = 5,
                         method: str = "GET", payload: Dict = None) -> List[Dict[str, Any]]:
        """压力测试 - 逐步增加并发数"""
        print(f"💪 压力测试: 逐步增加并发数到 {max_concurrent}")
        
        results = []
        
        for concurrent in range(step, max_concurrent + 1, step):
            print(f"\n🔄 测试并发数: {concurrent}")
            stats = await self.concurrent_test(endpoint, concurrent, method, payload)
            results.append(stats)
            
            # 如果成功率低于80%，停止测试
            if stats["success_rate"] < 80:
                print(f"⚠️ 成功率低于80%，停止压力测试")
                break
            
            # 短暂休息
            await asyncio.sleep(2)
        
        return results
    
    def print_performance_summary(self, results: List[Dict[str, Any]]):
        """打印性能测试摘要"""
        print("\n" + "="*80)
        print("📊 Data Service 性能测试摘要")
        print("="*80)
        
        for result in results:
            print(f"\n📋 {result.get('test_type', 'Unknown')} - {result.get('endpoint', 'Unknown')}")
            print(f"   成功率: {result.get('success_rate', 0):.1f}%")
            print(f"   平均响应时间: {result.get('avg_duration', 0):.3f}s")
            print(f"   QPS: {result.get('requests_per_second', 0):.1f}")
            
            if 'concurrent_count' in result:
                print(f"   并发数: {result['concurrent_count']}")
            if 'request_count' in result:
                print(f"   总请求数: {result['request_count']}")


async def run_performance_tests():
    """运行性能测试"""
    print("🚀 开始 Data Service 性能测试")
    print("="*80)
    
    tester = PerformanceTester()
    all_results = []
    
    # 1. 健康检查并发测试
    print("\n📋 1. 健康检查并发测试")
    health_concurrent = await tester.concurrent_test("/health", 20)
    health_concurrent["test_type"] = "并发测试"
    all_results.append(health_concurrent)
    
    # 2. 股票信息并发测试
    print("\n📋 2. 股票信息并发测试")
    info_concurrent = await tester.concurrent_test("/api/stock/info/000001", 10)
    info_concurrent["test_type"] = "并发测试"
    all_results.append(info_concurrent)
    
    # 3. 股票数据并发测试
    print("\n📋 3. 股票数据并发测试")
    data_payload = {
        "symbol": "000001",
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": datetime.now().strftime("%Y-%m-%d")
    }
    data_concurrent = await tester.concurrent_test("/api/stock/data", 5, "POST", data_payload)
    data_concurrent["test_type"] = "并发测试"
    all_results.append(data_concurrent)
    
    # 4. 健康检查负载测试
    print("\n📋 4. 健康检查负载测试")
    health_load = await tester.load_test("/health", 20)
    health_load["test_type"] = "负载测试"
    all_results.append(health_load)
    
    # 5. 股票信息压力测试
    print("\n📋 5. 股票信息压力测试")
    info_stress = await tester.stress_test("/api/stock/info/000001", 30, 5)
    for i, result in enumerate(info_stress):
        result["test_type"] = f"压力测试-{i+1}"
        all_results.append(result)
    
    # 打印性能摘要
    tester.print_performance_summary(all_results)


if __name__ == "__main__":
    # 运行性能测试
    asyncio.run(run_performance_tests())
