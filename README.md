# 🚀 NEXUS AI Trading Bot

Multi-agent AI crypto trading bot yang menggunakan Claude AI untuk analisis dan sinyal trading otomatis via Telegram.

## ✨ Fitur

- 7 Claude AI agent bekerja paralel (Technical, On-chain, Sentiment, News, Bull, Bear, Portfolio Manager)
- Sinyal BUY/SELL dengan Entry, TP1, TP2, SL berbasis dynamic Support/Resistance
- Notifikasi dan kontrol penuh via Telegram
- Support multi-pair dan multi-interval (bisa beda interval per koin)
- Paper trading mode untuk testing sebelum go live
- Auto-restart via systemd (jalan 24/7)
- Mudah ganti model LLM via command Telegram

## 🤖 Arsitektur Agen
cat > /home/ubuntu/nexus-ai/TradingAgents/README.md << 'READMEEOF'
# 🚀 NEXUS AI Trading Bot

Multi-agent AI crypto trading bot menggunakan Claude AI untuk analisis dan sinyal trading otomatis via Telegram.

## ✨ Fitur

- 7 Claude AI agent (Technical, On-chain, Sentiment, News, Bull, Bear, Portfolio Manager)
- Sinyal BUY/SELL dengan Entry, TP1, TP2, SL berbasis dynamic Support/Resistance
- Notifikasi dan kontrol penuh via Telegram
- Support multi-pair dan multi-interval
- Paper trading mode
- Auto-restart via systemd (24/7)
- Ganti model LLM via command Telegram

## 🤖 Arsitektur 7 Agent

Layer 1 - Analyst (Claude Haiku):
  Agent 1: Technical Analyst  -> EMA, RSI, MACD, Bollinger, S/R
  Agent 2: On-chain Analyst   -> CoinGecko market data
  Agent 3: Sentiment Analyst  -> Fear & Greed Index
  Agent 4: News Analyst       -> Alpha Vantage news sentiment

Layer 2 - Researcher (Claude Sonnet):
  Agent 5: Bull Researcher    -> Argumen bullish
  Agent 6: Bear Researcher    -> Argumen bearish

Layer 3 - Decision (Claude Sonnet):
  Agent 7: Portfolio Manager  -> Keputusan final + Entry/TP/SL

## 📋 Requirements

- Ubuntu 22.04 LTS
- Python 3.11+

## 🔑 API Keys yang Dibutuhkan

- Anthropic Claude (berbayar, pay per use)
- Binance (gratis)
- Alpha Vantage (gratis)
- Telegram Bot (gratis)
- CoinGecko (gratis)
- Fear & Greed Index (gratis)

## 🚀 Instalasi

### 1. Clone repo

    git clone https://github.com/USERNAME/nexus-ai-trading.git
    cd nexus-ai-trading

### 2. Setup Python environment

    python3.11 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install ccxt fastapi uvicorn websockets apscheduler sqlalchemy psycopg2-binary redis python-telegram-bot requests pandas python-dotenv

### 3. Setup config

    cp .env.example .env
    nano .env

Isi semua API keys di file .env

### 4. Test koneksi

    python3 -c "
    import anthropic, os
    from dotenv import load_dotenv
    load_dotenv()
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    msg = client.messages.create(model='claude-haiku-4-5-20251001', max_tokens=50, messages=[{'role':'user','content':'Say OK'}])
    print('Anthropic OK:', msg.content[0].text)
    "

### 5. Setup Telegram Bot

1. Buka @BotFather di Telegram
2. Ketik /newbot dan ikuti instruksi
3. Copy token ke .env sebagai TELEGRAM_BOT_TOKEN
4. Kirim pesan ke bot, buka: https://api.telegram.org/botTOKEN/getUpdates
5. Copy chat.id ke .env sebagai TELEGRAM_CHAT_ID

### 6. Setup systemd service

Buat file /etc/systemd/system/nexus-bot.service:

    [Unit]
    Description=NEXUS AI Trading Bot
    After=network.target

    [Service]
    Type=simple
    User=ubuntu
    WorkingDirectory=/home/ubuntu/nexus-ai/TradingAgents
    EnvironmentFile=/home/ubuntu/nexus-ai/TradingAgents/.env
    ExecStart=/home/ubuntu/nexus-ai/TradingAgents/venv/bin/python3 api/scheduler.py
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target

Buat file /etc/systemd/system/nexus-telegram.service:

    [Unit]
    Description=NEXUS AI Telegram Command Bot
    After=network.target

    [Service]
    Type=simple
    User=ubuntu
    WorkingDirectory=/home/ubuntu/nexus-ai/TradingAgents
    ExecStart=/home/ubuntu/nexus-ai/TradingAgents/venv/bin/python3 bot/telegram_bot.py
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target

Aktifkan:

    sudo systemctl daemon-reload
    sudo systemctl enable nexus-bot nexus-telegram
    sudo systemctl start nexus-bot nexus-telegram

## 📱 Telegram Commands

| Command | Fungsi |
|---------|--------|
| /status | Lihat watchlist dan status bot |
| /add BTC 4 | Tambah koin, interval 4 jam |
| /remove SOL | Hapus koin dari watchlist |
| /interval BTC 8 | Ubah interval BTC jadi 8 jam |
| /analyze BTC | Analisis sekarang |
| /setmodel analyst MODEL | Ganti model analyst |
| /setmodel reasoning MODEL | Ganti model reasoning |
| /setmodel provider PROVIDER | Ganti provider LLM |
| /confidence 70 | Ubah min confidence |
| /cost | Estimasi biaya API |
| /stop | Jeda semua analisis |
| /start | Aktifkan kembali |
| /restart | Restart bot |
| /help | Tampilkan semua command |

## 💰 Estimasi Biaya per Bulan

| Konfigurasi | Biaya |
|-------------|-------|
| 2 koin, 12 jam, Haiku+Sonnet | ~$8-12 |
| 3 koin, 12 jam, Haiku+Sonnet | ~$12-18 |
| 2 koin, 12 jam, DeepSeek+MiniMax | ~$1-2 |
| VPS | ~$5 |

## 🔄 Ganti Model LLM via Telegram

    /setmodel provider openrouter
    /setmodel analyst qwen/qwen3-30b-a3b
    /setmodel reasoning minimax/minimax-m2.7
    /restart

## 📁 Struktur Project

    TradingAgents/
    tradingagents/dataflows/crypto/
        __init__.py
        binance_crypto.py       Data OHLCV Binance
        coingecko_data.py       Market data + Fear&Greed
        alphavantage_crypto.py  News sentiment
        sentiment_data.py       Fear & Greed history
        technical_analysis.py   EMA/RSI/MACD/SR/TP/SL
        crypto_analyzer.py      7 agent pipeline
    api/
        scheduler.py            APScheduler 24/7
    bot/
        telegram_bot.py         Telegram commands
    .env.example
    .gitignore
    README.md

## ⚠️ Disclaimer

Sistem ini adalah alat bantu analisis, bukan jaminan profit. Crypto trading mengandung risiko tinggi. Selalu paper trading dulu sebelum go live.

## 📄 License

MIT License
