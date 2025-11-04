#!/usr/bin/env python3
"""
Volume Booster Test Runner
Simplified test runner for Volume Booster trading mode
"""

import sys
import os
import asyncio

# Add the tentacles directory to the path
sys.path.insert(0, '/Users/danielolaide/git-workspace/OctoBot-Tentacles')
sys.path.insert(0, '/Users/danielolaide/git-workspace/OctoBot')

try:
    # Import volume booster
    from Trading.Mode.volume_booster_trading_mode.volume_booster_trading import (
        VolumeBoosterTradingMode, 
        VolumeBoosterTradingModeProducer, 
        VolumeBoosterTradingModeConsumer
    )
    
    print("✅ Volume Booster imports successful")
    
    # Test basic instantiation
    class MockExchangeConfig:
        def __init__(self):
            self.traded_symbol_pairs = ['BTC/USDT']
            
    class MockTrader:
        def __init__(self):
            self.is_enabled = True
    
    class MockExchangeManager:
        def __init__(self):
            self.exchange_config = MockExchangeConfig()
            self.trader = MockTrader()
            self.exchange_name = "binance"
    
    class MockConfig:
        pass
    
    # Test mode creation
    config = MockConfig()
    exchange_manager = MockExchangeManager()
    
    mode = VolumeBoosterTradingMode(config, exchange_manager)
    print("✅ Volume Booster mode creation successful")
    
    # Test producer creation with proper mock channel
    class MockChannel:
        def __init__(self):
            self.exchange_manager = exchange_manager
    
    mock_channel = MockChannel()
    producer = VolumeBoosterTradingModeProducer(
        channel=mock_channel, 
        config=config, 
        trading_mode=mode, 
        exchange_manager=exchange_manager
    )
    print("✅ Volume Booster producer creation successful")
    
    # Test consumer creation
    consumer = VolumeBoosterTradingModeConsumer(mode)
    print("✅ Volume Booster consumer creation successful")
    
    # Test configuration methods
    test_config = {
        'volume_target': 1000.0,
        'enable_volume_booster': True,
        'order_type': 'market'
    }
    
    consumer._config_cache = test_config
    
    assert consumer._get_config('volume_target') == 1000.0
    assert consumer._get_config('enable_volume_booster') is True
    assert consumer._get_config('order_type') == 'market'
    assert consumer._get_config('nonexistent', 'default') == 'default'
    
    print("✅ Configuration methods work correctly")
    
    # Test status method
    async def test_status():
        status = await consumer.get_status()
        assert 'is_running' in status
        assert 'current_volume' in status
        assert 'target_volume' in status
        print("✅ Status method works correctly")
    
    # Test reset and update methods
    async def test_utility_methods():
        await consumer.reset_volume()
        assert consumer.current_volume == 0
        
        await consumer.update_target_volume(2000.0)
        assert consumer.target_volume == 2000.0
        
        print("✅ Utility methods work correctly")
    
    # Run async tests
    async def run_tests():
        await test_status()
        await test_utility_methods()
        print("\n🎉 All Volume Booster tests passed!")
        print("\n📋 Test Summary:")
        print("   ✅ Module imports")
        print("   ✅ Class instantiation") 
        print("   ✅ Configuration handling")
        print("   ✅ Status reporting")
        print("   ✅ Utility methods")
        print("\n🚀 Volume Booster is ready for integration testing!")
    
    # Execute tests
    asyncio.run(run_tests())
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure OctoBot modules are available")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test error: {e}")
    sys.exit(1)
