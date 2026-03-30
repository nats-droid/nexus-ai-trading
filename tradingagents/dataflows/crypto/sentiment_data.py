import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_fear_greed_history(limit=7):
    """Ambil histori Fear & Greed Index 7 hari terakhir"""
    try:
        r = requests.get(
            f'https://api.alternative.me/fng/?limit={limit}',
            timeout=10
        )
        data = r.json()['data']
        history = []
        for d in data:
            history.append({
                'date': datetime.fromtimestamp(int(d['timestamp'])).strftime('%Y-%m-%d'),
                'value': int(d['value']),
                'label': d['value_classification'],
            })
        return history
    except Exception as e:
        print(f'Error get_fear_greed_history: {e}')
        return None

def get_sentiment_summary():
    """Ringkasan sentiment untuk agent"""
    try:
        history = get_fear_greed_history(7)
        if not history:
            return None
        current = history[0]
        avg_7d = sum(h['value'] for h in history) / len(history)
        trend = 'MENINGKAT' if history[0]['value'] > history[-1]['value'] else 'MENURUN'
        label = current['label']
        value = current['value']
        if value >= 75:
            signal = 'BEARISH'
            reason = 'Extreme Greed — pasar terlalu panas, potensi koreksi'
        elif value >= 55:
            signal = 'NEUTRAL-BULLISH'
            reason = 'Greed — sentimen positif, hati-hati momentum'
        elif value >= 45:
            signal = 'NEUTRAL'
            reason = 'Neutral — pasar tidak terlalu greed atau fear'
        elif value >= 25:
            signal = 'NEUTRAL-BULLISH'
            reason = 'Fear — potensi buying opportunity'
        else:
            signal = 'BULLISH'
            reason = 'Extreme Fear — historis waktu terbaik untuk beli'
        return {
            'current_value': value,
            'current_label': label,
            'avg_7d': round(avg_7d, 1),
            'trend_7d': trend,
            'signal': signal,
            'reason': reason,
            'history': history,
        }
    except Exception as e:
        print(f'Error get_sentiment_summary: {e}')
        return None

if __name__ == '__main__':
    print('Testing Sentiment dataflow...')
    summary = get_sentiment_summary()
    if summary:
        print(f'Fear & Greed sekarang : {summary["current_value"]} — {summary["current_label"]}')
        print(f'Rata-rata 7 hari      : {summary["avg_7d"]}')
        print(f'Tren 7 hari           : {summary["trend_7d"]}')
        print(f'Sinyal untuk agent    : {summary["signal"]}')
        print(f'Alasan                : {summary["reason"]}')
        print(f'\nHistori 7 hari:')
        for h in summary['history']:
            bar = '█' * (h['value'] // 10)
            print(f'  {h["date"]} : {h["value"]:3d} {bar} {h["label"]}')
