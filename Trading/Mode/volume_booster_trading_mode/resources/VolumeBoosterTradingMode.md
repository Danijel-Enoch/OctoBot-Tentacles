# Volume Booster Trading Mode

## Description
The Volume Booster Trading Mode is designed to rapidly execute buy and sell orders to increase trading volume on selected cryptocurrency pairs. This mode is useful for:

- Testing exchange connectivity and order execution
- Market making activities
- Volume requirements for certain exchanges or listings
- Stress testing trading systems

## Features
- **Configurable Volume Target**: Set your desired volume target in base currency units
- **Market Orders Only**: All orders execute immediately at current market price
- **Flexible Trade Frequency**: Set minimum and maximum intervals between trades
- **Amount Randomization**: Configure min/max buy and sell amounts for natural trading patterns
- **Real-time Monitoring**: Track progress toward volume target
- **Balance Protection**: Automatic balance checking to prevent overtrading

## Configuration Parameters

### Volume Target
- **Default**: 10,000
- **Description**: Target volume to achieve (in base currency units like USDT)

### Order Type
- **Options**: "market" only
- **Default**: "market"
- **Description**: Market orders execute immediately at current market price

### Trade Frequency
- **Min Frequency**: Minimum seconds between trades (default: 1.0)
- **Max Frequency**: Maximum seconds between trades (default: 5.0)
- **Description**: Random interval between these values for natural trading patterns

### Trade Amounts
- **Min/Max Buy Amount**: Range for buy order sizes in quote currency
- **Min/Max Sell Amount**: Range for sell order sizes in quote currency
- **Defaults**: 10-100 for both buy and sell



## Safety Features
- **Balance Checking**: Verifies sufficient funds before placing orders
- **Error Handling**: Graceful handling of exchange errors and network issues
- **Configurable Limits**: Prevents excessive trading through amount and frequency controls
- **Stop/Start Control**: Enable/disable volume boosting without restarting the bot

## Usage Notes
- This mode is **NOT backtestable** as it's designed for live trading only
- Works with both SPOT and FUTURES exchanges
- Recommended for use in simulation mode first
- Monitor your exchange's rate limits and trading fees
- Ensure adequate balance in both base and quote currencies

## Risk Warnings
- This mode will consume trading fees on each transaction
- High-frequency trading may trigger exchange rate limits
- Always test in simulation mode first
- Consider market impact of rapid trading
- Monitor balance levels to avoid insufficient funds errors
