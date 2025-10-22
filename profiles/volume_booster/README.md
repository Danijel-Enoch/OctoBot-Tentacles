# Volume Booster Profile

## Overview
The Volume Booster profile is specifically designed to rapidly execute buy and sell orders to increase trading volume on selected cryptocurrency pairs. This profile uses the VolumeBoosterTradingMode to achieve high-frequency trading patterns.

## Use Cases
- **Volume Requirements**: Meeting exchange listing or tier requirements
- **Market Making**: Providing liquidity to thin markets  
- **System Testing**: Stress testing trading infrastructure
- **Research**: Studying market microstructure and order flow

## Profile Configuration

### Default Settings
- **Target Volume**: 50,000 USDT
- **Order Type**: Limit orders (0.2% offset from market price)
- **Trade Frequency**: 2-8 seconds between trades
- **Order Sizes**: 25-150 USDT per trade
- **Starting Portfolio**: 1 BTC + 10,000 USDT

### Risk Level: 5/5 (High)
This profile is marked as high risk because:
- Rapid order execution consumes trading fees
- High frequency may trigger exchange rate limits  
- Requires active monitoring and adequate balances
- Designed for experienced users only

### Complexity: 2/5 (Intermediate)
While the concept is straightforward, users should understand:
- Trading mechanics and order types
- Exchange fee structures
- Balance management
- Risk management principles

## Getting Started

1. **Test in Simulation Mode First**
   - Always start with paper trading to understand behavior
   - Verify configuration parameters work as expected
   - Monitor logs for any errors or warnings

2. **Configure Your Parameters**
   - Set appropriate volume targets for your needs
   - Adjust trade frequency based on exchange limits
   - Configure order sizes within your budget
   - Choose between market or limit orders

3. **Monitor Progress**
   - Watch the volume progress in logs
   - Ensure sufficient balance in both currencies
   - Check that orders are executing as expected
   - Monitor exchange rate limits

## Important Notes

### Exchange Compatibility  
- Works with SPOT and FUTURES markets
- Tested primarily with Binance
- Check your exchange's API rate limits
- Verify minimum order sizes

### Balance Requirements
- Maintain adequate base currency for sell orders
- Maintain adequate quote currency for buy orders  
- Consider trading fees in your calculations
- Monitor balance levels continuously

### Legal and Compliance
- Ensure compliance with local trading regulations
- Some jurisdictions may restrict high-frequency trading
- Understand tax implications of frequent trading
- Consider market manipulation regulations

## Troubleshooting

### Common Issues
1. **Insufficient Balance**: Reduce order sizes or increase funding
2. **Rate Limit Errors**: Increase minimum trade frequency
3. **Order Rejections**: Check minimum order sizes and price precision
4. **No Volume Progress**: Verify orders are actually executing

### Configuration Tips
- Start with smaller volume targets
- Use wider price offsets for limit orders in volatile markets
- Adjust frequency based on market conditions
- Monitor performance and optimize parameters

## Support
For issues or questions about the Volume Booster profile:
- Check the trading mode documentation
- Review OctoBot logs for error messages  
- Test configurations in simulation mode
- Ensure your exchange API permissions are correct
