#!/usr/bin/env python3
"""
快速测试修复后的分析流程
"""

import asyncio
import time
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

async def test_quick_analysis():
    """测试快速分析流程"""
    print("🚀 测试修复后的快速分析流程")
    print("=" * 60)
    
    # 创建快速分析配置
    config = DEFAULT_CONFIG.copy()
    config.update({
        "llm_provider": "dashscope",
        "deep_think_llm": "qwen-plus",
        "quick_think_llm": "qwen-turbo",
        "max_debate_rounds": 1,        # 最小轮次
        "max_risk_discuss_rounds": 1,  # 最小轮次
        "memory_enabled": True,        # 启用内存服务测试
        "online_tools": True
    })
    
    print(f"📊 配置参数:")
    print(f"  - max_debate_rounds: {config['max_debate_rounds']}")
    print(f"  - max_risk_discuss_rounds: {config['max_risk_discuss_rounds']}")
    print(f"  - memory_enabled: {config['memory_enabled']}")
    
    try:
        # 创建TradingAgentsGraph
        print(f"\n🔧 初始化TradingAgentsGraph...")
        start_time = time.time()
        
        ta = TradingAgentsGraph(
            selected_analysts=["market"],  # 只使用市场分析师加速测试
            debug=True,
            config=config
        )
        
        init_time = time.time() - start_time
        print(f"✅ 初始化完成，耗时: {init_time:.1f}秒")
        
        # 验证ConditionalLogic配置
        print(f"\n🔍 验证ConditionalLogic配置:")
        print(f"  - max_debate_rounds: {ta.conditional_logic.max_debate_rounds}")
        print(f"  - max_risk_discuss_rounds: {ta.conditional_logic.max_risk_discuss_rounds}")
        
        if (ta.conditional_logic.max_debate_rounds == config["max_debate_rounds"] and
            ta.conditional_logic.max_risk_discuss_rounds == config["max_risk_discuss_rounds"]):
            print(f"✅ 配置参数传递正确")
        else:
            print(f"❌ 配置参数传递失败")
            return False
        
        # 执行快速分析
        print(f"\n📊 开始快速分析 000001...")
        analysis_start = time.time()
        
        # 设置超时时间
        timeout = 300  # 5分钟超时
        
        try:
            state, decision = await asyncio.wait_for(
                asyncio.to_thread(ta.propagate, "000001", "2025-07-26"),
                timeout=timeout
            )
            
            analysis_time = time.time() - analysis_start
            print(f"✅ 分析完成，耗时: {analysis_time:.1f}秒")
            
            # 显示结果摘要
            print(f"\n📋 分析结果摘要:")
            if decision:
                # 安全地处理decision的显示
                decision_str = str(decision)
                if len(decision_str) > 200:
                    print(f"  📊 最终决策: {decision_str[:200]}...")
                else:
                    print(f"  📊 最终决策: {decision_str}")
                print(f"  📊 决策类型: {type(decision)}")
            else:
                print(f"  ⚠️ 未获得最终决策")
            
            # 检查分析时间是否合理
            if analysis_time < 600:  # 10分钟内
                print(f"✅ 分析时间合理: {analysis_time:.1f}秒")
                return True
            else:
                print(f"⚠️ 分析时间较长: {analysis_time:.1f}秒")
                return True  # 仍然算成功，只是提醒
                
        except asyncio.TimeoutError:
            print(f"❌ 分析超时 ({timeout}秒)")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_conditional_logic_config():
    """测试ConditionalLogic配置传递"""
    print(f"\n🧪 测试ConditionalLogic配置传递")
    print("=" * 60)
    
    test_configs = [
        {"max_debate_rounds": 1, "max_risk_discuss_rounds": 1},
        {"max_debate_rounds": 2, "max_risk_discuss_rounds": 1},
        {"max_debate_rounds": 1, "max_risk_discuss_rounds": 2},
    ]
    
    for test_config in test_configs:
        print(f"\n📊 测试配置: {test_config}")
        
        config = DEFAULT_CONFIG.copy()
        config.update({
            "llm_provider": "dashscope",
            "memory_enabled": False,
            **test_config
        })
        
        try:
            ta = TradingAgentsGraph(
                selected_analysts=["market"],
                debug=False,
                config=config
            )
            
            # 验证配置
            actual_debate = ta.conditional_logic.max_debate_rounds
            actual_risk = ta.conditional_logic.max_risk_discuss_rounds
            expected_debate = test_config["max_debate_rounds"]
            expected_risk = test_config["max_risk_discuss_rounds"]
            
            if actual_debate == expected_debate and actual_risk == expected_risk:
                print(f"  ✅ 配置正确: debate={actual_debate}, risk={actual_risk}")
            else:
                print(f"  ❌ 配置错误: 期望 debate={expected_debate}, risk={expected_risk}")
                print(f"                实际 debate={actual_debate}, risk={actual_risk}")
                
        except Exception as e:
            print(f"  ❌ 初始化失败: {str(e)}")

async def main():
    """主测试函数"""
    print("🔧 ConditionalLogic修复验证测试")
    print("=" * 80)
    
    # 测试配置传递
    test_conditional_logic_config()
    
    # 测试快速分析
    success = await test_quick_analysis()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 修复验证成功！ConditionalLogic配置传递正常！")
        print("\n💡 现在分析应该:")
        print("  - 使用正确的轮次配置")
        print("  - 在合理时间内完成")
        print("  - 避免无限循环问题")
    else:
        print("❌ 修复验证失败！需要进一步检查。")

if __name__ == "__main__":
    asyncio.run(main())
