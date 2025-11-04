#  Drakkar-Software OctoBot-Tentacles
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
import random
import time
import typing

try:
    import octobot_commons.constants as commons_constants
    import octobot_commons.enums as commons_enums
    import octobot_commons.pretty_printer as pretty_printer
    import octobot_commons.logging as bot_logging
    import octobot_commons.tentacles_management as tentacles_management
    
    import octobot_trading.constants as trading_constants
    import octobot_trading.api as trading_api
    import octobot_trading.modes as trading_modes
    import octobot_trading.enums as trading_enums
    import octobot_trading.personal_data as trading_personal_data
    import octobot_trading.errors as trading_errors
    import octobot_trading.util as trading_util
    
except ImportError as e:
    raise ImportError(f"Required OctoBot modules not found: {e}")

# Configuration constants
VOLUME_TARGET_KEY = "volume_target"
ORDER_TYPE_KEY = "order_type"
TRADE_FREQUENCY_MIN_KEY = "trade_frequency_min"
TRADE_FREQUENCY_MAX_KEY = "trade_frequency_max"
MIN_BUY_AMOUNT_KEY = "min_buy_amount"
MAX_BUY_AMOUNT_KEY = "max_buy_amount"
MIN_SELL_AMOUNT_KEY = "min_sell_amount"
MAX_SELL_AMOUNT_KEY = "max_sell_amount"
ENABLE_VOLUME_BOOSTER_KEY = "enable_volume_booster"

# Default values
DEFAULT_VOLUME_TARGET = 10000
DEFAULT_ORDER_TYPE = "market"
DEFAULT_TRADE_FREQUENCY_MIN = 1.0
DEFAULT_TRADE_FREQUENCY_MAX = 5.0
DEFAULT_MIN_BUY_AMOUNT = 10
DEFAULT_MAX_BUY_AMOUNT = 100
DEFAULT_MIN_SELL_AMOUNT = 10
DEFAULT_MAX_SELL_AMOUNT = 100
DEFAULT_ENABLE_VOLUME_BOOSTER = True

# User input descriptions
VOLUME_TARGET_DESC = "Target volume to achieve (in base currency units like USDT)"
ORDER_TYPE_DESC = "Market orders execute immediately at current market price"
TRADE_FREQUENCY_MIN_DESC = "Minimum seconds between trades (lower = more frequent)"
TRADE_FREQUENCY_MAX_DESC = "Maximum seconds between trades (creates randomized intervals)"
MIN_BUY_AMOUNT_DESC = "Minimum amount to buy in quote currency (e.g., USDT)"
MAX_BUY_AMOUNT_DESC = "Maximum amount to buy in quote currency (e.g., USDT)"
MIN_SELL_AMOUNT_DESC = "Minimum amount to sell in quote currency (e.g., USDT)"
MAX_SELL_AMOUNT_DESC = "Maximum amount to sell in quote currency (e.g., USDT)"
ENABLE_VOLUME_BOOSTER_DESC = "Start/Stop the volume boosting activity"

# Trading mode metadata
VOLUME_BOOSTER_MODE_NAME = "VolumeBoosterTradingMode"


class VolumeBoosterTradingMode(trading_modes.AbstractTradingMode):
    """
    Volume Booster Trading Mode - Rapidly executes buy and sell orders to boost volume
    """

    def init_user_inputs(self, inputs: dict) -> None:
        """
        Called right before starting the tentacle, should define all the tentacle's user inputs unless
        those are defined somewhere else.
        """
        # Volume Configuration
        self.UI.user_input(
            VOLUME_TARGET_KEY, commons_enums.UserInputTypes.FLOAT, DEFAULT_VOLUME_TARGET, inputs,
            min_val=1, max_val=10000000,
            title=VOLUME_TARGET_DESC
        )
        
        # Order Configuration - Market orders only
        self.UI.user_input(
            ORDER_TYPE_KEY, commons_enums.UserInputTypes.OPTIONS, DEFAULT_ORDER_TYPE, inputs,
            options=["market"],
            title=ORDER_TYPE_DESC
        )
        
        # Frequency Configuration  
        self.UI.user_input(
            TRADE_FREQUENCY_MIN_KEY, commons_enums.UserInputTypes.FLOAT, DEFAULT_TRADE_FREQUENCY_MIN, inputs,
            min_val=0.1, max_val=3600,
            title=TRADE_FREQUENCY_MIN_DESC
        )
        
        self.UI.user_input(
            TRADE_FREQUENCY_MAX_KEY, commons_enums.UserInputTypes.FLOAT, DEFAULT_TRADE_FREQUENCY_MAX, inputs,
            min_val=0.1, max_val=3600,
            title=TRADE_FREQUENCY_MAX_DESC
        )
        
        # Buy Amount Configuration
        self.UI.user_input(
            MIN_BUY_AMOUNT_KEY, commons_enums.UserInputTypes.FLOAT, DEFAULT_MIN_BUY_AMOUNT, inputs,
            min_val=0.01, max_val=1000000,
            title=MIN_BUY_AMOUNT_DESC
        )
        
        self.UI.user_input(
            MAX_BUY_AMOUNT_KEY, commons_enums.UserInputTypes.FLOAT, DEFAULT_MAX_BUY_AMOUNT, inputs,
            min_val=0.01, max_val=1000000,
            title=MAX_BUY_AMOUNT_DESC
        )
        
        # Sell Amount Configuration
        self.UI.user_input(
            MIN_SELL_AMOUNT_KEY, commons_enums.UserInputTypes.FLOAT, DEFAULT_MIN_SELL_AMOUNT, inputs,
            min_val=0.01, max_val=1000000,
            title=MIN_SELL_AMOUNT_DESC
        )
        
        self.UI.user_input(
            MAX_SELL_AMOUNT_KEY, commons_enums.UserInputTypes.FLOAT, DEFAULT_MAX_SELL_AMOUNT, inputs,
            min_val=0.01, max_val=1000000,
            title=MAX_SELL_AMOUNT_DESC
        )
        

        
        # Control Configuration
        self.UI.user_input(
            ENABLE_VOLUME_BOOSTER_KEY, commons_enums.UserInputTypes.BOOLEAN, DEFAULT_ENABLE_VOLUME_BOOSTER, inputs,
            title=ENABLE_VOLUME_BOOSTER_DESC
        )
        
        # Validate configuration after all inputs are defined
        self._validate_configuration(inputs)

    def _validate_configuration(self, inputs: dict):
        """
        Validate user configuration inputs and fix common issues
        """
        try:
            # Get values with defaults
            min_buy = inputs.get(MIN_BUY_AMOUNT_KEY, DEFAULT_MIN_BUY_AMOUNT)
            max_buy = inputs.get(MAX_BUY_AMOUNT_KEY, DEFAULT_MAX_BUY_AMOUNT)
            min_sell = inputs.get(MIN_SELL_AMOUNT_KEY, DEFAULT_MIN_SELL_AMOUNT)
            max_sell = inputs.get(MAX_SELL_AMOUNT_KEY, DEFAULT_MAX_SELL_AMOUNT)
            min_freq = inputs.get(TRADE_FREQUENCY_MIN_KEY, DEFAULT_TRADE_FREQUENCY_MIN)
            max_freq = inputs.get(TRADE_FREQUENCY_MAX_KEY, DEFAULT_TRADE_FREQUENCY_MAX)
            volume_target = inputs.get(VOLUME_TARGET_KEY, DEFAULT_VOLUME_TARGET)
            
            # Validation and auto-correction
            if min_buy >= max_buy:
                self.logger.warning(f"Minimum buy amount ({min_buy}) >= maximum ({max_buy}), swapping values")
                inputs[MIN_BUY_AMOUNT_KEY] = max_buy
                inputs[MAX_BUY_AMOUNT_KEY] = min_buy
                
            if min_sell >= max_sell:
                self.logger.warning(f"Minimum sell amount ({min_sell}) >= maximum ({max_sell}), swapping values")
                inputs[MIN_SELL_AMOUNT_KEY] = max_sell
                inputs[MAX_SELL_AMOUNT_KEY] = min_sell
                
            if min_freq >= max_freq:
                self.logger.warning(f"Minimum frequency ({min_freq}) >= maximum ({max_freq}), swapping values")
                inputs[TRADE_FREQUENCY_MIN_KEY] = max_freq
                inputs[TRADE_FREQUENCY_MAX_KEY] = min_freq
            
            # Critical validations
            if volume_target <= 0:
                self.logger.error("Volume target must be greater than 0")
                inputs[VOLUME_TARGET_KEY] = DEFAULT_VOLUME_TARGET
                
            # Log final configuration
            self.logger.info(f"Volume Booster Configuration validated:")
            self.logger.info(f"  - Target Volume: {inputs.get(VOLUME_TARGET_KEY)}")
            self.logger.info(f"  - Order Type: {inputs.get(ORDER_TYPE_KEY)}")
            self.logger.info(f"  - Trade Frequency: {inputs.get(TRADE_FREQUENCY_MIN_KEY)}-{inputs.get(TRADE_FREQUENCY_MAX_KEY)}s")
            self.logger.info(f"  - Buy Amounts: {inputs.get(MIN_BUY_AMOUNT_KEY)}-{inputs.get(MAX_BUY_AMOUNT_KEY)}")
            self.logger.info(f"  - Sell Amounts: {inputs.get(MIN_SELL_AMOUNT_KEY)}-{inputs.get(MAX_SELL_AMOUNT_KEY)}")
            
        except Exception as e:
            self.logger.error(f"Configuration validation error: {e}")

    @classmethod
    def get_mode_producer_classes(cls) -> list:
        """
        :return: The list of producers classes
        """
        return [VolumeBoosterTradingModeProducer]

    @classmethod  
    def get_mode_consumer_classes(cls) -> list:
        """
        :return: The list of consumers classes
        """
        return [VolumeBoosterTradingModeConsumer]

    async def create_state(self, config: object) -> trading_modes.ModeChannelConsumer:
        return VolumeBoosterTradingModeConsumer(self)

    @classmethod
    def get_supported_exchange_types(cls) -> list:
        """
        :return: The list of supported exchange types
        """
        return [
            trading_enums.ExchangeTypes.SPOT,
            trading_enums.ExchangeTypes.FUTURE
        ]

    @staticmethod
    def is_backtestable():
        return False

    @staticmethod
    def get_is_symbol_wildcard() -> bool:
        return False


class VolumeBoosterTradingModeProducer(trading_modes.AbstractTradingModeProducer):
    """
    Producer for Volume Booster Trading Mode - self-initiating like Market Making
    """
    
    def __init__(self, channel, config, trading_mode, exchange_manager):
        super().__init__(channel, config, trading_mode, exchange_manager)
        self.healthy = False
        self.is_initialized = False
        self.init_task = None
    
    async def start(self) -> None:
        """Start the producer and initialize volume boosting"""
        await super().start()
        self.healthy = True
        if not self.is_initialized:
            self.logger.info("Starting Volume Booster initialization...")
            # Schedule initialization - similar to market making
            self.init_task = asyncio.create_task(self._initialize_volume_booster())
    
    async def _initialize_volume_booster(self):
        """Initialize volume boosting - similar to market making approach"""
        try:
            # Check if we can start (portfolio exists, exchange is ready, etc.)
            can_start = (
                not trading_api.get_is_backtesting(self.exchange_manager)
                or trading_api.is_mark_price_initialized(self.exchange_manager, symbol=self.trading_mode.symbol)
            ) and (
                trading_api.get_portfolio(self.exchange_manager) != {}
                or trading_api.is_trader_simulated(self.exchange_manager)
            )
            
            if can_start:
                self.logger.info(f"Initializing Volume Booster for {self.trading_mode.symbol}")
                # Directly start the consumer
                consumers = self.trading_mode.get_trading_mode_consumers()
                if consumers:
                    consumer = consumers[0]  # Get the first (and only) consumer
                    self.is_initialized = True
                    # Start the consumer directly - no need for signals
                    await consumer.inner_start()
                    self.logger.info("Volume Booster consumer started successfully")
                else:
                    self.logger.error("No consumers found for Volume Booster")
            else:
                self.logger.info("Cannot start Volume Booster yet, retrying in 5 seconds...")
                # Retry after delay
                await asyncio.sleep(5)
                if not self.should_stop and self.healthy:
                    self.init_task = asyncio.create_task(self._initialize_volume_booster())
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize volume booster: {e}", exc_info=True)
            # Retry on error
            if not self.should_stop and self.healthy:
                await asyncio.sleep(5)
                self.init_task = asyncio.create_task(self._initialize_volume_booster())
    
    async def stop(self) -> None:
        """Stop the producer"""
        self.healthy = False
        if self.init_task and not self.init_task.done():
            self.init_task.cancel()
            try:
                await self.init_task
            except asyncio.CancelledError:
                pass
        await super().stop()

    async def set_final_eval(self, matrix_id: str, cryptocurrency: str, symbol: str, time_frame):
        # Volume booster doesn't use evaluator signals - it's self-initiating
        pass


class VolumeBoosterTradingModeConsumer(trading_modes.AbstractTradingModeConsumer):
    """
    Consumer for Volume Booster Trading Mode
    """

    def __init__(self, trading_mode):
        super().__init__(trading_mode)
        
        # Volume tracking
        self.current_volume = 0
        self.target_volume = 0
        self.volume_start_time = None
        
        # Control flags
        self.is_running = False
        self.should_stop = False
        
        # Task management
        self.volume_task = None
        self.symbol_tasks = {}
        
        # Configuration cache
        self._config_cache = {}
        self._last_config_update = 0
        
        # Statistics
        self.orders_placed = 0
        self.successful_orders = 0
        self.failed_orders = 0
        self.consecutive_failures = 0
        self.last_failure_time = 0

    async def inner_start(self) -> bool:
        """
        Start the volume booster with enhanced configuration loading
        """
        try:
            # Prevent duplicate starts
            if self.is_running:
                self.logger.info("Volume Booster is already running")
                return True
                
            self.logger.info("Volume Booster inner_start() called")
            
            # Load and cache configuration
            self._update_config_cache()
            
            enabled = self._get_config(ENABLE_VOLUME_BOOSTER_KEY, DEFAULT_ENABLE_VOLUME_BOOSTER)
            self.logger.info(f"Volume Booster enabled: {enabled}")
            
            if not enabled:
                self.logger.warning("Volume Booster is disabled in configuration")
                return False
            
            # Check if exchange manager is properly initialized
            if not self.exchange_manager:
                self.logger.error("Exchange manager not available")
                return False
                
            if not hasattr(self.exchange_manager, 'exchange_config') or not self.exchange_manager.exchange_config:
                self.logger.error("Exchange configuration not available")
                return False
                
            symbols = list(self.exchange_manager.exchange_config.traded_symbol_pairs)
            if not symbols:
                self.logger.error("No symbols configured for trading")
                return False
            
            # Initialize volume booster
            self.target_volume = self._get_config(VOLUME_TARGET_KEY, DEFAULT_VOLUME_TARGET)
            # Ensure target_volume is never None
            if self.target_volume is None:
                self.target_volume = DEFAULT_VOLUME_TARGET
            self.current_volume = 0
            self.volume_start_time = time.time()
            self.is_running = True
            self.should_stop = False
            
            # Reset statistics
            self.orders_placed = 0
            self.successful_orders = 0
            self.failed_orders = 0
            self.consecutive_failures = 0
            self.last_failure_time = 0
            
            self.logger.info(f"Volume Booster configuration loaded:")
            self.logger.info(f"  - Target Volume: {self.target_volume}")
            self.logger.info(f"  - Order Type: {self._get_config(ORDER_TYPE_KEY, DEFAULT_ORDER_TYPE)}")
            self.logger.info(f"  - Min/Max Buy: {self._get_config(MIN_BUY_AMOUNT_KEY, DEFAULT_MIN_BUY_AMOUNT)}-{self._get_config(MAX_BUY_AMOUNT_KEY, DEFAULT_MAX_BUY_AMOUNT)}")
            self.logger.info(f"  - Min/Max Sell: {self._get_config(MIN_SELL_AMOUNT_KEY, DEFAULT_MIN_SELL_AMOUNT)}-{self._get_config(MAX_SELL_AMOUNT_KEY, DEFAULT_MAX_SELL_AMOUNT)}")
            self.logger.info(f"  - Trade Frequency: {self._get_config(TRADE_FREQUENCY_MIN_KEY, DEFAULT_TRADE_FREQUENCY_MIN)}-{self._get_config(TRADE_FREQUENCY_MAX_KEY, DEFAULT_TRADE_FREQUENCY_MAX)}s")
            self.logger.info(f"  - Symbols: {symbols}")
            
            # Check if trader is enabled (either real or simulated)
            if not self.exchange_manager.trader or not (self.exchange_manager.trader.is_enabled or trading_api.is_trader_simulated(self.exchange_manager)):
                self.logger.error("Trading is not enabled (neither real nor simulated trading)")
                self.is_running = False
                return False
            
            # Start the volume boosting task
            if self.volume_task is None or self.volume_task.done():
                self.logger.info("Starting volume booster main loop...")
                self.volume_task = asyncio.create_task(self._volume_booster_loop())
            else:
                self.logger.info("Volume booster task already running")
            
            self.logger.info("Volume Booster started successfully!")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to start Volume Booster: {e}", exc_info=True)
            self.is_running = False
            return False
            
    def _update_config_cache(self):
        """Update the configuration cache"""
        self._config_cache = dict(self.trading_mode.trading_config)
        self._last_config_update = time.time()
        
    def _get_config(self, key: str, default_value=None):
        """Get configuration value with caching"""
        value = self._config_cache.get(key, default_value)
        # Ensure we never return None for numeric config values
        if value is None and default_value is not None:
            value = default_value
        return value

    async def stop(self):
        """
        Stop the volume booster with proper cleanup
        """
        try:
            self.logger.info("Stopping Volume Booster...")
            self.is_running = False
            self.should_stop = True
            
            # Cancel main volume task
            if self.volume_task and not self.volume_task.done():
                self.volume_task.cancel()
                try:
                    await self.volume_task
                except asyncio.CancelledError:
                    pass
            
            # Cancel individual symbol tasks
            for symbol, task in self.symbol_tasks.items():
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self.symbol_tasks.clear()
            
            # Log final statistics
            if self.volume_start_time:
                runtime = time.time() - self.volume_start_time
                self._log_final_statistics(runtime)
            
            await super().stop()
            self.logger.info("Volume Booster stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping Volume Booster: {e}")
            
    def _log_final_statistics(self, runtime: float):
        """Log final session statistics"""
        try:
            success_rate = (self.successful_orders / self.orders_placed * 100) if self.orders_placed > 0 else 0
            progress_percent = (self.current_volume / self.target_volume * 100) if self.target_volume > 0 else 0
            
            self.logger.info("Volume Booster Session Statistics:")
            self.logger.info(f"  - Runtime: {runtime:.1f} seconds")
            self.logger.info(f"  - Volume Progress: {self.current_volume:.2f}/{self.target_volume:.2f} ({progress_percent:.1f}%)")
            self.logger.info(f"  - Orders Placed: {self.orders_placed}")
            self.logger.info(f"  - Successful Orders: {self.successful_orders}")
            self.logger.info(f"  - Failed Orders: {self.failed_orders}")
            self.logger.info(f"  - Success Rate: {success_rate:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error logging statistics: {e}")

    async def _volume_booster_loop(self):
        """
        Enhanced main loop for volume boosting with better management
        """
        try:
            self.logger.info("Volume Booster main loop started")
            
            while self.is_running and not self.should_stop and self.current_volume < self.target_volume:
                # Refresh configuration periodically (every 60 seconds)
                if time.time() - self._last_config_update > 60:
                    self._update_config_cache()
                    
                # Check if volume booster is still enabled
                if not self._get_config(ENABLE_VOLUME_BOOSTER_KEY, DEFAULT_ENABLE_VOLUME_BOOSTER):
                    self.logger.info("Volume Booster disabled via configuration")
                    break
                
                symbols = list(self.exchange_manager.exchange_config.traded_symbol_pairs)
                if not symbols:
                    self.logger.warning("No symbols configured for trading")
                    await asyncio.sleep(5)
                    continue
                
                # Process each symbol
                for symbol in symbols:
                    if (not self.is_running or self.should_stop or 
                        (self.current_volume is not None and self.target_volume is not None and 
                         self.current_volume >= self.target_volume)):
                        break
                        
                    try:
                        # Check if we should slow down due to consecutive failures
                        if self.consecutive_failures >= 3:
                            backoff_time = min(30, self.consecutive_failures * 2)
                            self.logger.warning(f"Too many consecutive failures ({self.consecutive_failures}), backing off for {backoff_time}s")
                            await asyncio.sleep(backoff_time)
                            
                        await self._execute_volume_boost_trade(symbol)
                        
                        # Dynamic wait time based on configuration and recent failures
                        min_freq = self._get_config(TRADE_FREQUENCY_MIN_KEY, DEFAULT_TRADE_FREQUENCY_MIN)
                        max_freq = self._get_config(TRADE_FREQUENCY_MAX_KEY, DEFAULT_TRADE_FREQUENCY_MAX)
                        
                        # Ensure min_freq <= max_freq
                        if min_freq > max_freq:
                            min_freq, max_freq = max_freq, min_freq
                        
                        # Increase wait time if we've had recent failures
                        failure_multiplier = 1.0
                        if self.consecutive_failures > 0:
                            failure_multiplier = 1 + (self.consecutive_failures * 0.5)
                            
                        wait_time = random.uniform(min_freq, max_freq) * failure_multiplier
                        await asyncio.sleep(wait_time)
                        
                    except asyncio.CancelledError:
                        self.logger.info(f"Volume boost task for {symbol} cancelled")
                        break
                    except Exception as e:
                        self.failed_orders += 1
                        self.logger.warning(f"Error in volume boost trade for {symbol}: {e}")
                        await asyncio.sleep(2)  # Brief pause on error
            
            # Check completion status
            if (self.current_volume is not None and self.target_volume is not None and 
                self.current_volume >= self.target_volume):
                self.logger.info(f"🎯 Volume target reached! {self.current_volume:.2f}/{self.target_volume:.2f}")
            elif self.should_stop:
                self.logger.info("Volume Booster stopped by user request")
            else:
                self.logger.info("Volume Booster loop ended")
                
        except asyncio.CancelledError:
            self.logger.info("Volume booster main loop cancelled")
        except Exception as e:
            self.logger.error(f"Critical error in volume booster loop: {e}")
        finally:
            self.is_running = False

    async def _execute_volume_boost_trade(self, symbol: str):
        """
        Execute a single volume boost trade
        """
        try:
            self.logger.debug(f"Attempting to execute volume boost trade for {symbol}")
            
            # Defensive checks for None values to prevent comparison errors
            if self.current_volume is None:
                self.logger.warning("current_volume is None, resetting to 0")
                self.current_volume = 0
            if self.target_volume is None:
                self.logger.warning("target_volume is None, setting to default")
                self.target_volume = DEFAULT_VOLUME_TARGET
            
            # Check if target volume is reached
            if (self.current_volume is not None and self.target_volume is not None and 
                self.current_volume >= self.target_volume):
                self.logger.info(f"Target volume {self.target_volume} reached! Current: {self.current_volume}")
                self.is_running = False
                return
            
            # Get current price and symbol market info
            _, _, _, current_price, symbol_market = await trading_personal_data.get_pre_order_data(
                self.exchange_manager,
                symbol=symbol,
                timeout=30  # 30 second timeout for price fetching
            )
            
            if current_price is None:
                self.logger.warning(f"No price data available for {symbol}")
                return
            
            # Get minimum order limits from symbol market data
            if symbol_market:
                limits = symbol_market.get(trading_enums.ExchangeConstantsMarketStatusColumns.LIMITS.value, {})
                amount_limits = limits.get("amount") if limits else None
                cost_limits = limits.get("cost") if limits else None
                min_quantity = amount_limits.get("min", 0) if amount_limits else 0
                min_cost = cost_limits.get("min", 0) if cost_limits else 0
            else:
                min_quantity = 0
                min_cost = 0
            
            # Ensure values are not None (fallback to 0)
            min_quantity = min_quantity if min_quantity is not None else 0
            min_cost = min_cost if min_cost is not None else 0
            
            # Decide whether to buy or sell (random choice)
            is_buy = random.choice([True, False])
            
            # Get amount range
            if is_buy:
                min_amount = max(self._get_config(MIN_BUY_AMOUNT_KEY, DEFAULT_MIN_BUY_AMOUNT), min_cost)
                max_amount = self._get_config(MAX_BUY_AMOUNT_KEY, DEFAULT_MAX_BUY_AMOUNT)
            else:
                min_amount = max(self._get_config(MIN_SELL_AMOUNT_KEY, DEFAULT_MIN_SELL_AMOUNT), min_cost)
                max_amount = self._get_config(MAX_SELL_AMOUNT_KEY, DEFAULT_MAX_SELL_AMOUNT)
            
            # Ensure min is not greater than max
            if min_amount > max_amount:
                min_amount = max_amount
            
            # Random amount within range with better precision handling
            quote_amount = random.uniform(min_amount, max_amount)
            quantity = decimal.Decimal(str(quote_amount)) / current_price
            
            # Apply minimum quantity if exists
            if min_quantity and quantity < decimal.Decimal(str(min_quantity)):
                quantity = decimal.Decimal(str(min_quantity))
                quote_amount = float(quantity * current_price)
            
            # Round quantity to exchange precision to avoid rejection
            if symbol_market:
                precision = symbol_market.get(trading_enums.ExchangeConstantsMarketStatusColumns.PRECISION.value, {})
                amount_precision = precision.get("amount", 8) if precision else 8
                # Round to the appropriate decimal places
                quantity = quantity.quantize(decimal.Decimal('0.1') ** amount_precision)
                quote_amount = float(quantity * current_price)
            
            # Final safety check - ensure minimum order value
            min_order_value = max(min_cost, 1.0)  # At least $1 or exchange minimum
            if quote_amount < min_order_value:
                self.logger.debug(f"Order value {quote_amount} too small (min: {min_order_value}), skipping {symbol}")
                return
            
            # Enhanced balance checking with more conservative buffers
            base_currency, quote_currency = symbol.split("/")
            
            if is_buy:
                # Check quote currency balance for buying with larger buffer
                available_quote = trading_api.get_portfolio_currency(self.exchange_manager, quote_currency).available
                required_amount = decimal.Decimal(str(quote_amount * 1.05))  # Add 5% buffer for fees and slippage
                if available_quote is None:
                    self.logger.warning(f"Could not get {quote_currency} balance")
                    return
                if available_quote < required_amount:
                    self.logger.debug(f"Insufficient {quote_currency} balance: {available_quote} < {required_amount}")
                    return
                    
                # Additional check: ensure we're not using more than 80% of available balance
                max_usable = available_quote * decimal.Decimal("0.8")
                if required_amount > max_usable:
                    # Reduce the order size to fit within safe limits
                    safe_amount = float(max_usable * decimal.Decimal("0.95"))
                    quantity = decimal.Decimal(str(safe_amount)) / current_price
                    quote_amount = safe_amount
                    self.logger.debug(f"Reduced order size to {safe_amount} {quote_currency} for safety")
            else:
                # Check base currency balance for selling with larger buffer
                available_base = trading_api.get_portfolio_currency(self.exchange_manager, base_currency).available
                required_quantity = quantity * decimal.Decimal("1.05")  # Add 5% buffer
                if available_base is None:
                    self.logger.warning(f"Could not get {base_currency} balance")
                    return
                if available_base < required_quantity:
                    self.logger.debug(f"Insufficient {base_currency} balance: {available_base} < {required_quantity}")
                    return
                    
                # Additional check: ensure we're not using more than 80% of available balance
                max_usable = available_base * decimal.Decimal("0.8")
                if required_quantity > max_usable:
                    # Reduce the order size to fit within safe limits
                    quantity = max_usable * decimal.Decimal("0.95")
                    quote_amount = float(quantity * current_price)
                    self.logger.debug(f"Reduced order size to {quantity} {base_currency} for safety")
            
            # Create market order only
            order = trading_personal_data.create_order_instance(
                trader=self.exchange_manager.trader,
                order_type=trading_enums.TraderOrderType.BUY_MARKET if is_buy else trading_enums.TraderOrderType.SELL_MARKET,
                symbol=symbol,
                current_price=current_price,
                quantity=quantity,
                price=current_price
            )
            order_price = current_price
            
            # Disable instant fill to avoid issues in simulator (like market making does)
            order.allow_instant_fill = False
            
            # Execute the order with better monitoring
            action = "BUY" if is_buy else "SELL"
            self.logger.info(f"Creating {action} order: {quantity:.6f} {base_currency} at ~{order_price:.6f} {quote_currency}")
            
            created_order = await self.trading_mode.create_order(order)
            self.orders_placed += 1
            
            if created_order:
                # Wait a moment for order to be processed
                await asyncio.sleep(0.5)
                
                # Check order status to see if it was actually filled
                if hasattr(created_order, 'status'):
                    order_status = created_order.status
                    self.logger.debug(f"Order status after creation: {order_status}")
                    
                    if order_status in [trading_enums.OrderStatus.FILLED, trading_enums.OrderStatus.PARTIALLY_FILLED]:
                        self.successful_orders += 1
                        self.consecutive_failures = 0  # Reset failure counter on success
                        # Update volume tracking (use actual filled amount if available)
                        filled_quantity = getattr(created_order, 'filled_quantity', quantity)
                        filled_price = getattr(created_order, 'filled_price', order_price)
                        order_value = float(filled_quantity * filled_price)
                        self.current_volume += order_value
                        
                        progress_percent = ((self.current_volume / self.target_volume) * 100 
                                          if self.target_volume and self.target_volume > 0 else 0)
                        self.logger.info(
                            f"✅ Volume Boost {action}: {filled_quantity:.6f} {base_currency} "
                            f"at {filled_price:.6f} {quote_currency} "
                            f"(Progress: {self.current_volume:.2f}/{self.target_volume:.2f} = {progress_percent:.1f}%)"
                        )
                    elif order_status in [trading_enums.OrderStatus.CANCELED, trading_enums.OrderStatus.REJECTED]:
                        self.failed_orders += 1
                        self.consecutive_failures += 1
                        self.last_failure_time = time.time()
                        self.logger.warning(f"❌ Order {action} was {order_status.value} by exchange for {symbol}")
                    else:
                        # Order is still pending/open
                        self.successful_orders += 1  # Count as successful creation even if pending
                        self.consecutive_failures = 0  # Reset failure counter on successful creation
                        order_value = float(quantity * order_price)
                        self.current_volume += order_value
                        
                        progress_percent = ((self.current_volume / self.target_volume) * 100 
                                          if self.target_volume and self.target_volume > 0 else 0)
                        self.logger.info(
                            f"⏳ Volume Boost {action}: {quantity:.6f} {base_currency} "
                            f"at {order_price:.6f} {quote_currency} [Status: {order_status.value}] "
                            f"(Progress: {self.current_volume:.2f}/{self.target_volume:.2f} = {progress_percent:.1f}%)"
                        )
                else:
                    # Fallback for orders without status attribute
                    self.successful_orders += 1
                    self.consecutive_failures = 0  # Reset failure counter on successful creation
                    order_value = float(quantity * order_price)
                    self.current_volume += order_value
                    
                    progress_percent = ((self.current_volume / self.target_volume) * 100 
                                      if self.target_volume and self.target_volume > 0 else 0)
                    self.logger.info(
                        f"✅ Volume Boost {action}: {quantity:.6f} {base_currency} "
                        f"at {order_price:.6f} {quote_currency} "
                        f"(Progress: {self.current_volume:.2f}/{self.target_volume:.2f} = {progress_percent:.1f}%)"
                    )
            else:
                self.failed_orders += 1
                self.consecutive_failures += 1
                self.last_failure_time = time.time()
                self.logger.warning(f"❌ Order creation returned None for {symbol} {action}")
            
        except trading_errors.MissingMinimalExchangeTradeVolume as e:
            self.failed_orders += 1
            self.consecutive_failures += 1
            self.last_failure_time = time.time()
            self.logger.debug(f"Trade amount too small for {symbol}: {e}")
        except trading_errors.NotSupported as e:
            self.failed_orders += 1
            self.consecutive_failures += 1
            self.last_failure_time = time.time()
            self.logger.warning(f"Order type not supported for {symbol}: {e}")
        except trading_errors.InsufficientFunds as e:
            self.failed_orders += 1
            self.consecutive_failures += 1
            self.last_failure_time = time.time()
            self.logger.warning(f"Insufficient funds for {symbol} {action}: {e}")
        except Exception as e:
            self.failed_orders += 1
            self.consecutive_failures += 1
            self.last_failure_time = time.time()
            error_msg = str(e).lower()
            
            # Provide more specific error messages
            if "insufficient" in error_msg or "balance" in error_msg:
                self.logger.warning(f"Balance issue for {symbol} {action}: {e}")
            elif "canceled" in error_msg or "cancelled" in error_msg:
                self.logger.warning(f"Order canceled by exchange for {symbol} {action}: {e}")
            elif "reject" in error_msg or "invalid" in error_msg:
                self.logger.warning(f"Order rejected by exchange for {symbol} {action}: {e}")
            elif "rate" in error_msg or "limit" in error_msg:
                self.logger.warning(f"Rate limit reached for {symbol}: {e}")
                await asyncio.sleep(10)  # Longer pause for rate limits
                return
            else:
                self.logger.error(f"Unexpected error executing volume boost trade for {symbol}: {e}", exc_info=True)
            
            # Add a longer pause on errors to prevent spam
            await asyncio.sleep(5)

    async def get_status(self) -> dict:
        """
        Get current status of the volume booster
        """
        progress_percent = (self.current_volume / self.target_volume * 100) if self.target_volume > 0 else 0
        return {
            "is_running": self.is_running,
            "current_volume": self.current_volume,
            "target_volume": self.target_volume,
            "progress_percent": progress_percent,
            "remaining_volume": max(0, self.target_volume - self.current_volume)
        }

    async def reset_volume(self):
        """
        Reset the volume counter
        """
        self.current_volume = 0
        self.logger.info("Volume counter reset")

    async def update_target_volume(self, new_target: float):
        """
        Update the target volume
        """
        old_target = self.target_volume
        self.target_volume = new_target
        self.logger.info(f"Target volume updated from {old_target} to {new_target}")

    async def internal_callback(self, trading_mode_name: str, cryptocurrency: str, symbol: str, signal: str,
                              **kwargs):
        """
        Handle trading signals (not used - volume booster is self-initiating)
        """
        pass
