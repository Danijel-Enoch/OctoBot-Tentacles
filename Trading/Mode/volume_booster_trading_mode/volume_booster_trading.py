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

import octobot_commons.constants as commons_constants
import octobot_commons.enums as commons_enums
import octobot_commons.pretty_printer as pretty_printer
import octobot_trading.constants as trading_constants
import octobot_trading.api as trading_api
import octobot_trading.modes as trading_modes
import octobot_trading.enums as trading_enums
import octobot_trading.personal_data as trading_personal_data
import octobot_trading.errors as trading_errors


class VolumeBoosterTradingMode(trading_modes.AbstractTradingMode):
    """
    Volume Booster Trading Mode - Rapidly executes buy and sell orders to boost volume
    """

    def init_user_inputs(self, inputs: dict) -> None:
        """
        Called right before starting the tentacle, should define all the tentacle's user inputs unless
        those are defined somewhere else.
        """
        self.UI.user_input(
            "volume_target", commons_enums.UserInputTypes.FLOAT, 10000, inputs,
            min_val=1,
            title="Volume Target: Target volume to achieve (in base currency units)",
        )
        
        self.UI.user_input(
            "order_type", commons_enums.UserInputTypes.OPTIONS, "limit", inputs,
            options=["market", "limit"],
            title="Order Type: Choose between market orders (immediate execution) or limit orders",
        )
        
        self.UI.user_input(
            "trade_frequency_min", commons_enums.UserInputTypes.FLOAT, 1.0, inputs,
            min_val=0.1, max_val=3600,
            title="Minimum Trade Frequency: Minimum seconds between trades",
        )
        
        self.UI.user_input(
            "trade_frequency_max", commons_enums.UserInputTypes.FLOAT, 5.0, inputs,
            min_val=0.1, max_val=3600,
            title="Maximum Trade Frequency: Maximum seconds between trades",
        )
        
        self.UI.user_input(
            "min_buy_amount", commons_enums.UserInputTypes.FLOAT, 10, inputs,
            min_val=0.01,
            title="Minimum Buy Amount: Minimum amount to buy in quote currency (e.g., USDT)",
        )
        
        self.UI.user_input(
            "max_buy_amount", commons_enums.UserInputTypes.FLOAT, 100, inputs,
            min_val=0.01,
            title="Maximum Buy Amount: Maximum amount to buy in quote currency (e.g., USDT)",
        )
        
        self.UI.user_input(
            "min_sell_amount", commons_enums.UserInputTypes.FLOAT, 10, inputs,
            min_val=0.01,
            title="Minimum Sell Amount: Minimum amount to sell in quote currency (e.g., USDT)",
        )
        
        self.UI.user_input(
            "max_sell_amount", commons_enums.UserInputTypes.FLOAT, 100, inputs,
            min_val=0.01,
            title="Maximum Sell Amount: Maximum amount to sell in quote currency (e.g., USDT)",
        )
        
        self.UI.user_input(
            "price_offset_percent", commons_enums.UserInputTypes.FLOAT, 0.1, inputs,
            min_val=0, max_val=5,
            title="Price Offset Percent: For limit orders, percentage offset from current price (0.1 = 0.1%)",
        )
        
        self.UI.user_input(
            "enable_volume_booster", commons_enums.UserInputTypes.BOOLEAN, True, inputs,
            title="Enable Volume Booster: Start/Stop the volume boosting activity",
        )
        
        # Add validation for configuration
        self._validate_configuration(inputs)

    def _validate_configuration(self, inputs: dict):
        """
        Validate user configuration inputs
        """
        # Ensure min values are less than max values
        min_buy = inputs.get("min_buy_amount", 10)
        max_buy = inputs.get("max_buy_amount", 100)
        min_sell = inputs.get("min_sell_amount", 10)
        max_sell = inputs.get("max_sell_amount", 100)
        min_freq = inputs.get("trade_frequency_min", 1.0)
        max_freq = inputs.get("trade_frequency_max", 5.0)
        
        if min_buy > max_buy:
            self.logger.warning(f"Minimum buy amount ({min_buy}) is greater than maximum ({max_buy})")
        if min_sell > max_sell:
            self.logger.warning(f"Minimum sell amount ({min_sell}) is greater than maximum ({max_sell})")
        if min_freq > max_freq:
            self.logger.warning(f"Minimum frequency ({min_freq}) is greater than maximum ({max_freq})")
        
        volume_target = inputs.get("volume_target", 10000)
        if volume_target <= 0:
            self.logger.error("Volume target must be greater than 0")

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


class VolumeBoosterTradingModeConsumer(trading_modes.AbstractTradingModeConsumer):
    """
    Consumer for Volume Booster Trading Mode
    """

    def __init__(self, trading_mode):
        super().__init__(trading_mode)
        self.current_volume = 0
        self.target_volume = 0
        self.is_running = False
        self.volume_task = None

    async def inner_start(self) -> bool:
        """
        Start the volume booster
        """
        if self.trading_mode.trading_config.get("enable_volume_booster", True):
            self.target_volume = self.trading_mode.trading_config.get("volume_target", 10000)
            self.is_running = True
            
            # Start the volume boosting task
            if self.volume_task is None or self.volume_task.done():
                self.volume_task = asyncio.create_task(self._volume_booster_loop())
            
            self.logger.info(f"Volume Booster started with target volume: {self.target_volume}")
            return True
        return False

    async def stop(self):
        """
        Stop the volume booster
        """
        self.is_running = False
        if self.volume_task and not self.volume_task.done():
            self.volume_task.cancel()
        self.logger.info("Volume Booster stopped")

    async def _volume_booster_loop(self):
        """
        Main loop for volume boosting
        """
        try:
            while self.is_running and self.current_volume < self.target_volume:
                for symbol in self.exchange_manager.exchange_config.traded_symbol_pairs:
                    if not self.is_running:
                        break
                    
                    try:
                        await self._execute_volume_boost_trade(symbol)
                        
                        # Wait for next trade
                        min_freq = self.trading_mode.trading_config.get("trade_frequency_min", 1.0)
                        max_freq = self.trading_mode.trading_config.get("trade_frequency_max", 5.0)
                        wait_time = random.uniform(min_freq, max_freq)
                        await asyncio.sleep(wait_time)
                        
                    except Exception as e:
                        self.logger.error(f"Error in volume boost trade for {symbol}: {e}")
                        await asyncio.sleep(1)  # Brief pause on error
                        
        except asyncio.CancelledError:
            self.logger.info("Volume booster loop cancelled")
        except Exception as e:
            self.logger.error(f"Error in volume booster loop: {e}")

    async def _execute_volume_boost_trade(self, symbol: str):
        """
        Execute a single volume boost trade
        """
        try:
            # Check if target volume is reached
            if self.current_volume >= self.target_volume:
                self.logger.info(f"Target volume {self.target_volume} reached! Current: {self.current_volume}")
                self.is_running = False
                return
            
            # Get current price
            ticker = await trading_api.get_symbol_ticker(self.exchange_manager, symbol)
            if not ticker:
                self.logger.warning(f"No ticker data for {symbol}")
                return
            
            current_price = decimal.Decimal(str(ticker[trading_enums.ExchangeConstantsTickersColumns.LAST.value]))
            
            # Get symbol info for minimum order size validation
            symbol_market = self.exchange_manager.exchange.get_market_status(symbol)
            if symbol_market:
                min_quantity = symbol_market.get("limits", {}).get("amount", {}).get("min", 0)
                min_cost = symbol_market.get("limits", {}).get("cost", {}).get("min", 0)
            else:
                min_quantity = 0
                min_cost = 0
            
            # Decide whether to buy or sell (random choice)
            is_buy = random.choice([True, False])
            
            # Get amount range
            if is_buy:
                min_amount = max(self.trading_mode.trading_config.get("min_buy_amount", 10), min_cost)
                max_amount = self.trading_mode.trading_config.get("max_buy_amount", 100)
            else:
                min_amount = max(self.trading_mode.trading_config.get("min_sell_amount", 10), min_cost)
                max_amount = self.trading_mode.trading_config.get("max_sell_amount", 100)
            
            # Ensure min is not greater than max
            if min_amount > max_amount:
                min_amount = max_amount
            
            # Random amount within range
            quote_amount = random.uniform(min_amount, max_amount)
            quantity = decimal.Decimal(str(quote_amount)) / current_price
            
            # Apply minimum quantity if exists
            if min_quantity and quantity < decimal.Decimal(str(min_quantity)):
                quantity = decimal.Decimal(str(min_quantity))
                quote_amount = float(quantity * current_price)
            
            # Check if we have enough balance
            portfolio = self.exchange_manager.exchange_personal_data.portfolio_manager.portfolio
            base_currency, quote_currency = symbol.split("/")
            
            if is_buy:
                # Check quote currency balance for buying
                available_quote = portfolio.get_currency_portfolio(quote_currency).available
                required_amount = decimal.Decimal(str(quote_amount * 1.01))  # Add 1% buffer for fees
                if available_quote < required_amount:
                    self.logger.debug(f"Insufficient {quote_currency} balance: {available_quote} < {required_amount}")
                    return
            else:
                # Check base currency balance for selling
                available_base = portfolio.get_currency_portfolio(base_currency).available
                required_quantity = quantity * decimal.Decimal("1.01")  # Add 1% buffer
                if available_base < required_quantity:
                    self.logger.debug(f"Insufficient {base_currency} balance: {available_base} < {required_quantity}")
                    return
            
            # Create order
            order_type = self.trading_mode.trading_config.get("order_type", "limit")
            
            if order_type == "market":
                # Market order
                order = trading_personal_data.create_order_instance(
                    trader=self.exchange_manager.trader,
                    order_type=trading_enums.TraderOrderType.BUY_MARKET if is_buy else trading_enums.TraderOrderType.SELL_MARKET,
                    symbol=symbol,
                    current_price=current_price,
                    quantity=quantity,
                    price=current_price
                )
                order_price = current_price
            else:
                # Limit order with price offset
                price_offset = self.trading_mode.trading_config.get("price_offset_percent", 0.1) / 100
                
                if is_buy:
                    # Buy slightly below current price
                    order_price = current_price * (1 - decimal.Decimal(str(price_offset)))
                else:
                    # Sell slightly above current price
                    order_price = current_price * (1 + decimal.Decimal(str(price_offset)))
                
                order = trading_personal_data.create_order_instance(
                    trader=self.exchange_manager.trader,
                    order_type=trading_enums.TraderOrderType.BUY_LIMIT if is_buy else trading_enums.TraderOrderType.SELL_LIMIT,
                    symbol=symbol,
                    current_price=current_price,
                    quantity=quantity,
                    price=order_price
                )
            
            # Execute the order
            await self.exchange_manager.trader.create_order(order)
            
            # Update volume tracking (use order value for consistent tracking)
            order_value = float(quantity * order_price)
            self.current_volume += order_value
            
            action = "BUY" if is_buy else "SELL"
            progress_percent = (self.current_volume / self.target_volume) * 100
            self.logger.info(
                f"Volume Boost {action}: {quantity:.6f} {base_currency} "
                f"at {order_price:.6f} {quote_currency} "
                f"(Progress: {self.current_volume:.2f}/{self.target_volume:.2f} = {progress_percent:.1f}%)"
            )
            
        except trading_errors.MissingMinimalExchangeTradeVolume as e:
            self.logger.debug(f"Trade amount too small for {symbol}: {e}")
        except trading_errors.NotSupported as e:
            self.logger.warning(f"Order type not supported for {symbol}: {e}")
        except Exception as e:
            self.logger.error(f"Error executing volume boost trade for {symbol}: {e}")
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
        Handle trading signals (not used in volume booster mode)
        This mode operates independently of evaluator signals
        """
        pass
