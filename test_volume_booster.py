#!/usr/bin/env python3
"""
Volume Booster Testing Script
This script helps test and debug the Volume Booster trading mode
"""

import asyncio
import json
import sys
import os

def test_volume_booster_config():
    """Test if Volume Booster configuration is valid"""
    
    print("🔍 Testing Volume Booster Configuration...")
    
    # Check profile configuration
    profile_path = "/Users/danielolaide/git-workspace/OctoBot-Tentacles/profiles/volume_booster/profile.json"
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            profile = json.load(f)
        
        print(f"✅ Profile loaded: {profile['profile']['name']}")
        print(f"   - Trader enabled: {profile['config']['trader']['enabled']}")
        print(f"   - Trader-simulator enabled: {profile['config']['trader-simulator']['enabled']}")
        print(f"   - Crypto currencies: {list(profile['config']['crypto-currencies'].keys())}")
        print(f"   - Exchanges: {list(profile['config']['exchanges'].keys())}")
    else:
        print(f"❌ Profile not found at {profile_path}")
        return False
    
    # Check tentacles configuration
    tentacles_path = "/Users/danielolaide/git-workspace/OctoBot-Tentacles/profiles/volume_booster/tentacles_config.json"
    if os.path.exists(tentacles_path):
        with open(tentacles_path, 'r') as f:
            tentacles = json.load(f)
        
        trading_modes = tentacles.get('tentacle_activation', {}).get('Trading', {})
        print(f"✅ Trading modes: {trading_modes}")
    else:
        print(f"❌ Tentacles config not found at {tentacles_path}")
        return False
    
    # Check specific configuration
    specific_config_path = "/Users/danielolaide/git-workspace/OctoBot-Tentacles/profiles/volume_booster/specific_config/VolumeBoosterTradingMode.json"
    if os.path.exists(specific_config_path):
        with open(specific_config_path, 'r') as f:
            specific_config = json.load(f)
        
        print(f"✅ Volume Booster specific config:")
        for key, value in specific_config.items():
            print(f"   - {key}: {value}")
    else:
        print(f"❌ Specific config not found at {specific_config_path}")
        return False
    
    return True

def check_python_syntax():
    """Check if the Python file has syntax errors"""
    
    print("\n🔍 Checking Python syntax...")
    
    volume_booster_path = "/Users/danielolaide/git-workspace/OctoBot-Tentacles/Trading/Mode/volume_booster_trading_mode/volume_booster_trading.py"
    
    try:
        with open(volume_booster_path, 'r') as f:
            code = f.read()
        
        # Try to compile the code
        compile(code, volume_booster_path, 'exec')
        print("✅ Python syntax is valid")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error checking syntax: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 Volume Booster Test Suite")
    print("=" * 50)
    
    # Test 1: Configuration
    config_ok = test_volume_booster_config()
    
    # Test 2: Syntax
    syntax_ok = check_python_syntax()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"   Python Syntax: {'✅ PASS' if syntax_ok else '❌ FAIL'}")
    
    if config_ok and syntax_ok:
        print("\n🎉 All tests passed! Volume Booster should work now.")
        print("\n💡 Next steps:")
        print("   1. Start OctoBot with the volume_booster profile")
        print("   2. Check logs for 'Volume Booster' messages")
        print("   3. Look for trade execution messages with ✅ emoji")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
