from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List, Optional
import json
from datetime import datetime
import math

class TradingSignalProcessorInput(BaseModel):
    """Input schema for Trading Signal Processor Tool."""
    signal_data: Dict[str, Any] = Field(
        ...,
        description="Raw signal data from TradingView or other sources in JSON format"
    )
    account_balance: float = Field(
        ...,
        description="Total account balance for position sizing calculations",
        gt=0
    )
    risk_percentage: float = Field(
        ...,
        description="Maximum risk percentage per trade (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    max_position_size: float = Field(
        ...,
        description="Maximum position size limit",
        gt=0
    )
    signal_filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional filtering criteria for signals"
    )

class TradingSignalProcessor(BaseTool):
    """Tool for processing trading signals with risk management and position sizing."""

    name: str = "TradingSignalProcessor"
    description: str = (
        "Processes trading signals from TradingView and other sources, validates signals, "
        "applies risk management rules, calculates position sizing based on account balance "
        "and risk percentage, and generates standardized trade execution orders with audit logging. "
        "Supports BUY, SELL, STOP_LOSS, and TAKE_PROFIT signal types."
    )
    args_schema: Type[BaseModel] = TradingSignalProcessorInput

    def _run(self, signal_data: Dict[str, Any], account_balance: float, 
             risk_percentage: float, max_position_size: float, 
             signal_filters: Optional[Dict[str, Any]] = None) -> str:
        try:
            timestamp = datetime.now().isoformat()
            
            # Validate and parse signal data
            processed_signal = self._validate_signal(signal_data)
            if not processed_signal["valid"]:
                return json.dumps({
                    "status": "rejected",
                    "reason": processed_signal["error"],
                    "timestamp": timestamp,
                    "original_signal": signal_data
                }, indent=2)
            
            signal = processed_signal["signal"]
            
            # Apply signal filters if provided
            if signal_filters and not self._apply_filters(signal, signal_filters):
                return json.dumps({
                    "status": "filtered",
                    "reason": "Signal did not meet filter criteria",
                    "timestamp": timestamp,
                    "signal": signal,
                    "filters_applied": signal_filters
                }, indent=2)
            
            # Calculate position size and risk management
            position_calc = self._calculate_position_size(
                signal, account_balance, risk_percentage, max_position_size
            )
            
            # Generate trade execution order
            trade_order = self._generate_trade_order(signal, position_calc)
            
            # Create audit log entry
            audit_log = {
                "timestamp": timestamp,
                "signal_source": signal.get("source", "unknown"),
                "signal_type": signal["action"],
                "symbol": signal["symbol"],
                "price": signal.get("price", 0),
                "account_balance": account_balance,
                "risk_percentage": risk_percentage,
                "calculated_position_size": position_calc["position_size"],
                "risk_amount": position_calc["risk_amount"],
                "stop_loss": signal.get("stop_loss"),
                "take_profit": signal.get("take_profit")
            }
            
            return json.dumps({
                "status": "processed",
                "trade_order": trade_order,
                "risk_management": position_calc,
                "audit_log": audit_log,
                "timestamp": timestamp
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": f"Processing failed: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "original_signal": signal_data
            }, indent=2)
    
    def _validate_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate incoming trading signal format and required fields."""
        try:
            required_fields = ["action", "symbol"]
            valid_actions = ["BUY", "SELL", "STOP_LOSS", "TAKE_PROFIT"]
            
            # Check required fields
            for field in required_fields:
                if field not in signal_data:
                    return {"valid": False, "error": f"Missing required field: {field}"}
            
            # Validate action type
            action = signal_data["action"].upper()
            if action not in valid_actions:
                return {"valid": False, "error": f"Invalid action: {action}. Must be one of {valid_actions}"}
            
            # Normalize signal data
            normalized_signal = {
                "action": action,
                "symbol": signal_data["symbol"].upper(),
                "price": float(signal_data.get("price", 0)),
                "quantity": float(signal_data.get("quantity", 0)),
                "stop_loss": float(signal_data.get("stop_loss", 0)) if signal_data.get("stop_loss") else None,
                "take_profit": float(signal_data.get("take_profit", 0)) if signal_data.get("take_profit") else None,
                "source": signal_data.get("source", "TradingView"),
                "strategy": signal_data.get("strategy", "unknown"),
                "timeframe": signal_data.get("timeframe", "unknown")
            }
            
            return {"valid": True, "signal": normalized_signal}
            
        except (ValueError, TypeError) as e:
            return {"valid": False, "error": f"Signal validation error: {str(e)}"}
    
    def _apply_filters(self, signal: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Apply filtering criteria to signals."""
        try:
            # Symbol filter
            if "allowed_symbols" in filters:
                if signal["symbol"] not in filters["allowed_symbols"]:
                    return False
            
            # Strategy filter
            if "allowed_strategies" in filters:
                if signal["strategy"] not in filters["allowed_strategies"]:
                    return False
            
            # Timeframe filter
            if "allowed_timeframes" in filters:
                if signal["timeframe"] not in filters["allowed_timeframes"]:
                    return False
            
            # Price range filter
            if "price_range" in filters and signal["price"] > 0:
                price_range = filters["price_range"]
                if "min" in price_range and signal["price"] < price_range["min"]:
                    return False
                if "max" in price_range and signal["price"] > price_range["max"]:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _calculate_position_size(self, signal: Dict[str, Any], account_balance: float, 
                               risk_percentage: float, max_position_size: float) -> Dict[str, Any]:
        """Calculate position size based on risk management rules."""
        try:
            risk_amount = account_balance * risk_percentage
            
            # Calculate position size based on stop loss if available
            if signal["stop_loss"] and signal["price"] > 0:
                if signal["action"] == "BUY":
                    price_diff = abs(signal["price"] - signal["stop_loss"])
                elif signal["action"] == "SELL":
                    price_diff = abs(signal["stop_loss"] - signal["price"])
                else:
                    price_diff = 0
                
                if price_diff > 0:
                    position_size = risk_amount / price_diff
                else:
                    # Fallback to percentage-based position sizing
                    position_size = risk_amount / signal["price"] if signal["price"] > 0 else 0
            else:
                # Default position sizing (2% rule alternative)
                position_size = risk_amount / signal["price"] if signal["price"] > 0 else 0
            
            # Apply maximum position size limit
            position_size = min(position_size, max_position_size)
            
            # Calculate effective risk
            effective_risk = position_size * abs(signal["price"] - (signal["stop_loss"] or signal["price"]))
            risk_reward_ratio = None
            
            if signal["take_profit"] and signal["stop_loss"] and signal["price"] > 0:
                risk_points = abs(signal["price"] - signal["stop_loss"])
                reward_points = abs(signal["take_profit"] - signal["price"])
                if risk_points > 0:
                    risk_reward_ratio = reward_points / risk_points
            
            return {
                "position_size": round(position_size, 6),
                "risk_amount": round(risk_amount, 2),
                "effective_risk": round(effective_risk, 2),
                "risk_reward_ratio": round(risk_reward_ratio, 2) if risk_reward_ratio else None,
                "max_position_applied": position_size >= max_position_size
            }
            
        except Exception as e:
            return {
                "position_size": 0,
                "risk_amount": 0,
                "effective_risk": 0,
                "risk_reward_ratio": None,
                "error": f"Position calculation error: {str(e)}"
            }
    
    def _generate_trade_order(self, signal: Dict[str, Any], position_calc: Dict[str, Any]) -> Dict[str, Any]:
        """Generate standardized trade execution order."""
        return {
            "order_type": "market" if signal["action"] in ["BUY", "SELL"] else "stop",
            "action": signal["action"],
            "symbol": signal["symbol"],
            "quantity": position_calc["position_size"],
            "price": signal["price"] if signal["price"] > 0 else None,
            "stop_loss": signal["stop_loss"],
            "take_profit": signal["take_profit"],
            "time_in_force": "GTC",  # Good Till Cancelled
            "order_id": f"{signal['symbol']}_{signal['action']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "strategy": signal["strategy"],
            "source": signal["source"]
        }