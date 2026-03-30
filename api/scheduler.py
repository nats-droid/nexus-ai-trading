import os
import sys
import logging
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

sys.path.insert(0, '.')
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

from tradingagents.dataflows.crypto.crypto_analyzer import run_analysis

def send_telegram(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": msg}, timeout=10)
        return r.json().get("ok", False)
    except Exception as e:
        log.error(f"Telegram error: {e}")
        return False

def get_watchlist():
    watchlist = []
    for key, val in os.environ.items():
        if key.startswith("WATCH_") and key.endswith("_USDT"):
            pair = key.replace("WATCH_", "").replace("_", "/")
            try:
                interval = int(val)
                watchlist.append((pair, interval))
            except:
                pass
    return watchlist

def analyze_pair(symbol, interval_hours=12):
    log.info(f"Memulai analisis {symbol}...")
    paper = os.getenv("PAPER_TRADING", "true").lower() == "true"
    try:
        result = run_analysis(symbol, timeframe_hours=interval_hours, paper_trading=paper)
        if result["message"]:
            ok = send_telegram(result["message"])
            if ok:
                log.info(f"{symbol}: Sinyal {result['decision']} ({result['confidence']}%) terkirim")
            else:
                log.error(f"{symbol}: Gagal kirim ke Telegram")
        else:
            log.info(f"{symbol}: {result['decision']} confidence {result['confidence']}% — tidak ada sinyal")
    except Exception as e:
        log.error(f"{symbol}: Error — {e}")
        send_telegram(f"⚠️ Error analisis {symbol}: {str(e)[:100]}")

def run_all():
    watchlist = get_watchlist()
    log.info(f"Menjalankan analisis untuk {len(watchlist)} pair...")
    for symbol, interval in watchlist:
        analyze_pair(symbol, interval)

def main():
    watchlist = get_watchlist()
    if not watchlist:
        log.error("Tidak ada watchlist! Cek .env file")
        return

    log.info("="*50)
    log.info("NEXUS AI Trading Bot dimulai")
    log.info(f"Mode: {'PAPER TRADING' if os.getenv('PAPER_TRADING','true').lower()=='true' else 'LIVE TRADING'}")
    log.info(f"Watchlist: {[w[0] for w in watchlist]}")
    log.info("="*50)

    send_telegram("🚀 NEXUS AI Trading Bot dimulai!\n\nWatchlist:\n" +
                  "\n".join([f"• {w[0]} — setiap {w[1]} jam" for w in watchlist]))

    scheduler = BlockingScheduler()

    for symbol, interval in watchlist:
        scheduler.add_job(
            analyze_pair,
            trigger=IntervalTrigger(hours=interval),
            args=[symbol, interval],
            id=f"analyze_{symbol.replace('/','_')}",
            name=f"Analisis {symbol}",
            max_instances=1
        )
        log.info(f"Scheduled: {symbol} setiap {interval} jam")

    run_all()

    log.info("Scheduler aktif. Tekan Ctrl+C untuk berhenti.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot dihentikan.")
        send_telegram("⏹ NEXUS AI Trading Bot dihentikan.")

if __name__ == "__main__":
    main()
