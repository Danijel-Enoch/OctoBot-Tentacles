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

"""
Configuration validation utilities for Volume Booster Trading Mode
"""

def validate_volume_booster_config(config: dict) -> tuple[bool, list[str]]:
    """
    Validate Volume Booster configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required keys
    required_keys = [
        "volume_target",
        "order_type", 
        "trade_frequency_min",
        "trade_frequency_max",
        "min_buy_amount",
        "max_buy_amount",
        "min_sell_amount", 
        "max_sell_amount"
    ]
    
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required configuration: {key}")
    
    if errors:
        return False, errors
        
    # Validate ranges
    if config["trade_frequency_min"] >= config["trade_frequency_max"]:
        errors.append("trade_frequency_min must be less than trade_frequency_max")
        
    if config["min_buy_amount"] >= config["max_buy_amount"]:
        errors.append("min_buy_amount must be less than max_buy_amount")
        
    if config["min_sell_amount"] >= config["max_sell_amount"]:
        errors.append("min_sell_amount must be less than max_sell_amount")
        
    # Validate values
    if config["volume_target"] <= 0:
        errors.append("volume_target must be greater than 0")
        
    if config["order_type"] != "market":
        errors.append("order_type must be 'market'")
        
    # Validate frequency ranges
    if config["trade_frequency_min"] < 0.1:
        errors.append("trade_frequency_min must be at least 0.1 seconds")
        
    if config["trade_frequency_max"] > 3600:
        errors.append("trade_frequency_max must be at most 3600 seconds")
        
    # Validate amounts
    for amount_key in ["min_buy_amount", "max_buy_amount", "min_sell_amount", "max_sell_amount"]:
        if config[amount_key] <= 0:
            errors.append(f"{amount_key} must be greater than 0")
            
    # Validate price offset if present
    if "price_offset_percent" in config:
        if config["price_offset_percent"] < 0 or config["price_offset_percent"] > 10:
            errors.append("price_offset_percent must be between 0 and 10")
    
    return len(errors) == 0, errors


def get_recommended_config(exchange_name: str = "binance") -> dict:
    """
    Get recommended configuration based on exchange
    
    Args:
        exchange_name: Name of the exchange
        
    Returns:
        Recommended configuration dictionary
    """
    # Base configuration
    base_config = {
        "volume_target": 10000,
        "order_type": "market",
        "trade_frequency_min": 2.0,
        "trade_frequency_max": 8.0,
        "min_buy_amount": 25,
        "max_buy_amount": 100,
        "min_sell_amount": 25,
        "max_sell_amount": 100,
        "enable_volume_booster": True
    }
    
    # Exchange-specific adjustments
    exchange_adjustments = {
        "binance": {
            "trade_frequency_min": 1.0,  # Higher rate limits
            "trade_frequency_max": 5.0
        },
        "coinbase": {
            "trade_frequency_min": 5.0,  # More conservative
            "trade_frequency_max": 15.0,
            "price_offset_percent": 0.5
        },
        "kraken": {
            "trade_frequency_min": 3.0,
            "trade_frequency_max": 10.0,
            "price_offset_percent": 0.3
        }
    }
    
    # Apply exchange-specific settings
    if exchange_name.lower() in exchange_adjustments:
        base_config.update(exchange_adjustments[exchange_name.lower()])
    
    return base_config


def calculate_estimated_runtime(config: dict) -> dict:
    """
    Calculate estimated runtime based on configuration
    
    Args:
        config: Volume booster configuration
        
    Returns:
        Dictionary with runtime estimates
    """
    volume_target = config.get("volume_target", 10000)
    avg_trade_amount = (
        config.get("min_buy_amount", 25) + config.get("max_buy_amount", 100) +
        config.get("min_sell_amount", 25) + config.get("max_sell_amount", 100)
    ) / 4
    
    avg_frequency = (
        config.get("trade_frequency_min", 2.0) + config.get("trade_frequency_max", 8.0)
    ) / 2
    
    estimated_trades = volume_target / avg_trade_amount
    estimated_time_seconds = estimated_trades * avg_frequency
    
    return {
        "estimated_trades": int(estimated_trades),
        "estimated_runtime_seconds": int(estimated_time_seconds),
        "estimated_runtime_minutes": round(estimated_time_seconds / 60, 1),
        "estimated_runtime_hours": round(estimated_time_seconds / 3600, 2),
        "avg_trade_amount": round(avg_trade_amount, 2),
        "avg_frequency_seconds": round(avg_frequency, 1)
    }
