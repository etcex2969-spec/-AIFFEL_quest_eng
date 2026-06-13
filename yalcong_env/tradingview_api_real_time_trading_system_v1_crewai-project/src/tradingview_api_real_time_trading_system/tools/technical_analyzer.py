from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List, Optional
import json
import math

class OHLCVData(BaseModel):
    """OHLCV data point."""
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Closing price")
    volume: float = Field(..., description="Volume")
    timestamp: Optional[str] = Field(None, description="Timestamp (optional)")

class TechnicalAnalyzerInput(BaseModel):
    """Input schema for Technical Analyzer Tool."""
    ohlcv_data: List[OHLCVData] = Field(..., description="List of OHLCV data points")
    indicators: List[str] = Field(..., description="List of indicators to calculate (rsi, macd, bb, sma, ema)")
    periods: Dict[str, int] = Field(..., description="Periods for each indicator (e.g., {'rsi': 14, 'sma': 20})")
    signal_threshold: float = Field(default=0.5, description="Signal sensitivity threshold (0.0-1.0)")

class TechnicalAnalyzer(BaseTool):
    """Tool for advanced technical analysis of financial data."""

    name: str = "TechnicalAnalyzer"
    description: str = (
        "Advanced technical analysis tool that calculates trading indicators (RSI, MACD, Bollinger Bands, Moving Averages), "
        "detects chart patterns, and generates actionable trading signals with confidence levels. "
        "Supports RSI, MACD, Bollinger Bands (bb), Simple Moving Average (sma), and Exponential Moving Average (ema)."
    )
    args_schema: Type[BaseModel] = TechnicalAnalyzerInput

    def _run(self, ohlcv_data: List[OHLCVData], indicators: List[str], periods: Dict[str, int], signal_threshold: float = 0.5) -> str:
        try:
            # Extract price data
            closes = [float(candle.close) for candle in ohlcv_data]
            highs = [float(candle.high) for candle in ohlcv_data]
            lows = [float(candle.low) for candle in ohlcv_data]
            volumes = [float(candle.volume) for candle in ohlcv_data]
            
            if len(closes) < 20:
                return json.dumps({
                    "error": "Insufficient data points. Need at least 20 data points for reliable analysis.",
                    "data_points": len(closes)
                })

            results = {
                "indicators": {},
                "signals": {},
                "patterns": {},
                "summary": {}
            }

            # Calculate requested indicators
            for indicator in indicators:
                if indicator.lower() == 'rsi':
                    rsi_period = periods.get('rsi', 14)
                    rsi_values = self._calculate_rsi(closes, rsi_period)
                    results['indicators']['rsi'] = {
                        'values': rsi_values[-10:],  # Last 10 values
                        'current': rsi_values[-1] if rsi_values else None,
                        'period': rsi_period
                    }
                    
                elif indicator.lower() == 'macd':
                    fast_period = periods.get('macd_fast', 12)
                    slow_period = periods.get('macd_slow', 26)
                    signal_period = periods.get('macd_signal', 9)
                    macd_data = self._calculate_macd(closes, fast_period, slow_period, signal_period)
                    results['indicators']['macd'] = {
                        'macd': macd_data['macd'][-10:],
                        'signal': macd_data['signal'][-10:],
                        'histogram': macd_data['histogram'][-10:],
                        'current': {
                            'macd': macd_data['macd'][-1] if macd_data['macd'] else None,
                            'signal': macd_data['signal'][-1] if macd_data['signal'] else None,
                            'histogram': macd_data['histogram'][-1] if macd_data['histogram'] else None
                        }
                    }
                    
                elif indicator.lower() == 'bb':
                    bb_period = periods.get('bb', 20)
                    bb_data = self._calculate_bollinger_bands(closes, bb_period)
                    results['indicators']['bollinger_bands'] = {
                        'upper': bb_data['upper'][-10:],
                        'middle': bb_data['middle'][-10:],
                        'lower': bb_data['lower'][-10:],
                        'current': {
                            'upper': bb_data['upper'][-1] if bb_data['upper'] else None,
                            'middle': bb_data['middle'][-1] if bb_data['middle'] else None,
                            'lower': bb_data['lower'][-1] if bb_data['lower'] else None
                        },
                        'period': bb_period
                    }
                    
                elif indicator.lower() == 'sma':
                    sma_period = periods.get('sma', 20)
                    sma_values = self._calculate_sma(closes, sma_period)
                    results['indicators']['sma'] = {
                        'values': sma_values[-10:],
                        'current': sma_values[-1] if sma_values else None,
                        'period': sma_period
                    }
                    
                elif indicator.lower() == 'ema':
                    ema_period = periods.get('ema', 20)
                    ema_values = self._calculate_ema(closes, ema_period)
                    results['indicators']['ema'] = {
                        'values': ema_values[-10:],
                        'current': ema_values[-1] if ema_values else None,
                        'period': ema_period
                    }

            # Generate trading signals
            results['signals'] = self._generate_signals(results['indicators'], closes[-1], signal_threshold)
            
            # Detect patterns
            results['patterns'] = self._detect_patterns(closes, highs, lows)
            
            # Generate summary
            results['summary'] = self._generate_summary(results, closes[-1])

            return json.dumps(results, indent=2)

        except Exception as e:
            return json.dumps({
                "error": f"Technical analysis failed: {str(e)}",
                "indicators": {},
                "signals": {},
                "patterns": {},
                "summary": {}
            })

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return []
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [max(delta, 0) for delta in deltas]
        losses = [abs(min(delta, 0)) for delta in deltas]
        
        rsi_values = []
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        for i in range(period, len(gains)):
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
            
            # Update averages
            avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
            avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
        
        return rsi_values

    def _calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(prices) < slow:
            return {'macd': [], 'signal': [], 'histogram': []}
        
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        # Calculate MACD line
        macd_line = []
        start_idx = max(0, len(ema_fast) - len(ema_slow))
        for i in range(len(ema_slow)):
            if i + start_idx < len(ema_fast):
                macd_line.append(ema_fast[i + start_idx] - ema_slow[i])
        
        # Calculate signal line (EMA of MACD)
        signal_line = self._calculate_ema(macd_line, signal) if len(macd_line) >= signal else []
        
        # Calculate histogram
        histogram = []
        start_hist = max(0, len(macd_line) - len(signal_line))
        for i in range(len(signal_line)):
            if i + start_hist < len(macd_line):
                histogram.append(macd_line[i + start_hist] - signal_line[i])
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: int = 2) -> Dict[str, List[float]]:
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            return {'upper': [], 'middle': [], 'lower': []}
        
        sma = self._calculate_sma(prices, period)
        upper_band = []
        lower_band = []
        
        for i in range(len(sma)):
            # Calculate standard deviation for the period
            start_idx = i + period - 1
            if start_idx < len(prices):
                period_prices = prices[start_idx - period + 1:start_idx + 1]
                std = math.sqrt(sum((p - sma[i]) ** 2 for p in period_prices) / period)
                
                upper_band.append(sma[i] + (std_dev * std))
                lower_band.append(sma[i] - (std_dev * std))
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }

    def _calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return []
        
        sma = []
        for i in range(period - 1, len(prices)):
            avg = sum(prices[i - period + 1:i + 1]) / period
            sma.append(avg)
        
        return sma

    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return []
        
        multiplier = 2 / (period + 1)
        ema = [sum(prices[:period]) / period]  # Start with SMA
        
        for i in range(period, len(prices)):
            ema_value = (prices[i] * multiplier) + (ema[-1] * (1 - multiplier))
            ema.append(ema_value)
        
        return ema

    def _generate_signals(self, indicators: Dict, current_price: float, threshold: float) -> Dict:
        """Generate trading signals based on indicators."""
        signals = {}
        
        # RSI signals
        if 'rsi' in indicators and indicators['rsi']['current']:
            rsi_current = indicators['rsi']['current']
            if rsi_current > 70:
                signals['rsi'] = {
                    'signal': 'SELL',
                    'strength': min(10, int((rsi_current - 70) / 3) + 6),
                    'confidence': 0.8,
                    'reason': f'RSI overbought at {rsi_current:.2f}'
                }
            elif rsi_current < 30:
                signals['rsi'] = {
                    'signal': 'BUY',
                    'strength': min(10, int((30 - rsi_current) / 3) + 6),
                    'confidence': 0.8,
                    'reason': f'RSI oversold at {rsi_current:.2f}'
                }
            else:
                signals['rsi'] = {
                    'signal': 'HOLD',
                    'strength': 5,
                    'confidence': 0.5,
                    'reason': f'RSI neutral at {rsi_current:.2f}'
                }
        
        # MACD signals
        if 'macd' in indicators and indicators['macd']['current']['histogram']:
            histogram = indicators['macd']['current']['histogram']
            if histogram > 0:
                signals['macd'] = {
                    'signal': 'BUY',
                    'strength': min(10, int(abs(histogram) * 100) + 5),
                    'confidence': 0.7,
                    'reason': 'MACD histogram positive (bullish momentum)'
                }
            else:
                signals['macd'] = {
                    'signal': 'SELL',
                    'strength': min(10, int(abs(histogram) * 100) + 5),
                    'confidence': 0.7,
                    'reason': 'MACD histogram negative (bearish momentum)'
                }
        
        # Bollinger Bands signals
        if 'bollinger_bands' in indicators:
            bb = indicators['bollinger_bands']['current']
            if bb['upper'] and bb['lower']:
                if current_price > bb['upper']:
                    signals['bollinger_bands'] = {
                        'signal': 'SELL',
                        'strength': 7,
                        'confidence': 0.6,
                        'reason': 'Price above upper Bollinger Band (overbought)'
                    }
                elif current_price < bb['lower']:
                    signals['bollinger_bands'] = {
                        'signal': 'BUY',
                        'strength': 7,
                        'confidence': 0.6,
                        'reason': 'Price below lower Bollinger Band (oversold)'
                    }
                else:
                    signals['bollinger_bands'] = {
                        'signal': 'HOLD',
                        'strength': 5,
                        'confidence': 0.5,
                        'reason': 'Price within Bollinger Bands (normal range)'
                    }
        
        return signals

    def _detect_patterns(self, closes: List[float], highs: List[float], lows: List[float]) -> Dict:
        """Detect basic chart patterns."""
        patterns = {}
        
        if len(closes) < 10:
            return patterns
        
        # Support and Resistance levels
        recent_highs = highs[-20:] if len(highs) >= 20 else highs
        recent_lows = lows[-20:] if len(lows) >= 20 else lows
        
        resistance = max(recent_highs)
        support = min(recent_lows)
        current_price = closes[-1]
        
        patterns['support_resistance'] = {
            'support': support,
            'resistance': resistance,
            'current_price': current_price,
            'distance_to_support': ((current_price - support) / support) * 100,
            'distance_to_resistance': ((resistance - current_price) / current_price) * 100
        }
        
        # Trend detection (simple)
        short_ma = sum(closes[-5:]) / 5 if len(closes) >= 5 else current_price
        long_ma = sum(closes[-20:]) / 20 if len(closes) >= 20 else current_price
        
        if short_ma > long_ma * 1.02:
            trend = 'UPTREND'
            trend_strength = min(10, int(((short_ma - long_ma) / long_ma) * 100))
        elif short_ma < long_ma * 0.98:
            trend = 'DOWNTREND'
            trend_strength = min(10, int(((long_ma - short_ma) / short_ma) * 100))
        else:
            trend = 'SIDEWAYS'
            trend_strength = 5
        
        patterns['trend'] = {
            'direction': trend,
            'strength': trend_strength,
            'short_ma': short_ma,
            'long_ma': long_ma
        }
        
        return patterns

    def _generate_summary(self, results: Dict, current_price: float) -> Dict:
        """Generate overall analysis summary."""
        signals = results.get('signals', {})
        patterns = results.get('patterns', {})
        
        buy_signals = sum(1 for s in signals.values() if s.get('signal') == 'BUY')
        sell_signals = sum(1 for s in signals.values() if s.get('signal') == 'SELL')
        total_signals = len(signals)
        
        if total_signals == 0:
            overall_signal = 'HOLD'
            confidence = 0.5
        elif buy_signals > sell_signals:
            overall_signal = 'BUY'
            confidence = min(0.9, 0.5 + (buy_signals - sell_signals) / total_signals * 0.4)
        elif sell_signals > buy_signals:
            overall_signal = 'SELL'
            confidence = min(0.9, 0.5 + (sell_signals - buy_signals) / total_signals * 0.4)
        else:
            overall_signal = 'HOLD'
            confidence = 0.5
        
        # Calculate average signal strength
        avg_strength = sum(s.get('strength', 5) for s in signals.values()) / total_signals if total_signals > 0 else 5
        
        summary = {
            'overall_signal': overall_signal,
            'confidence': round(confidence, 2),
            'signal_strength': round(avg_strength, 1),
            'current_price': current_price,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'hold_signals': total_signals - buy_signals - sell_signals,
            'trend': patterns.get('trend', {}).get('direction', 'UNKNOWN'),
            'key_levels': {
                'support': patterns.get('support_resistance', {}).get('support'),
                'resistance': patterns.get('support_resistance', {}).get('resistance')
            }
        }
        
        return summary