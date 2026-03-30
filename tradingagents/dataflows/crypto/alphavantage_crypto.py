import requests
import os
from dotenv import load_dotenv

load_dotenv()

AV_KEY = os.getenv('ALPHA_VANTAGE_KEY')
AV_URL = "https://www.alphavantage.co/query"

def get_crypto_daily(symbol='BTC', market='USD'):
    """Ambil data harian crypto dari Alpha Vantage"""
    try:
        params = {
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': symbol,
            'market': market,
            'apikey': AV_KEY,
        }
        r = requests.get(AV_URL, params=params, timeout=15)
        data = r.json()
        if 'Time Series (Digital Currency Daily)' not in data:
            print(f'AV Error: {data}')
            return None
        ts = data['Time Series (Digital Currency Daily)']
        latest_date = list(ts.keys())[0]
        latest = ts[latest_date]
        return {
            'date': latest_date,
            'open': float(latest['1. open']),
            'high': float(latest['2. high']),
            'low': float(latest['3. low']),
            'close': float(latest['4. close']),
            'volume': float(latest['5. volume']),
        }
    except Exception as e:
        print(f'Error get_crypto_daily: {e}')
        return None

def get_crypto_news(tickers='CRYPTO:BTC,CRYPTO:ETH'):
    """Ambil berita crypto dari Alpha Vantage"""
    try:
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': tickers,
            'limit': 10,
            'apikey': AV_KEY,
        }
        r = requests.get(AV_URL, params=params, timeout=15)
        data = r.json()
        if 'feed' not in data:
            print(f'AV News Error: {data}')
            return None
        news = []
        for item in data['feed'][:5]:
            news.append({
                'title': item['title'],
                'summary': item['summary'][:200],
                'sentiment': item['overall_sentiment_label'],
                'score': item['overall_sentiment_score'],
                'source': item['source'],
                'time': item['time_published'],
            })
        return news
    except Exception as e:
        print(f'Error get_crypto_news: {e}')
        return None

def get_rsi(symbol='BTC', interval='60min'):
    """Ambil RSI dari Alpha Vantage"""
    try:
        params = {
            'function': 'RSI',
            'symbol': f'{symbol}USD',
            'interval': interval,
            'time_period': 14,
            'series_type': 'close',
            'apikey': AV_KEY,
        }
        r = requests.get(AV_URL, params=params, timeout=15)
        data = r.json()
        if 'Technical Analysis: RSI' not in data:
            return None
        ts = data['Technical Analysis: RSI']
        latest = list(ts.values())[0]
        return float(latest['RSI'])
    except Exception as e:
        print(f'Error get_rsi: {e}')
        return None

if __name__ == '__main__':
    print('Testing Alpha Vantage dataflow...')
    daily = get_crypto_daily('BTC')
    if daily:
        print(f'BTC Daily Close: ${daily["close"]:,.2f}')
        print(f'Date: {daily["date"]}')
    news = get_crypto_news()
    if news:
        print(f'\nTop news ({len(news)} articles):')
        for n in news[:3]:
            print(f'  [{n["sentiment"]}] {n["title"][:60]}...')
    else:
        print('News: rate limit atau belum tersedia')
