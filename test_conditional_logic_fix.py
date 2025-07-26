#!/usr/bin/env python3
"""
测试ConditionalLogic修复后的轮次控制
"""

from tradingagents.graph.conditional_logic import ConditionalLogic
from tradingagents.agents.utils.agent_states import RiskDebateState

def test_risk_analysis_rounds():
    """测试风险分析轮次控制"""
    print("🧪 测试ConditionalLogic风险分析轮次控制")
    print("=" * 60)
    
    # 测试不同的max_risk_discuss_rounds设置
    test_cases = [
        {"max_rounds": 1, "expected_limit": 3},
        {"max_rounds": 2, "expected_limit": 6},
        {"max_rounds": 3, "expected_limit": 9}
    ]
    
    for case in test_cases:
        max_rounds = case["max_rounds"]
        expected_limit = case["expected_limit"]
        
        print(f"\n📊 测试 max_risk_discuss_rounds = {max_rounds}")
        print(f"📊 期望终止条件: count >= {expected_limit}")
        
        # 创建ConditionalLogic实例
        logic = ConditionalLogic(max_risk_discuss_rounds=max_rounds)
        
        # 模拟风险分析状态
        speakers = ["Risky", "Safe", "Neutral"]
        count = 0
        
        # 模拟分析流程
        for round_num in range(1, 5):  # 最多测试4轮
            for speaker in speakers:
                count += 1
                
                # 创建模拟状态
                mock_state = {
                    "risk_debate_state": {
                        "count": count,
                        "latest_speaker": speaker
                    }
                }
                
                # 检查是否应该继续
                next_step = logic.should_continue_risk_analysis(mock_state)
                
                print(f"  轮次 {round_num}, 发言者 {speaker}, count={count} -> {next_step}")
                
                if next_step == "Risk Judge":
                    print(f"  ✅ 在count={count}时正确终止 (期望>={expected_limit})")
                    break
            
            if next_step == "Risk Judge":
                break
        
        # 验证结果
        if count >= expected_limit and next_step == "Risk Judge":
            print(f"  ✅ 测试通过: 在count={count}时终止")
        else:
            print(f"  ❌ 测试失败: count={count}, next_step={next_step}")

def test_debate_rounds():
    """测试投资辩论轮次控制"""
    print(f"\n🧪 测试投资辩论轮次控制")
    print("=" * 60)
    
    # 测试不同的max_debate_rounds设置
    test_cases = [
        {"max_rounds": 1, "expected_limit": 2},
        {"max_rounds": 2, "expected_limit": 4},
        {"max_rounds": 3, "expected_limit": 6}
    ]
    
    for case in test_cases:
        max_rounds = case["max_rounds"]
        expected_limit = case["expected_limit"]
        
        print(f"\n📊 测试 max_debate_rounds = {max_rounds}")
        print(f"📊 期望终止条件: count >= {expected_limit}")
        
        # 创建ConditionalLogic实例
        logic = ConditionalLogic(max_debate_rounds=max_rounds)
        
        # 模拟辩论状态
        speakers = ["Bull", "Bear"]
        count = 0
        
        # 模拟辩论流程
        for round_num in range(1, 5):  # 最多测试4轮
            for speaker in speakers:
                count += 1
                
                # 创建模拟状态
                mock_state = {
                    "investment_debate_state": {
                        "count": count,
                        "current_response": f"{speaker} Researcher response"
                    }
                }
                
                # 检查是否应该继续
                next_step = logic.should_continue_debate(mock_state)
                
                print(f"  轮次 {round_num}, 发言者 {speaker}, count={count} -> {next_step}")
                
                if next_step == "Research Manager":
                    print(f"  ✅ 在count={count}时正确终止 (期望>={expected_limit})")
                    break
            
            if next_step == "Research Manager":
                break
        
        # 验证结果
        if count >= expected_limit and next_step == "Research Manager":
            print(f"  ✅ 测试通过: 在count={count}时终止")
        else:
            print(f"  ❌ 测试失败: count={count}, next_step={next_step}")

def test_config_integration():
    """测试配置集成"""
    print(f"\n🧪 测试配置集成")
    print("=" * 60)
    
    # 模拟不同的配置
    configs = [
        {"max_debate_rounds": 1, "max_risk_discuss_rounds": 1},
        {"max_debate_rounds": 2, "max_risk_discuss_rounds": 1},
        {"max_debate_rounds": 1, "max_risk_discuss_rounds": 2},
    ]
    
    for config in configs:
        print(f"\n📊 测试配置: {config}")
        
        # 创建ConditionalLogic实例
        logic = ConditionalLogic(
            max_debate_rounds=config["max_debate_rounds"],
            max_risk_discuss_rounds=config["max_risk_discuss_rounds"]
        )
        
        print(f"  📊 辩论轮次限制: {logic.max_debate_rounds} -> 终止条件: count >= {2 * logic.max_debate_rounds}")
        print(f"  📊 风险分析轮次限制: {logic.max_risk_discuss_rounds} -> 终止条件: count >= {3 * logic.max_risk_discuss_rounds}")

if __name__ == "__main__":
    print("🔧 ConditionalLogic轮次控制测试")
    print("=" * 80)
    
    # 测试风险分析轮次
    test_risk_analysis_rounds()
    
    # 测试投资辩论轮次
    test_debate_rounds()
    
    # 测试配置集成
    test_config_integration()
    
    print("\n" + "=" * 80)
    print("🎉 测试完成！")
    print("\n💡 修复建议:")
    print("1. 确保ConditionalLogic初始化时传递正确的配置参数")
    print("2. 使用较小的轮次设置避免分析时间过长")
    print("3. 推荐配置: max_debate_rounds=1, max_risk_discuss_rounds=1")
