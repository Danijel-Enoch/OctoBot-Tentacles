# Volume Booster Trading Mode - Complete Setup Guide

## Overview
The Volume Booster Trading Mode is a custom OctoBot tentacle that rapidly executes buy and sell orders to increase trading volume on selected pairs. This guide follows OctoBot's official tentacle development guidelines.

## Installation Methods

### Method 1: Direct Installation (Recommended)

1. **Copy files to OctoBot-Tentacles directory**
Ensure all files are in the correct locations:

```
OctoBot-Tentacles/
├── Trading/Mode/volume_booster_trading_mode/
│   ├── __init__.py
│   ├── volume_booster_trading.py
│   ├── volume_booster_trading.pxd
│   ├── metadata.json
│   ├── config/
│   │   └── configuration_examples.json
│   ├── resources/
│   │   └── VolumeBoosterTradingMode.md
│   └── tests/
│       └── __init__.py
└── profiles/volume_booster/
    ├── profile.json
    ├── tentacles_config.json
    ├── README.md
    ├── volume_booster_profile.png
    └── specific_config/
        └── VolumeBoosterTradingMode.json
```

2. **Restart OctoBot** for tentacle discovery

3. **Verify installation** in OctoBot web interface:
   - Go to Configuration > Tentacles
   - Find "VolumeBoosterTradingMode" in Trading Modes section
   - Ensure it's available for activation

### Method 2: Tentacle Bundle Installation

1. **Create tentacle bundle** (from OctoBot directory):
   ```bash
   python start.py tentacles --pack "../volume_booster_bundle.zip" --directory "path/to/volume_booster_files"
   ```

2. **Install the bundle**:
   ```bash
   python start.py tentacles --install --all --location "../volume_booster_bundle.zip"
   ```

### Method 3: Single Tentacle Installation

```bash
python start.py tentacles --single-tentacle-install "path/to/volume_booster_trading_mode" Trading/Mode
```

## Profile Setup
1. Start OctoBot
2. Navigate to Configuration > Profiles
3. Select "Volume Booster" profile
4. Configure the parameters according to your needs
5. Save and restart if necessary

## Configuration

### Basic Setup
1. **Volume Target**: Set your desired volume (e.g., 50000 USDT)
2. **Order Type**: Market orders only for immediate execution at current price
3. **Frequency**: Start conservative (5-15 seconds) and adjust as needed
4. **Amounts**: Set within your budget and exchange minimums

### Testing
Always test in simulation mode first:
1. Enable "Trader Simulator" in configuration
2. Set a reasonable starting portfolio
3. Monitor logs for any errors
4. Verify orders are being placed correctly

### Live Trading
Only switch to live trading after thorough testing:
1. Ensure adequate balance in both currencies
2. Check exchange API limits and fees  
3. Start with smaller volume targets
4. Monitor closely for the first few hours

## Troubleshooting

### Common Issues

**"Insufficient balance" errors:**
- Check your portfolio balances
- Reduce order sizes
- Ensure you have both base and quote currencies

**"Order rejected" errors:**
- Check minimum order sizes for your exchange
- Verify price precision requirements
- Ensure you have sufficient balance including fees

**"Rate limit" errors:**
- Increase minimum trade frequency
- Check your exchange's API limits
- Consider using VIP accounts for higher limits

**No orders being placed:**
- Verify the mode is enabled in configuration
- Check that `enable_volume_booster` is true
- Look for error messages in logs

### Performance Tips

1. **Balance Management**: Keep roughly 50/50 split between base and quote currencies
2. **Fee Consideration**: Account for trading fees in your volume calculations
3. **Market Hours**: Some exchanges have different limits during high/low activity
4. **Network**: Ensure stable internet connection for consistent order placement

## Support

For additional help:
1. Check OctoBot documentation
2. Review the mode's resource files
3. Enable debug logging for detailed information
4. Test in simulation mode to isolate issues

## Legal Notice
This trading mode is for educational and research purposes. Users are responsible for:
- Compliance with local trading regulations
- Understanding exchange terms of service
- Managing risk appropriately
- Paying applicable taxes on trading activity
