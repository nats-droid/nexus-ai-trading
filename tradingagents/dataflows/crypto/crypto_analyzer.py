import os
import sys
import re
import anthropic
import requests
from dotenv import load_dotenv
sys.path.insert(0, '.')
from tradingagents.dataflows.crypto.binance_crypto import get_ticker
from tradingagents.dataflows.crypto.coingecko_data import get_market_data, get_trending
from tradingagents.dataflows.crypto.alphavantage_crypto import get_crypto_news
from tradingagents.dataflows.crypto.sentiment_data import get_sentiment_summary
from tradingagents.dataflows.crypto.technical_analysis import get_full_analysis

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
ANALYST_MODEL = os.getenv("ANALYST_MODEL", "claude-haiku-4-5-20251001")
REASONING_MODEL = os.getenv("REASONING_MODEL", "claude-sonnet-4-6")

def clean_text(text):
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
    text = re.sub(r'---+', '', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'^\s*[-•]\s*', '', text, flags=re.MULTILINE)
    return text.strip()

def call_llm(prompt, model=None, max_tokens=1000):
    if model is None:
        model = ANALYST_MODEL
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text

def collect_data(symbol="BTC/USDT"):
    print(f"Mengumpulkan data {symbol}...")
    ticker = get_ticker(symbol)
    market = get_market_data(symbol)
    sentiment = get_sentiment_summary()
    coin = symbol.split("/")[0]
    news = get_crypto_news(f"CRYPTO:{coin}")
    technical = get_full_analysis(symbol, "4h")
    return {
        "ticker": ticker,
        "market": market,
        "sentiment": sentiment,
        "news": news,
        "technical": technical,
    }

def technical_analyst(data, symbol):
    tech = data["technical"]
    ticker = data["ticker"]
    prompt = f"""Kamu adalah Technical Analyst crypto profesional. Berikan analisis SINGKAT dan PADAT tanpa formatting markdown, tanpa heading, tanpa bullet points, tanpa bold text.

Analisis data teknikal {symbol}:
Harga: ${ticker["price"]:,.2f} | 24h: {ticker["change_pct"]:.2f}%
Trend: {tech["trend"]} | EMA9: {tech["ema9"]} | EMA21: {tech["ema21"]} | EMA50: {tech["ema50"]}
RSI: {tech["rsi"]} | MACD: {tech["macd"]} | BB Position: {tech["bb_position"]}%
Support: {tech["supports"]} | Resistance: {tech["resistances"]}
Sinyal: {tech["signals"] if tech["signals"] else "Tidak ada crossover"}

Tulis 2-3 kalimat biasa (bukan list, bukan heading): kondisi trend, level kunci, dan kesimpulan BULLISH/BEARISH/NEUTRAL."""
    return call_llm(prompt, ANALYST_MODEL)

def onchain_analyst(data, symbol):
    market = data["market"]
    prompt = f"""Kamu adalah On-chain Analyst crypto profesional. Berikan analisis SINGKAT tanpa formatting markdown, tanpa heading, tanpa bullet points.

Data market {symbol}:
Market Cap: ${market["market_cap"]:,.0f} | Rank: #{market["market_cap_rank"]}
Volume 24h: ${market["volume_24h"]:,.0f} | 7d: {market["price_change_7d"]:.2f}% | 30d: {market["price_change_30d"]:.2f}%
ATH Change: {market["ath_change_pct"]:.1f}% | Sentiment Up: {market["sentiment_votes_up"]:.1f}%

Tulis 2-3 kalimat biasa: kondisi fundamental, volume, dan kesimpulan BULLISH/BEARISH/NEUTRAL."""
    return call_llm(prompt, ANALYST_MODEL)

def sentiment_analyst(data, symbol):
    sent = data["sentiment"]
    history_text = ""
    for h in sent["history"]:
        history_text += f"{h['date']}: {h['value']} {h['label']}\n"
    prompt = f"""Kamu adalah Sentiment Analyst crypto profesional. Berikan analisis SINGKAT tanpa formatting markdown, tanpa heading, tanpa bullet points.

Data sentiment {symbol}:
Fear & Greed: {sent["current_value"]} — {sent["current_label"]}
Rata-rata 7 hari: {sent["avg_7d"]} | Tren: {sent["trend_7d"]}
Sinyal: {sent["signal"]} — {sent["reason"]}
Histori: {history_text}

Tulis 2-3 kalimat biasa: kondisi sentiment, tren, dan kesimpulan BULLISH/BEARISH/NEUTRAL."""
    return call_llm(prompt, ANALYST_MODEL)

def news_analyst(data, symbol):
    news = data["news"]
    if not news:
        return "Tidak ada data berita tersedia saat ini."
    news_text = ""
    for i, n in enumerate(news[:5], 1):
        news_text += f"{i}. [{n['sentiment']}] {n['title']}\n"
    prompt = f"""Kamu adalah News Analyst crypto profesional. Berikan analisis SINGKAT tanpa formatting markdown, tanpa heading, tanpa bullet points.

Berita terkini {symbol}:
{news_text}

Tulis 2-3 kalimat biasa: tema utama berita, dampak ke pasar, dan kesimpulan BULLISH/BEARISH/NEUTRAL."""
    return call_llm(prompt, ANALYST_MODEL)

def bull_researcher(symbol, tech, onchain, sentiment, news):
    prompt = f"""Kamu adalah Bull Researcher. Buat argumen TERKUAT kenapa {symbol} akan NAIK.
Tulis dalam paragraf biasa tanpa markdown, tanpa heading, tanpa bullet points, tanpa bold text.

Data dari analyst:
Technical: {tech}
On-chain: {onchain}
Sentiment: {sentiment}
News: {news}

Tulis 3-4 kalimat argumen bullish yang kuat dan meyakinkan."""
    return call_llm(prompt, REASONING_MODEL, 1500)

def bear_researcher(symbol, tech, onchain, sentiment, news):
    prompt = f"""Kamu adalah Bear Researcher. Buat argumen TERKUAT kenapa {symbol} akan TURUN.
Tulis dalam paragraf biasa tanpa markdown, tanpa heading, tanpa bullet points, tanpa bold text.

Data dari analyst:
Technical: {tech}
On-chain: {onchain}
Sentiment: {sentiment}
News: {news}

Tulis 3-4 kalimat argumen bearish yang kuat dan meyakinkan."""
    return call_llm(prompt, REASONING_MODEL, 1500)

def portfolio_manager(symbol, bull_case, bear_case, technical, levels):
    prompt = f"""Kamu adalah Portfolio Manager crypto profesional.
Buat keputusan trading final untuk {symbol}.
Tulis ALASAN dalam 1-2 kalimat biasa tanpa markdown.

ARGUMEN BULL: {bull_case}
ARGUMEN BEAR: {bear_case}
Entry: ${technical["current_price"]:,.2f}
TP1: ${levels["tp1"]:,.2f} ({levels["tp1_pct"]:+.2f}%)
TP2: ${levels["tp2"]:,.2f} ({levels["tp2_pct"]:+.2f}%)
SL: ${levels["sl"]:,.2f} ({levels["sl_pct"]:+.2f}%)
R/R: 1:{levels["rr1"]}

Format jawaban TEPAT (tidak ada teks lain):
KEPUTUSAN: [BUY/SELL/HOLD]
CONFIDENCE: [0-100]%
ALASAN: [1-2 kalimat tanpa markdown]"""
    return call_llm(prompt, REASONING_MODEL, 1000)

def parse_decision(pm_output):
    lines = pm_output.strip().split("\n")
    decision = "HOLD"
    confidence = 50
    reason = ""
    for line in lines:
        if line.startswith("KEPUTUSAN:"):
            val = line.replace("KEPUTUSAN:", "").strip().upper()
            if "BUY" in val:
                decision = "BUY"
            elif "SELL" in val:
                decision = "SELL"
            else:
                decision = "HOLD"
        elif line.startswith("CONFIDENCE:"):
            val = line.replace("CONFIDENCE:", "").replace("%", "").strip()
            try:
                confidence = int(val)
            except:
                confidence = 50
        elif line.startswith("ALASAN:"):
            reason = line.replace("ALASAN:", "").strip()
    return decision, confidence, clean_text(reason)

def format_telegram_message(symbol, decision, confidence, reason,
                             levels, tech_summary, onchain_summary,
                             sentiment_summary, news_summary,
                             bull_case, bear_case,
                             timeframe="12H", paper_trading=True):
    min_confidence = int(os.getenv("MIN_CONFIDENCE", 65))
    if confidence < min_confidence:
        return None
    if decision == "BUY":
        emoji = "🟢"
    elif decision == "SELL":
        emoji = "🔴"
    else:
        return None
    mode = "📋 PAPER TRADING" if paper_trading else "💰 LIVE TRADING"
    max_pos = os.getenv("MAX_POSITION_SIZE_USD", 100)

    tech_clean = clean_text(tech_summary)[:120]
    onchain_clean = clean_text(onchain_summary)[:120]
    sentiment_clean = clean_text(sentiment_summary)[:120]
    news_clean = clean_text(news_summary)[:120]
    bull_clean = clean_text(bull_case)[:220]
    bear_clean = clean_text(bear_case)[:220]

    msg = f"""{emoji} {decision} — {symbol}  |  {timeframe}  |  Confidence {confidence}%

📍 Entry   : ${levels["entry"]:,.2f}
🎯 TP1     : ${levels["tp1"]:,.2f} ({levels["tp1_pct"]:+.2f}%)
🎯 TP2     : ${levels["tp2"]:,.2f} ({levels["tp2_pct"]:+.2f}%)
🛑 SL      : ${levels["sl"]:,.2f} ({levels["sl_pct"]:+.2f}%)
📊 R/R     : 1:{levels["rr1"]} (TP1)  ·  1:{levels["rr2"]} (TP2)
💰 Posisi  : ${max_pos} max

━━━━━━━━━━━━━━━━━━
🤖 ANALYST:
- Technical  : {tech_clean}
- On-chain   : {onchain_clean}
- Sentiment  : {sentiment_clean}
- News       : {news_clean}

⚔️ DEBAT:
🐂 Bull: {bull_clean}
🐻 Bear: {bear_clean}

🏦 PM: {reason}

━━━━━━━━━━━━━━━━━━
{mode}
⚠️ Eksekusi manual di Binance"""
    return msg

def run_analysis(symbol="BTC/USDT", timeframe_hours=12, paper_trading=True):
    print(f"\n{'='*50}")
    print(f"Memulai analisis {symbol}...")
    print(f"{'='*50}")

    timeframe_label = f"{timeframe_hours}H"

    data = collect_data(symbol)
    print("  [1/7] Technical Analyst...")
    tech = technical_analyst(data, symbol)
    print("  [2/7] On-chain Analyst...")
    onchain = onchain_analyst(data, symbol)
    print("  [3/7] Sentiment Analyst...")
    sentiment = sentiment_analyst(data, symbol)
    print("  [4/7] News Analyst...")
    news = news_analyst(data, symbol)
    print("  [5/7] Bull Researcher...")
    bull = bull_researcher(symbol, tech, onchain, sentiment, news)
    print("  [6/7] Bear Researcher...")
    bear = bear_researcher(symbol, tech, onchain, sentiment, news)
    print("  [7/7] Portfolio Manager...")
    levels = data["technical"]["levels"]
    pm_output = portfolio_manager(symbol, bull, bear, data["technical"], levels)
    decision, confidence, reason = parse_decision(pm_output)
    print(f"\nKeputusan: {decision} | Confidence: {confidence}%")

    msg = format_telegram_message(
        symbol, decision, confidence, reason,
        levels, tech, onchain, sentiment, news,
        bull, bear,
        timeframe=timeframe_label,
        paper_trading=paper_trading
    )
    return {
        "symbol": symbol,
        "decision": decision,
        "confidence": confidence,
        "reason": reason,
        "levels": levels,
        "message": msg,
    }

if __name__ == "__main__":
    paper = os.getenv("PAPER_TRADING", "true").lower() == "true"
    result = run_analysis("BTC/USDT", timeframe_hours=12, paper_trading=paper)
    print("\n" + "="*50)
    if result["message"]:
        print(result["message"])
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, json={"chat_id": chat_id, "text": result["message"]})
        if r.json().get("ok"):
            print("\n✅ Sinyal terkirim ke Telegram!")
        else:
            print("\n❌ Gagal kirim ke Telegram")
    else:
        print(f"Confidence {result['confidence']}% di bawah threshold")
        print(f"Keputusan internal: {result['decision']}")
