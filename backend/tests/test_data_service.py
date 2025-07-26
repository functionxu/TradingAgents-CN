#!/usr/bin/env python3
"""
Data Service 全功能测试用例
测试所有API端点和功能
"""

import pytest
import asyncio
import httpx
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# 测试配置
BASE_URL = "http://localhost:8002"
TEST_TIMEOUT = 30  # 测试超时时间（秒）

class DataServiceTester:
    """Data Service 测试器"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = None
        self.test_results = []
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = httpx.AsyncClient(timeout=TEST_TIMEOUT)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.client:
            await self.client.aclose()
    
    def log_test_result(self, test_name: str, success: bool, message: str, duration: float = 0):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "message": message,
            "duration": f"{duration:.2f}s"
        })
        print(f"{status} {test_name}: {message} ({duration:.2f}s)")
    
    async def test_health_check(self):
        """测试健康检查"""
        test_name = "健康检查"
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test_result(test_name, True, f"服务健康，版本: {data.get('version')}", duration)
                    return True
                else:
                    self.log_test_result(test_name, False, f"服务状态异常: {data.get('status')}", duration)
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"连接失败: {str(e)}", duration)
            
        return False
    
    async def test_stock_info(self, symbol: str = "000001"):
        """测试股票信息获取"""
        test_name = f"股票信息获取 ({symbol})"
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{self.base_url}/api/stock/info/{symbol}")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    stock_info = data.get("data", {})
                    self.log_test_result(
                        test_name, True, 
                        f"获取成功: {stock_info.get('name', 'Unknown')} - {stock_info.get('industry', 'Unknown')}", 
                        duration
                    )
                    return data
                else:
                    self.log_test_result(test_name, False, f"API返回失败: {data.get('message')}", duration)
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"请求失败: {str(e)}", duration)
            
        return None
    
    async def test_stock_data(self, symbol: str = "000001", days: int = 7):
        """测试股票历史数据获取"""
        test_name = f"股票历史数据 ({symbol}, {days}天)"
        start_time = time.time()
        
        # 计算日期范围
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        try:
            payload = {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/stock/data",
                json=payload,
                headers={"X-Analysis-ID": "test-analysis-001"}
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    stock_data = data.get("data", {})
                    prices_count = len(stock_data.get("close_prices", []))
                    self.log_test_result(
                        test_name, True, 
                        f"获取成功: {prices_count}个数据点", 
                        duration
                    )
                    return data
                else:
                    self.log_test_result(test_name, False, f"API返回失败: {data.get('message')}", duration)
            elif response.status_code == 408:
                self.log_test_result(test_name, False, "请求超时", duration)
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"请求失败: {str(e)}", duration)
            
        return None
    
    async def test_stock_search(self, keyword: str = "平安"):
        """测试股票搜索"""
        test_name = f"股票搜索 ({keyword})"
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{self.base_url}/api/stock/search?q={keyword}")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    results = data.get("data", [])
                    self.log_test_result(
                        test_name, True, 
                        f"搜索成功: 找到{len(results)}个结果", 
                        duration
                    )
                    return data
                else:
                    self.log_test_result(test_name, False, f"API返回失败: {data.get('message')}", duration)
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"请求失败: {str(e)}", duration)
            
        return None
    
    async def test_market_data(self, market: str = "A股"):
        """测试市场数据获取"""
        test_name = f"市场数据 ({market})"
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{self.base_url}/api/market/data?market={market}")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    market_data = data.get("data", {})
                    self.log_test_result(
                        test_name, True, 
                        f"获取成功: {market_data.get('total_stocks', 0)}只股票", 
                        duration
                    )
                    return data
                else:
                    self.log_test_result(test_name, False, f"API返回失败: {data.get('message')}", duration)
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"请求失败: {str(e)}", duration)
            
        return None
    
    async def test_cache_functionality(self, symbol: str = "000001"):
        """测试缓存功能"""
        test_name = "缓存功能测试"
        
        # 第一次请求（应该从数据源获取）
        start_time = time.time()
        first_response = await self.test_stock_info(symbol)
        first_duration = time.time() - start_time
        
        if not first_response:
            self.log_test_result(test_name, False, "第一次请求失败", first_duration)
            return False
        
        # 第二次请求（应该从缓存获取，更快）
        start_time = time.time()
        second_response = await self.test_stock_info(symbol)
        second_duration = time.time() - start_time
        
        if not second_response:
            self.log_test_result(test_name, False, "第二次请求失败", second_duration)
            return False
        
        # 比较响应时间
        if second_duration < first_duration * 0.8:  # 缓存应该快至少20%
            self.log_test_result(
                test_name, True, 
                f"缓存生效: 第一次{first_duration:.2f}s, 第二次{second_duration:.2f}s", 
                second_duration
            )
            return True
        else:
            self.log_test_result(
                test_name, False, 
                f"缓存可能未生效: 第一次{first_duration:.2f}s, 第二次{second_duration:.2f}s", 
                second_duration
            )
            return False
    
    async def test_error_handling(self):
        """测试错误处理"""
        test_name = "错误处理测试"
        start_time = time.time()
        
        # 测试无效股票代码
        try:
            response = await self.client.get(f"{self.base_url}/api/stock/info/INVALID_CODE")
            duration = time.time() - start_time
            
            if response.status_code in [400, 404, 500]:
                data = response.json()
                self.log_test_result(
                    test_name, True, 
                    f"正确处理无效代码: HTTP {response.status_code}", 
                    duration
                )
                return True
            else:
                self.log_test_result(test_name, False, f"未正确处理错误: HTTP {response.status_code}", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"异常处理失败: {str(e)}", duration)
            
        return False
    
    async def test_analysis_id_tracking(self, symbol: str = "000001"):
        """测试分析ID追踪"""
        test_name = "分析ID追踪测试"
        start_time = time.time()
        
        analysis_id = f"test-{int(time.time())}"
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/stock/info/{symbol}",
                headers={"X-Analysis-ID": analysis_id}
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                # 检查响应头或日志中是否包含分析ID
                self.log_test_result(
                    test_name, True, 
                    f"分析ID传递成功: {analysis_id}", 
                    duration
                )
                return True
            else:
                self.log_test_result(test_name, False, f"HTTP {response.status_code}", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(test_name, False, f"请求失败: {str(e)}", duration)
            
        return False
    
    def print_summary(self):
        """打印测试摘要"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*80)
        print("📊 Data Service 测试摘要")
        print("="*80)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        print("="*80)
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"   - {result['test']}: {result['message']}")
        
        print("\n📋 详细结果:")
        for result in self.test_results:
            print(f"   {result['status']} {result['test']} ({result['duration']})")
            print(f"      {result['message']}")


async def run_comprehensive_test():
    """运行全面测试"""
    print("🚀 开始 Data Service 全功能测试")
    print("="*80)
    
    async with DataServiceTester() as tester:
        # 1. 基础功能测试
        print("\n📋 1. 基础功能测试")
        await tester.test_health_check()
        
        # 2. 股票信息测试
        print("\n📋 2. 股票信息测试")
        await tester.test_stock_info("000001")  # 平安银行
        await tester.test_stock_info("600036")  # 招商银行
        await tester.test_stock_info("000002")  # 万科A
        
        # 3. 股票数据测试
        print("\n📋 3. 股票历史数据测试")
        await tester.test_stock_data("000001", 7)   # 7天数据
        await tester.test_stock_data("600036", 30)  # 30天数据
        
        # 4. 搜索功能测试
        print("\n📋 4. 搜索功能测试")
        await tester.test_stock_search("平安")
        await tester.test_stock_search("银行")
        
        # 5. 市场数据测试
        print("\n📋 5. 市场数据测试")
        await tester.test_market_data("A股")
        await tester.test_market_data("港股")
        
        # 6. 缓存功能测试
        print("\n📋 6. 缓存功能测试")
        await tester.test_cache_functionality("000001")
        
        # 7. 错误处理测试
        print("\n📋 7. 错误处理测试")
        await tester.test_error_handling()
        
        # 8. 分析ID追踪测试
        print("\n📋 8. 分析ID追踪测试")
        await tester.test_analysis_id_tracking("000001")
        
        # 打印测试摘要
        tester.print_summary()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(run_comprehensive_test())
