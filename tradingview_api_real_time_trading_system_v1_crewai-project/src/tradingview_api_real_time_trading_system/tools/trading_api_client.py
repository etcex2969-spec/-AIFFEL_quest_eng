from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, Optional
import requests
import json
import time
import hmac
import hashlib
from urllib.parse import urlencode

class TradingAPIClientInput(BaseModel):
    """Input schema for Trading API Client Tool."""
    exchange: str = Field(..., description="Exchange name (binance, upbit, kucoin)")
    endpoint: str = Field(..., description="API endpoint (ticker, orderbook, trades, klines)")
    symbol: str = Field(..., description="Trading pair symbol (BTCUSDT, BTC-KRW, BTC-USDT)")
    additional_params: Optional[Dict[str, Any]] = Field(default={}, description="Additional parameters for the API call")

class TradingAPIClientTool(BaseTool):
    """Tool for fetching real-time trading data from various cryptocurrency exchanges."""

    name: str = "trading_api_client"
    description: str = (
        "Fetches real-time trading data from cryptocurrency exchanges including "
        "price tickers, order books, recent trades, and candlestick data. "
        "Supports Binance, Upbit, and KuCoin exchanges with proper authentication and rate limiting."
    )
    args_schema: Type[BaseModel] = TradingAPIClientInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_request_time = {}
        self.rate_limits = {
            'binance': 0.1,  # 10 requests per second
            'upbit': 0.1,    # 10 requests per second  
            'kucoin': 0.33   # 3 requests per second
        }
        
        # Exchange base URLs
        self.base_urls = {
            'binance': 'https://api.binance.com',
            'upbit': 'https://api.upbit.com',
            'kucoin': 'https://api.kucoin.com'
        }
        
        # Exchange endpoint mappings
        self.endpoint_mappings = {
            'binance': {
                'ticker': '/api/v3/ticker/24hr',
                'orderbook': '/api/v3/depth',
                'trades': '/api/v3/trades',
                'klines': '/api/v3/klines'
            },
            'upbit': {
                'ticker': '/v1/ticker',
                'orderbook': '/v1/orderbook',
                'trades': '/v1/trades/ticks',
                'klines': '/v1/candles/minutes/1'
            },
            'kucoin': {
                'ticker': '/api/v1/market/stats',
                'orderbook': '/api/v1/market/orderbook/level2_20',
                'trades': '/api/v1/market/histories',
                'klines': '/api/v1/market/candles'
            }
        }

    def _apply_rate_limit(self, exchange: str):
        """Apply rate limiting based on exchange requirements."""
        current_time = time.time()
        last_time = self.last_request_time.get(exchange, 0)
        time_diff = current_time - last_time
        min_interval = self.rate_limits.get(exchange, 0.1)
        
        if time_diff < min_interval:
            time.sleep(min_interval - time_diff)
        
        self.last_request_time[exchange] = time.time()

    def _normalize_symbol(self, symbol: str, exchange: str) -> str:
        """Normalize symbol format for different exchanges."""
        if exchange == 'upbit':
            # Upbit uses KRW-BTC format
            if '-' not in symbol:
                # Convert BTCUSDT to KRW-BTC (assuming KRW for Upbit)
                if 'USDT' in symbol:
                    base = symbol.replace('USDT', '')
                    return f'KRW-{base}'
                else:
                    return f'KRW-{symbol}'
            return symbol
        elif exchange == 'kucoin':
            # KuCoin uses BTC-USDT format
            if '-' not in symbol:
                # Convert BTCUSDT to BTC-USDT
                if 'USDT' in symbol:
                    base = symbol.replace('USDT', '')
                    return f'{base}-USDT'
                else:
                    return f'{symbol}-USDT'
            return symbol
        else:
            # Binance uses BTCUSDT format (no separator)
            return symbol.replace('-', '')

    def _build_url(self, exchange: str, endpoint: str, symbol: str, additional_params: Dict) -> str:
        """Build the complete API URL."""
        base_url = self.base_urls[exchange]
        endpoint_path = self.endpoint_mappings[exchange][endpoint]
        normalized_symbol = self._normalize_symbol(symbol, exchange)
        
        params = additional_params.copy()
        
        # Add symbol parameter based on exchange
        if exchange == 'upbit':
            params['markets'] = normalized_symbol
        elif exchange == 'kucoin':
            params['symbol'] = normalized_symbol
        else:  # binance
            params['symbol'] = normalized_symbol
            
        # Add default parameters for specific endpoints
        if endpoint == 'orderbook':
            if exchange == 'binance':
                params.setdefault('limit', 20)
        elif endpoint == 'trades':
            if exchange == 'binance':
                params.setdefault('limit', 100)
        
        query_string = urlencode(params) if params else ''
        url = f"{base_url}{endpoint_path}"
        if query_string:
            url += f"?{query_string}"
            
        return url

    def _standardize_ticker_response(self, data: Any, exchange: str) -> Dict:
        """Standardize ticker response across exchanges."""
        if exchange == 'binance':
            return {
                'symbol': data.get('symbol'),
                'price': float(data.get('lastPrice', 0)),
                'price_change_24h': float(data.get('priceChange', 0)),
                'price_change_percent_24h': float(data.get('priceChangePercent', 0)),
                'volume_24h': float(data.get('volume', 0)),
                'high_24h': float(data.get('highPrice', 0)),
                'low_24h': float(data.get('lowPrice', 0)),
                'exchange': exchange
            }
        elif exchange == 'upbit':
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            return {
                'symbol': data.get('market'),
                'price': float(data.get('trade_price', 0)),
                'price_change_24h': float(data.get('change_price', 0)),
                'price_change_percent_24h': float(data.get('change_rate', 0)) * 100,
                'volume_24h': float(data.get('acc_trade_volume_24h', 0)),
                'high_24h': float(data.get('high_price', 0)),
                'low_24h': float(data.get('low_price', 0)),
                'exchange': exchange
            }
        elif exchange == 'kucoin':
            return {
                'symbol': data.get('symbol'),
                'price': float(data.get('last', 0)),
                'price_change_24h': float(data.get('changePrice', 0)),
                'price_change_percent_24h': float(data.get('changeRate', 0)) * 100,
                'volume_24h': float(data.get('vol', 0)),
                'high_24h': float(data.get('high', 0)),
                'low_24h': float(data.get('low', 0)),
                'exchange': exchange
            }
        return data

    def _standardize_orderbook_response(self, data: Any, exchange: str) -> Dict:
        """Standardize orderbook response across exchanges."""
        if exchange in ['binance', 'kucoin']:
            return {
                'bids': [[float(bid[0]), float(bid[1])] for bid in data.get('bids', [])[:10]],
                'asks': [[float(ask[0]), float(ask[1])] for ask in data.get('asks', [])[:10]],
                'exchange': exchange
            }
        elif exchange == 'upbit':
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            orderbook_units = data.get('orderbook_units', [])
            bids = [[unit['bid_price'], unit['bid_size']] for unit in orderbook_units]
            asks = [[unit['ask_price'], unit['ask_size']] for unit in orderbook_units]
            return {
                'bids': bids[:10],
                'asks': asks[:10],
                'exchange': exchange
            }
        return data

    def _run(self, exchange: str, endpoint: str, symbol: str, additional_params: Dict[str, Any] = {}) -> str:
        """Execute the trading API request."""
        try:
            # Validate exchange
            if exchange.lower() not in self.base_urls:
                return f"Error: Unsupported exchange '{exchange}'. Supported: {list(self.base_urls.keys())}"
            
            exchange = exchange.lower()
            
            # Validate endpoint
            if endpoint.lower() not in self.endpoint_mappings[exchange]:
                return f"Error: Unsupported endpoint '{endpoint}' for {exchange}. Supported: {list(self.endpoint_mappings[exchange].keys())}"
            
            endpoint = endpoint.lower()
            
            # Apply rate limiting
            self._apply_rate_limit(exchange)
            
            # Build URL
            url = self._build_url(exchange, endpoint, symbol, additional_params)
            
            # Make request
            headers = {
                'User-Agent': 'TradingAPIClient/1.0',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Standardize response based on endpoint
            if endpoint == 'ticker':
                standardized_data = self._standardize_ticker_response(data, exchange)
            elif endpoint == 'orderbook':
                standardized_data = self._standardize_orderbook_response(data, exchange)
            else:
                # For trades and klines, return raw data with exchange info
                standardized_data = {
                    'data': data,
                    'exchange': exchange,
                    'endpoint': endpoint,
                    'symbol': symbol
                }
            
            return json.dumps({
                'success': True,
                'exchange': exchange,
                'endpoint': endpoint,
                'symbol': symbol,
                'data': standardized_data
            }, indent=2)
            
        except requests.exceptions.RequestException as e:
            return f"Error: Network request failed - {str(e)}"
        except requests.exceptions.HTTPError as e:
            return f"Error: HTTP error {response.status_code} - {str(e)}"
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON response - {str(e)}"
        except Exception as e:
            return f"Error: Unexpected error - {str(e)}"