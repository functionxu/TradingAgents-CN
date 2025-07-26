#!/usr/bin/env python3
"""
测试内存服务状态
"""

import os
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

def test_memory_service_status():
    """测试内存服务状态"""
    print("🧠 测试内存服务状态")
    print("=" * 60)
    
    # 检查环境变量
    print("📊 检查环境变量:")
    dashscope_key = os.getenv('DASHSCOPE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    force_openai = os.getenv('FORCE_OPENAI_EMBEDDING', 'false').lower()
    
    print(f"  - DASHSCOPE_API_KEY: {'✅ 已设置' if dashscope_key else '❌ 未设置'}")
    print(f"  - OPENAI_API_KEY: {'✅ 已设置' if openai_key else '❌ 未设置'}")
    print(f"  - FORCE_OPENAI_EMBEDDING: {force_openai}")
    
    # 测试不同的内存配置
    test_configs = [
        {
            "name": "内存禁用",
            "config": {"memory_enabled": False}
        },
        {
            "name": "内存启用 - DashScope",
            "config": {"memory_enabled": True, "llm_provider": "dashscope"}
        },
        {
            "name": "内存启用 - OpenAI强制",
            "config": {"memory_enabled": True, "llm_provider": "dashscope"}
        }
    ]
    
    for test_case in test_configs:
        print(f"\n📊 测试: {test_case['name']}")
        print("-" * 40)
        
        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config.update({
            "llm_provider": "dashscope",
            "deep_think_llm": "qwen-plus",
            "quick_think_llm": "qwen-turbo",
            **test_case["config"]
        })
        
        # 如果是OpenAI强制测试，设置环境变量
        if test_case["name"] == "内存启用 - OpenAI强制":
            os.environ['FORCE_OPENAI_EMBEDDING'] = 'true'
        else:
            os.environ.pop('FORCE_OPENAI_EMBEDDING', None)
        
        try:
            print(f"🔧 初始化TradingAgentsGraph...")
            ta = TradingAgentsGraph(
                selected_analysts=["market"],
                debug=False,
                config=config
            )
            
            # 检查内存对象状态
            print(f"📊 内存服务状态:")
            print(f"  - memory_enabled: {config.get('memory_enabled', True)}")
            print(f"  - bull_memory: {type(ta.bull_memory).__name__ if ta.bull_memory else 'None'}")
            print(f"  - bear_memory: {type(ta.bear_memory).__name__ if ta.bear_memory else 'None'}")
            print(f"  - trader_memory: {type(ta.trader_memory).__name__ if ta.trader_memory else 'None'}")
            print(f"  - invest_judge_memory: {type(ta.invest_judge_memory).__name__ if ta.invest_judge_memory else 'None'}")
            print(f"  - risk_manager_memory: {type(ta.risk_manager_memory).__name__ if ta.risk_manager_memory else 'None'}")
            
            # 如果内存启用，测试内存功能
            if ta.bull_memory:
                print(f"\n🧠 测试内存功能:")
                try:
                    # 测试内存客户端状态
                    if hasattr(ta.bull_memory, 'client'):
                        client_status = ta.bull_memory.client
                        if client_status == "DISABLED":
                            print(f"  ❌ 内存客户端已禁用")
                        elif client_status is None:
                            print(f"  ✅ 内存客户端正常 (DashScope)")
                        else:
                            print(f"  ✅ 内存客户端正常 (OpenAI)")
                    
                    # 测试嵌入模型
                    if hasattr(ta.bull_memory, 'embedding'):
                        embedding_model = ta.bull_memory.embedding
                        print(f"  📊 嵌入模型: {embedding_model}")
                    
                    # 测试LLM提供商
                    if hasattr(ta.bull_memory, 'llm_provider'):
                        llm_provider = ta.bull_memory.llm_provider
                        print(f"  📊 LLM提供商: {llm_provider}")
                        
                except Exception as e:
                    print(f"  ❌ 内存功能测试失败: {str(e)}")
            
            print(f"  ✅ 初始化成功")
            
        except Exception as e:
            print(f"  ❌ 初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()

def test_memory_dependencies():
    """测试内存服务依赖"""
    print(f"\n🔍 测试内存服务依赖")
    print("=" * 60)
    
    # 测试ChromaDB
    try:
        import chromadb
        print(f"✅ ChromaDB: 已安装 (版本: {chromadb.__version__})")
    except ImportError as e:
        print(f"❌ ChromaDB: 未安装 - {e}")
    
    # 测试DashScope
    try:
        import dashscope
        print(f"✅ DashScope: 已安装")
        
        # 测试DashScope TextEmbedding
        try:
            from dashscope import TextEmbedding
            print(f"✅ DashScope TextEmbedding: 可用")
        except ImportError as e:
            print(f"❌ DashScope TextEmbedding: 不可用 - {e}")
            
    except ImportError as e:
        print(f"❌ DashScope: 未安装 - {e}")
    
    # 测试OpenAI (用于嵌入)
    try:
        import openai
        print(f"✅ OpenAI: 已安装 (版本: {openai.__version__})")
    except ImportError as e:
        print(f"❌ OpenAI: 未安装 - {e}")

def main():
    """主测试函数"""
    print("🧠 内存服务状态检查")
    print("=" * 80)
    
    # 测试依赖
    test_memory_dependencies()
    
    # 测试内存服务状态
    test_memory_service_status()
    
    print("\n" + "=" * 80)
    print("🎯 内存服务状态检查完成")
    print("\n💡 说明:")
    print("- 如果看到 'memory为None，跳过历史记忆检索'，说明内存服务被禁用")
    print("- 内存服务需要 ChromaDB + (DashScope 或 OpenAI) 嵌入模型")
    print("- 可以通过 memory_enabled=True 启用内存服务")
    print("- 内存服务主要用于存储和检索历史分析经验")

if __name__ == "__main__":
    main()
