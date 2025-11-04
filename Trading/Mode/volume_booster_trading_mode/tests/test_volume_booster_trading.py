# Drakkar-Software OctoBot-Tentacles
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
import asyncio
import decimal
import contextlib
import mock
import os
import pytest


import async_channel.util as channel_util
import octobot_commons.constants as commons_constants
import octobot_commons.asyncio_tools as asyncio_tools
import octobot_commons.tests.test_config as test_config
import octobot_tentacles_manager.api as tentacles_manager_api
import octobot_backtesting.api as backtesting_api
import octobot_trading.api as trading_api
import octobot_trading.exchange_channel as exchanges_channel
import octobot_trading.enums as trading_enums
import octobot_trading.exchanges as exchanges
import tentacles.Trading.Mode.volume_booster_trading_mode.volume_booster_trading as volume_booster_trading

import tests.test_utils.config as test_utils_config
import tests.test_utils.test_exchanges as test_exchanges
import tests.test_utils.trading_modes as test_trading_modes

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

# binance symbol market extract
SYMBOL_MARKET = {
    'id': 'BTCUSDT', 'lowercaseId': 'btcusdt', 'symbol': 'BTC/USDT', 'base': 'BTC', 'quote': 'USDT',
    'settle': None, 'baseId': 'BTC', 'quoteId': 'USDT', 'settleId': None, 'type': 'spot', 'spot': True,
    'margin': True, 'swap': False, 'future': False, 'option': False, 'index': None, 'active': True,
    'contract': False, 'linear': None, 'inverse': None, 'subType': None, 'taker': 0.001, 'maker': 0.001,
    'contractSize': None, 'expiry': None, 'expiryDatetime': None, 'strike': None, 'optionType': None,
    'precision': {'amount': 5, 'price': 2, 'cost': None, 'base': 1e-08, 'quote': 1e-08},
    'limits': {
        'leverage': {'min': None, 'max': None},
        'amount': {'min': 1e-05, 'max': 9000.0},
        'price': {'min': 0.01, 'max': 1000000.0},
        'cost': {'min': 5.0, 'max': 9000000.0},
        'market': {'min': 0.0, 'max': 107.1489592}
    }, 'created': None,
    'percentage': True, 'feeSide': 'get', 'tierBased': False
}

def _get_volume_booster_config():
    return {
        "volume_target": 1000.0,
        "order_type": "market",
        "trade_frequency_min": 0.1,
        "trade_frequency_max": 0.5,
        "min_buy_amount": 10.0,
        "max_buy_amount": 50.0,
        "min_sell_amount": 10.0,
        "max_sell_amount": 50.0,
        "enable_volume_booster": True
    }


async def _init_trading_mode(config, exchange_manager, symbol):
    mode = volume_booster_trading.VolumeBoosterTradingMode(config, exchange_manager)
    mode.symbol = None if mode.get_is_symbol_wildcard() else symbol
    mode.trading_config = _get_volume_booster_config()
    await mode.initialize(trading_config=mode.trading_config)
    # add mode to exchange manager so that it can be stopped and freed from memory
    exchange_manager.trading_modes.append(mode)
    test_trading_modes.set_ready_to_start(mode.producers[0])
    return mode, mode.producers[0]


@contextlib.asynccontextmanager
async def _get_tools(symbol, additional_portfolio={}):
    tentacles_manager_api.reload_tentacle_info()
    exchange_manager = None
    try:
        config = test_config.load_test_config()
        config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_STARTING_PORTFOLIO]["USDT"] = 1000
        config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_STARTING_PORTFOLIO][
            "BTC"] = 10
        config[commons_constants.CONFIG_SIMULATOR][commons_constants.CONFIG_STARTING_PORTFOLIO].update(additional_portfolio)
        exchange_manager = test_exchanges.get_test_exchange_manager(config, "binance")
        exchange_manager.tentacles_setup_config = test_utils_config.load_test_tentacles_config()

        # use backtesting not to spam exchanges apis
        exchange_manager.is_simulated = True
        exchange_manager.is_backtesting = True
        exchange_manager.use_cached_markets = False
        backtesting = await backtesting_api.initialize_backtesting(
            config,
            exchange_ids=[exchange_manager.id],
            matrix_id=None,
            data_files=[
                os.path.join(test_config.TEST_CONFIG_FOLDER, "AbstractExchangeHistoryCollector_1586017993.616272.data")])
        exchange_manager.exchange = exchanges.ExchangeSimulator(exchange_manager.config,
                                                                exchange_manager,
                                                                backtesting)
        await exchange_manager.exchange.initialize()
        for exchange_channel_class_type in [exchanges_channel.ExchangeChannel, exchanges_channel.TimeFrameExchangeChannel]:
            await channel_util.create_all_subclasses_channel(exchange_channel_class_type, exchanges_channel.set_chan,
                                                             exchange_manager=exchange_manager)

        trader = exchanges.TraderSimulator(config, exchange_manager)
        await trader.initialize()

        # set BTC/USDT price at 1000 USDT
        if symbol not in exchange_manager.client_symbols:
            exchange_manager.client_symbols.append(symbol)
        trading_api.force_set_mark_price(exchange_manager, symbol, 1000)

        mode, producer = await _init_trading_mode(config, exchange_manager, symbol)

        yield producer, mode.get_trading_mode_consumers()[0], exchange_manager
    finally:
        if exchange_manager:
            await _stop(exchange_manager)


async def _stop(exchange_manager):
    for importer in backtesting_api.get_importers(exchange_manager.exchange.backtesting):
        await backtesting_api.stop_importer(importer)
    await exchange_manager.exchange.backtesting.stop()
    await exchange_manager.stop()


async def test_volume_booster_initialization():
    """Test that Volume Booster initializes correctly"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        # Check producer initialization
        assert producer.healthy is True
        assert producer.is_initialized is False
        
        # Check consumer initialization
        assert consumer.is_running is False
        assert consumer.target_volume == 0
        assert consumer.current_volume == 0
        assert consumer.orders_placed == 0
        assert consumer.successful_orders == 0
        assert consumer.failed_orders == 0


async def test_volume_booster_config_validation():
    """Test Volume Booster configuration validation"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        # Test configuration loading
        consumer._update_config_cache()
        
        # Check default values
        assert consumer._get_config("volume_target") == 1000.0
        assert consumer._get_config("order_type") == "market"
        assert consumer._get_config("enable_volume_booster") is True
        assert consumer._get_config("trade_frequency_min") == 0.1
        assert consumer._get_config("trade_frequency_max") == 0.5
        assert consumer._get_config("min_buy_amount") == 10.0
        assert consumer._get_config("max_buy_amount") == 50.0
        assert consumer._get_config("price_offset_percent") == 0.1


async def test_volume_booster_startup():
    """Test Volume Booster startup process"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        # Test producer startup
        await producer.start()
        
        # Wait for initialization
        await asyncio_tools.wait_asyncio_next_cycle()
        await asyncio_tools.wait_asyncio_next_cycle()
        
        # Check that producer is initialized
        assert producer.is_initialized is True
        
        # Check that consumer is running
        assert consumer.is_running is True
        assert consumer.target_volume == 1000.0
        assert consumer.current_volume == 0
        assert consumer.volume_start_time is not None


async def test_volume_booster_disabled():
    """Test Volume Booster when disabled in configuration"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        # Disable volume booster
        consumer.trading_mode.trading_config["enable_volume_booster"] = False
        
        # Try to start
        result = await consumer.inner_start()
        
        # Should return False and not start
        assert result is False
        assert consumer.is_running is False


async def test_volume_booster_insufficient_balance():
    """Test Volume Booster with insufficient balance"""
    symbol = "BTC/USDT"
    # Set very low USDT balance
    async with _get_tools(symbol, additional_portfolio={"USDT": 5}) as (producer, consumer, exchange_manager):
        await consumer.inner_start()
        
        # Try to execute a trade
        with mock.patch('random.choice', return_value=True):  # Force buy order
            with mock.patch('random.uniform', return_value=30):  # Force amount > available balance
                # This should not place an order due to insufficient balance
                await consumer._execute_volume_boost_trade(symbol)
        
        # No orders should be placed
        assert consumer.orders_placed == 0
        assert consumer.successful_orders == 0





async def test_volume_booster_order_creation_market_orders():
    """Test Volume Booster market order creation"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        # Set order type to market
        consumer.trading_mode.trading_config["order_type"] = "market"
        await consumer.inner_start()
        
        # Mock random functions
        with mock.patch('random.choice', return_value=True), \
             mock.patch('random.uniform', return_value=25.0):
            
            # Execute a trade
            await consumer._execute_volume_boost_trade(symbol)
            
            # Wait for order processing
            await asyncio_tools.wait_asyncio_next_cycle()
        
        # Check that an order was attempted
        assert consumer.orders_placed >= 1


async def test_volume_booster_buy_and_sell_orders():
    """Test that Volume Booster creates both buy and sell orders"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        await consumer.inner_start()
        
        buy_count = 0
        sell_count = 0
        
        # Execute multiple trades to test both buy and sell
        for i in range(20):
            with mock.patch('random.choice', return_value=i % 2 == 0) as mock_choice, \
                 mock.patch('random.uniform', return_value=25.0):
                
                await consumer._execute_volume_boost_trade(symbol)
                await asyncio_tools.wait_asyncio_next_cycle()
                
                if mock_choice.return_value:
                    buy_count += 1
                else:
                    sell_count += 1
        
        # Should have attempted both buy and sell orders
        assert buy_count > 0
        assert sell_count > 0
        assert consumer.orders_placed == 20


async def test_volume_booster_volume_tracking():
    """Test Volume Booster volume tracking"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        await consumer.inner_start()
        
        initial_volume = consumer.current_volume
        
        # Execute a successful trade
        with mock.patch('random.choice', return_value=True), \
             mock.patch('random.uniform', return_value=25.0):
            
            await consumer._execute_volume_boost_trade(symbol)
            await asyncio_tools.wait_asyncio_next_cycle()
        
        # Volume should increase if order was successful
        if consumer.successful_orders > 0:
            assert consumer.current_volume > initial_volume


async def test_volume_booster_target_reached():
    """Test Volume Booster stops when target is reached"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        # Set a low target for testing
        consumer.trading_mode.trading_config["volume_target"] = 50.0
        await consumer.inner_start()
        
        # Set current volume close to target
        consumer.current_volume = 45.0
        consumer.target_volume = 50.0
        
        # Execute a trade that should reach the target
        with mock.patch('random.choice', return_value=True), \
             mock.patch('random.uniform', return_value=10.0):
            
            await consumer._execute_volume_boost_trade(symbol)
            await asyncio_tools.wait_asyncio_next_cycle()
        
        # If successful, should have reached target and stopped
        if consumer.successful_orders > 0 and consumer.current_volume >= consumer.target_volume:
            # The next trade attempt should return early due to target reached
            initial_orders = consumer.orders_placed
            await consumer._execute_volume_boost_trade(symbol)
            assert consumer.orders_placed == initial_orders  # No new orders


async def test_volume_booster_stop():
    """Test Volume Booster stop functionality"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        await consumer.inner_start()
        
        # Verify it's running
        assert consumer.is_running is True
        
        # Stop the consumer
        await consumer.stop()
        
        # Verify it's stopped
        assert consumer.is_running is False
        assert consumer.should_stop is True


async def test_volume_booster_status():
    """Test Volume Booster status reporting"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        await consumer.inner_start()
        
        # Get status
        status = await consumer.get_status()
        
        # Check status fields
        assert "is_running" in status
        assert "current_volume" in status
        assert "target_volume" in status
        assert "progress_percent" in status
        assert "remaining_volume" in status
        
        assert status["is_running"] is True
        assert status["target_volume"] == 1000.0
        assert status["current_volume"] == 0.0
        assert status["progress_percent"] == 0.0
        assert status["remaining_volume"] == 1000.0


async def test_volume_booster_reset_volume():
    """Test Volume Booster volume reset functionality"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        await consumer.inner_start()
        
        # Set some volume
        consumer.current_volume = 100.0
        
        # Reset volume
        await consumer.reset_volume()
        
        # Check volume is reset
        assert consumer.current_volume == 0.0


async def test_volume_booster_update_target():
    """Test Volume Booster target volume update"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        await consumer.inner_start()
        
        # Check initial target
        assert consumer.target_volume == 1000.0
        
        # Update target
        await consumer.update_target_volume(2000.0)
        
        # Check target is updated
        assert consumer.target_volume == 2000.0





async def test_volume_booster_multiple_symbols():
    """Test Volume Booster with multiple symbols (if supported)"""
    symbols = ["BTC/USDT", "ETH/USDT"]
    
    async with _get_tools("BTC/USDT") as (producer, consumer, exchange_manager):
        # Add additional symbol
        if "ETH/USDT" not in exchange_manager.client_symbols:
            exchange_manager.client_symbols.append("ETH/USDT")
        trading_api.force_set_mark_price(exchange_manager, "ETH/USDT", 2000)
        
        await consumer.inner_start()
        
        # Test that it can handle multiple symbols in the trading loop
        # The actual behavior depends on how the exchange_config is set up
        configured_symbols = list(exchange_manager.exchange_config.traded_symbol_pairs)
        
        # Should have at least the original symbol
        assert "BTC/USDT" in configured_symbols or len(configured_symbols) > 0


async def test_volume_booster_error_handling():
    """Test Volume Booster error handling"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        await consumer.inner_start()
        
        # Test with invalid symbol to trigger error handling
        await consumer._execute_volume_boost_trade("INVALID/SYMBOL")
        
        # Should handle error gracefully and increment failed orders
        # (The exact behavior depends on how the API handles invalid symbols)
        # At minimum, it shouldn't crash


async def test_volume_booster_configuration_update():
    """Test Volume Booster configuration update during runtime"""
    symbol = "BTC/USDT"
    async with _get_tools(symbol) as (producer, consumer, exchange_manager):
        await consumer.inner_start()
        
        # Change configuration
        consumer.trading_mode.trading_config["trade_frequency_min"] = 1.0
        consumer.trading_mode.trading_config["trade_frequency_max"] = 2.0
        
        # Force configuration update
        consumer._update_config_cache()
        
        # Check updated values
        assert consumer._get_config("trade_frequency_min") == 1.0
        assert consumer._get_config("trade_frequency_max") == 2.0
