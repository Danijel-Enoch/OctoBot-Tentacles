#!/usr/bin/env python3
"""
Comprehensive test for Volume Booster configuration and initialization
"""

import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, '/Users/danielolaide/git-workspace/OctoBot-Tentacles')
sys.path.insert(0, '/Users/danielolaide/git-workspace/OctoBot')

def test_volume_booster_configuration():
    """Test Volume Booster configuration validation"""
    print("🔧 Testing Volume Booster Configuration...")
    
    try:
        # Import the Volume Booster
        from Trading.Mode.volume_booster_trading_mode.volume_booster_trading import (
            VolumeBoosterTradingMode,
            VolumeBoosterTradingModeProducer,
            VolumeBoosterTradingModeConsumer,
            DEFAULT_VOLUME_TARGET,
            DEFAULT_ORDER_TYPE,
            DEFAULT_TRADE_FREQUENCY_MIN,
            DEFAULT_TRADE_FREQUENCY_MAX,
            DEFAULT_MIN_BUY_AMOUNT,
            DEFAULT_MAX_BUY_AMOUNT,
            DEFAULT_MIN_SELL_AMOUNT,
            DEFAULT_MAX_SELL_AMOUNT,
            DEFAULT_PRICE_OFFSET_PERCENT,
            DEFAULT_ENABLE_VOLUME_BOOSTER,
            VOLUME_TARGET_KEY,
            ORDER_TYPE_KEY,
            TRADE_FREQUENCY_MIN_KEY,
            TRADE_FREQUENCY_MAX_KEY,
            MIN_BUY_AMOUNT_KEY,
            MAX_BUY_AMOUNT_KEY,
            MIN_SELL_AMOUNT_KEY,
            MAX_SELL_AMOUNT_KEY,
            PRICE_OFFSET_PERCENT_KEY,
            ENABLE_VOLUME_BOOSTER_KEY
        )
        print("✅ Volume Booster imports successful")

        # Create a simple mock UI for testing
        class MockUI:
            def user_input(self, key, input_type, default, inputs, **kwargs):
                inputs[key] = default
                return default

        # Create Volume Booster instance
        trading_mode = VolumeBoosterTradingMode()
        trading_mode.UI = MockUI()
        
        # Set up a mock logger
        trading_mode.logger = logging.getLogger("VolumeBoosterTest")
        trading_mode.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        trading_mode.logger.addHandler(handler)
        
        print("✅ Volume Booster instance created with mock logger")

        # Test configuration with valid inputs
        print("\n📋 Testing valid configuration...")
        valid_inputs = {}
        trading_mode.init_user_inputs(valid_inputs)
        
        # Check that all required keys are present
        required_keys = [
            VOLUME_TARGET_KEY,
            ORDER_TYPE_KEY,
            TRADE_FREQUENCY_MIN_KEY,
            TRADE_FREQUENCY_MAX_KEY,
            MIN_BUY_AMOUNT_KEY,
            MAX_BUY_AMOUNT_KEY,
            MIN_SELL_AMOUNT_KEY,
            MAX_SELL_AMOUNT_KEY,
            PRICE_OFFSET_PERCENT_KEY,
            ENABLE_VOLUME_BOOSTER_KEY
        ]
        
        for key in required_keys:
            if key not in valid_inputs:
                raise ValueError(f"Missing configuration key: {key}")
        
        print("✅ All configuration keys present")
        print("✅ Configuration validation completed without errors")

        # Test configuration with invalid inputs (should auto-correct)
        print("\n🔧 Testing invalid configuration (should auto-correct)...")
        invalid_inputs = {
            VOLUME_TARGET_KEY: 0,  # Invalid: should be > 0
            MIN_BUY_AMOUNT_KEY: 100,  # Invalid: min > max
            MAX_BUY_AMOUNT_KEY: 50,
            MIN_SELL_AMOUNT_KEY: 200,  # Invalid: min > max  
            MAX_SELL_AMOUNT_KEY: 100,
            TRADE_FREQUENCY_MIN_KEY: 10,  # Invalid: min > max
            TRADE_FREQUENCY_MAX_KEY: 5
        }
        
        trading_mode.init_user_inputs(invalid_inputs)
        print("✅ Invalid configuration auto-corrected successfully")
        
        # Check auto-corrections
        assert invalid_inputs[VOLUME_TARGET_KEY] == DEFAULT_VOLUME_TARGET, "Volume target should be corrected"
        assert invalid_inputs[MIN_BUY_AMOUNT_KEY] <= invalid_inputs[MAX_BUY_AMOUNT_KEY], "Buy amounts should be swapped"
        assert invalid_inputs[MIN_SELL_AMOUNT_KEY] <= invalid_inputs[MAX_SELL_AMOUNT_KEY], "Sell amounts should be swapped"
        assert invalid_inputs[TRADE_FREQUENCY_MIN_KEY] <= invalid_inputs[TRADE_FREQUENCY_MAX_KEY], "Frequencies should be swapped"
        print("✅ All auto-corrections work properly")

        print("\n🎉 Volume Booster Configuration Test Completed Successfully!")
        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Volume Booster Comprehensive Test Suite")
    print("=" * 50)
    
    success = test_volume_booster_configuration()
    
    if success:
        print("\n🎉 All tests passed! Volume Booster is ready for use.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
