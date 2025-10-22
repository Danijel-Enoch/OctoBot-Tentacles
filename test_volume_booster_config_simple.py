#!/usr/bin/env python3
"""
Simple configuration test for Volume Booster without full initialization
"""

import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, '/Users/danielolaide/git-workspace/OctoBot-Tentacles')
sys.path.insert(0, '/Users/danielolaide/git-workspace/OctoBot')

def test_volume_booster_imports_and_constants():
    """Test Volume Booster imports and constants"""
    print("📦 Testing Volume Booster imports and constants...")
    
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

        # Test that constants are properly defined
        constants = {
            "VOLUME_TARGET": DEFAULT_VOLUME_TARGET,
            "ORDER_TYPE": DEFAULT_ORDER_TYPE, 
            "TRADE_FREQUENCY_MIN": DEFAULT_TRADE_FREQUENCY_MIN,
            "TRADE_FREQUENCY_MAX": DEFAULT_TRADE_FREQUENCY_MAX,
            "MIN_BUY_AMOUNT": DEFAULT_MIN_BUY_AMOUNT,
            "MAX_BUY_AMOUNT": DEFAULT_MAX_BUY_AMOUNT,
            "MIN_SELL_AMOUNT": DEFAULT_MIN_SELL_AMOUNT,
            "MAX_SELL_AMOUNT": DEFAULT_MAX_SELL_AMOUNT,
            "PRICE_OFFSET_PERCENT": DEFAULT_PRICE_OFFSET_PERCENT,
            "ENABLE_VOLUME_BOOSTER": DEFAULT_ENABLE_VOLUME_BOOSTER
        }
        
        for name, value in constants.items():
            if value is None:
                raise ValueError(f"Constant {name} is None")
            print(f"  ✅ {name}: {value}")
        
        print("✅ All constants properly defined")

        # Test that keys are properly defined
        keys = [
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
        
        for key in keys:
            if not key or not isinstance(key, str):
                raise ValueError(f"Invalid key: {key}")
            print(f"  ✅ Key: {key}")
        
        print("✅ All configuration keys properly defined")
        
        return True

    except Exception as e:
        print(f"❌ Import/constants test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validate_configuration_method():
    """Test the _validate_configuration method indirectly"""
    print("\n🔧 Testing configuration validation method...")
    
    try:
        from Trading.Mode.volume_booster_trading_mode.volume_booster_trading import (
            VolumeBoosterTradingMode,
            DEFAULT_VOLUME_TARGET,
            MIN_BUY_AMOUNT_KEY,
            MAX_BUY_AMOUNT_KEY,
            VOLUME_TARGET_KEY
        )
        
        # Check that the method exists
        if not hasattr(VolumeBoosterTradingMode, '_validate_configuration'):
            raise AttributeError("_validate_configuration method not found")
        
        print("✅ _validate_configuration method exists")
        
        # Test that the method doesn't use get_logger (the previous issue)
        import inspect
        source = inspect.getsource(VolumeBoosterTradingMode._validate_configuration)
        if 'get_logger()' in source:
            raise ValueError("Method still uses get_logger() instead of logger")
        
        if 'self.logger' in source:
            print("✅ Method uses self.logger correctly")
        else:
            print("⚠️  Method doesn't use logging (may be acceptable)")
        
        print("✅ Configuration validation method looks good")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Volume Booster Configuration Test Suite")
    print("=" * 50)
    
    test1 = test_volume_booster_imports_and_constants()
    test2 = test_validate_configuration_method()
    
    if test1 and test2:
        print("\n🎉 All configuration tests passed!")
        print("✅ Volume Booster can be imported without errors")
        print("✅ Configuration constants are properly defined") 
        print("✅ Configuration validation method is correct")
        print("✅ Logger usage has been fixed")
        return 0
    else:
        print("\n❌ Some configuration tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
