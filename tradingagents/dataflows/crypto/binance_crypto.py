import ccxt
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_SECRET'),
})

def get_ohlcv(symbol='BTC/USDT', timeframe='4h', limit=100):
    """Ambil data OHLCV dari Binance"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        print(f'Error get_ohlcv {symbol}: {e}')
        return None

def get_ticker(symbol='BTC/USDT'):
    """Ambil harga terkini"""
    try:
        ticker = exchange.fetch_ticker(symbol)
        return {
            'symbol': symbol,
            'price': ticker['last'],
            'change_pct': ticker['percentage'],
            'volume_24h': ticker['quoteVolume'],
            'high_24h': ticker['high'],
            'low_24h': ticker['low'],
        }
    except Exception as e:
        print(f'Error get_ticker {symbol}: {e}')
        return None

def get_orderbook(symbol='BTC/USDT', limit=10):
    """Ambil order book"""
    try:
        ob = exchange.fetch_order_book(symbol, limit)
        return {
            'bids': ob['bids'][:5],
            'asks': ob['asks'][:5],
        }
    except Exception as e:
        print(f'Error get_orderbook {symbol}: {e}')
        return None

if __name__ == '__main__':
    print('Testing Binance dataflow...')
    ticker = get_ticker('BTC/USDT')
    print(f'BTC Price: ${ticker["price"]:,.2f}')
    print(f'24h Change: {ticker["change_pct"]:.2f}%')
    df = get_ohlcv('BTC/USDT', '4h', 10)
    print(f'OHLCV data: {len(df)} candles')
    print(df.tail(3))
