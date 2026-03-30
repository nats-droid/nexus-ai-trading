import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '.')
from tradingagents.dataflows.crypto.binance_crypto import get_ohlcv

def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = calc_ema(series, fast)
    ema_slow = calc_ema(series, slow)
    macd = ema_fast - ema_slow
    signal_line = calc_ema(macd, signal)
    histogram = macd - signal_line
    return macd, signal_line, histogram

def calc_bollinger(series, period=20, std=2):
    sma = series.rolling(period).mean()
    std_dev = series.rolling(period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return upper, sma, lower

def find_support_resistance(df, lookback=50):
    highs = []
    lows = []
    data = df['close'].tail(lookback).values
    for i in range(2, len(data) - 2):
        if data[i] > data[i-1] and data[i] > data[i-2] and data[i] > data[i+1] and data[i] > data[i+2]:
            highs.append(data[i])
        if data[i] < data[i-1] and data[i] < data[i-2] and data[i] < data[i+1] and data[i] < data[i+2]:
            lows.append(data[i])
    current_price = data[-1]
    resistances = sorted([h for h in highs if h > current_price])[:3]
    supports = sorted([l for l in lows if l < current_price], reverse=True)[:3]
    return supports, resistances

def calculate_tp_sl(current_price, supports, resistances, side='BUY'):
    if side == 'BUY':
        sl = supports[0] * 0.999 if supports else current_price * 0.98
        tp1 = resistances[0] if resistances else current_price * 1.02
        tp2 = resistances[1] if len(resistances) > 1 else current_price * 1.04
    else:
        sl = resistances[0] * 1.001 if resistances else current_price * 1.02
        tp1 = supports[0] if supports else current_price * 0.98
        tp2 = supports[1] if len(supports) > 1 else current_price * 0.96
    rr1 = abs(tp1 - current_price) / abs(current_price - sl)
    rr2 = abs(tp2 - current_price) / abs(current_price - sl)
    return {
        'entry': current_price,
        'sl': round(sl, 2),
        'tp1': round(tp1, 2),
        'tp2': round(tp2, 2),
        'sl_pct': round((sl - current_price) / current_price * 100, 2),
        'tp1_pct': round((tp1 - current_price) / current_price * 100, 2),
        'tp2_pct': round((tp2 - current_price) / current_price * 100, 2),
        'rr1': round(rr1, 2),
        'rr2': round(rr2, 2),
    }

def get_full_analysis(symbol='BTC/USDT', timeframe='4h'):
    df = get_ohlcv(symbol, timeframe, 100)
    if df is None:
        return None
    close = df['close']
    ema9  = calc_ema(close, 9)
    ema21 = calc_ema(close, 21)
    ema50 = calc_ema(close, 50)
    rsi   = calc_rsi(close)
    macd, signal, hist = calc_macd(close)
    bb_upper, bb_mid, bb_lower = calc_bollinger(close)
    supports, resistances = find_support_resistance(df)
    current = close.iloc[-1]
    ema9_cross  = ema9.iloc[-1] > ema21.iloc[-1] and ema9.iloc[-2] <= ema21.iloc[-2]
    ema9_dcross = ema9.iloc[-1] < ema21.iloc[-1] and ema9.iloc[-2] >= ema21.iloc[-2]
    macd_cross  = hist.iloc[-1] > 0 and hist.iloc[-2] <= 0
    macd_dcross = hist.iloc[-1] < 0 and hist.iloc[-2] >= 0
    rsi_val = rsi.iloc[-1]
    trend = 'BULLISH' if ema9.iloc[-1] > ema21.iloc[-1] > ema50.iloc[-1] else 'BEARISH' if ema9.iloc[-1] < ema21.iloc[-1] < ema50.iloc[-1] else 'SIDEWAYS'
    signals = []
    if ema9_cross:
        signals.append('EMA9 cross EMA21 ke atas (BULLISH)')
    if ema9_dcross:
        signals.append('EMA9 cross EMA21 ke bawah (BEARISH)')
    if macd_cross:
        signals.append('MACD cross signal ke atas (BULLISH)')
    if macd_dcross:
        signals.append('MACD cross signal ke bawah (BEARISH)')
    if rsi_val < 30:
        signals.append(f'RSI {rsi_val:.1f} — Oversold (BULLISH)')
    if rsi_val > 70:
        signals.append(f'RSI {rsi_val:.1f} — Overbought (BEARISH)')
    bb_pos = (current - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1]) * 100
    levels = calculate_tp_sl(current, supports, resistances)
    return {
        'symbol': symbol,
        'timeframe': timeframe,
        'current_price': round(current, 2),
        'trend': trend,
        'ema9': round(ema9.iloc[-1], 2),
        'ema21': round(ema21.iloc[-1], 2),
        'ema50': round(ema50.iloc[-1], 2),
        'rsi': round(rsi_val, 1),
        'macd': round(macd.iloc[-1], 2),
        'macd_signal': round(signal.iloc[-1], 2),
        'bb_upper': round(bb_upper.iloc[-1], 2),
        'bb_lower': round(bb_lower.iloc[-1], 2),
        'bb_position': round(bb_pos, 1),
        'supports': [round(s, 2) for s in supports],
        'resistances': [round(r, 2) for r in resistances],
        'signals': signals,
        'levels': levels,
    }

if __name__ == '__main__':
    print('Testing Technical Analysis...')
    analysis = get_full_analysis('BTC/USDT', '4h')
    if analysis:
        print(f'Symbol      : {analysis["symbol"]}')
        print(f'Price       : \${analysis["current_price"]:,.2f}')
        print(f'Trend       : {analysis["trend"]}')
        print(f'EMA9/21/50  : {analysis["ema9"]} / {analysis["ema21"]} / {analysis["ema50"]}')
        print(f'RSI         : {analysis["rsi"]}')
        print(f'BB Position : {analysis["bb_position"]}%')
        print(f'Supports    : {analysis["supports"]}')
        print(f'Resistances : {analysis["resistances"]}')
        print()
        print('Sinyal aktif:')
        if analysis['signals']:
            for s in analysis['signals']:
                print(f'  - {s}')
        else:
            print('  - Tidak ada sinyal crossover saat ini')
        print()
        lvl = analysis['levels']
        print(f'Entry : \${lvl["entry"]:,.2f}')
        print(f'TP1   : \${lvl["tp1"]:,.2f} ({lvl["tp1_pct"]:+.2f}%)')
        print(f'TP2   : \${lvl["tp2"]:,.2f} ({lvl["tp2_pct"]:+.2f}%)')
        print(f'SL    : \${lvl["sl"]:,.2f} ({lvl["sl_pct"]:+.2f}%)')
        print(f'R/R   : 1:{lvl["rr1"]} (TP1) / 1:{lvl["rr2"]} (TP2)')
