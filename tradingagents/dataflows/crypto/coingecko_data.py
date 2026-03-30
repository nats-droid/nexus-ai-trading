import requests
import os
from dotenv import load_dotenv

load_dotenv()

COINGECKO_URL = "https://api.coingecko.com/api/v3"

COIN_IDS = {
    'BTC/USDT': 'bitcoin',
    'ETH/USDT': 'ethereum',
    'SOL/USDT': 'solana',
    'BNB/USDT': 'binancecoin',
}

def get_market_data(symbol='BTC/USDT'):
    """Ambil market data dari CoinGecko"""
    try:
        coin_id = COIN_IDS.get(symbol, 'bitcoin')
        url = f"{COINGECKO_URL}/coins/{coin_id}"
        params = {
            'localization': 'false',
            'tickers': 'false',
            'community_data': 'true',
            'developer_data': 'false',
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        market = data['market_data']
        return {
            'symbol': symbol,
            'market_cap': market['market_cap']['usd'],
            'market_cap_rank': data['market_cap_rank'],
            'volume_24h': market['total_volume']['usd'],
            'price_change_7d': market['price_change_percentage_7d'],
            'price_change_30d': market['price_change_percentage_30d'],
            'ath': market['ath']['usd'],
            'ath_change_pct': market['ath_change_percentage']['usd'],
            'circulating_supply': market['circulating_supply'],
            'sentiment_votes_up': data.get('sentiment_votes_up_percentage', 0),
            'sentiment_votes_down': data.get('sentiment_votes_down_percentage', 0),
        }
    except Exception as e:
        print(f'Error get_market_data {symbol}: {e}')
        return None

def get_fear_greed():
    """Ambil Fear & Greed Index"""
    try:
        r = requests.get('https://api.alternative.me/fng/', timeout=10)
        data = r.json()['data'][0]
        return {
            'value': int(data['value']),
            'label': data['value_classification'],
        }
    except Exception as e:
        print(f'Error get_fear_greed: {e}')
        return None

def get_trending():
    """Ambil trending coins"""
    try:
        r = requests.get(f"{COINGECKO_URL}/search/trending", timeout=10)
        coins = r.json()['coins'][:5]
        return [c['item']['name'] for c in coins]
    except Exception as e:
        print(f'Error get_trending: {e}')
        return None

if __name__ == '__main__':
    print('Testing CoinGecko dataflow...')
    data = get_market_data('BTC/USDT')
    print(f'Market Cap: ${data["market_cap"]:,.0f}')
    print(f'Rank: #{data["market_cap_rank"]}')
    print(f'7d Change: {data["price_change_7d"]:.2f}%')
    print(f'Community Sentiment Up: {data["sentiment_votes_up"]:.1f}%')
    fg = get_fear_greed()
    print(f'Fear & Greed: {fg["value"]} — {fg["label"]}')
    trending = get_trending()
    print(f'Trending: {", ".join(trending)}')
