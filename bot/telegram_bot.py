import os
import sys
import logging
import requests
import threading
from dotenv import load_dotenv

sys.path.insert(0, '.')
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def send_msg(text, chat_id=None):
    if chat_id is None:
        chat_id = CHAT_ID
    try:
        r = requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
        return r.json().get("ok", False)
    except Exception as e:
        log.error(f"Send error: {e}")
        return False

def get_updates(offset=None):
    try:
        params = {"timeout": 30, "allowed_updates": ["message"]}
        if offset:
            params["offset"] = offset
        r = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=35)
        return r.json().get("result", [])
    except Exception as e:
        log.error(f"getUpdates error: {e}")
        return []

def get_watchlist():
    watchlist = []
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("WATCH_") and "=" in line:
                key, val = line.split("=", 1)
                pair = key.replace("WATCH_", "").replace("_USDT", "/USDT")
                try:
                    watchlist.append((pair, int(val)))
                except:
                    pass
    return watchlist

def update_env(key, value):
    lines = []
    found = False
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith(key + "="):
                lines.append(f"{key}={value}\n")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"{key}={value}\n")
    with open('.env', 'w') as f:
        f.writelines(lines)

def remove_env(key):
    lines = []
    with open('.env', 'r') as f:
        for line in f:
            if not line.startswith(key + "="):
                lines.append(line)
    with open('.env', 'w') as f:
        f.writelines(lines)

def cmd_help(chat_id):
    msg = """🤖 NEXUS AI — Commands

/status — lihat watchlist & status bot
/add BTC 4 — tambah koin, interval 4 jam
/remove SOL — hapus koin dari watchlist
/interval BTC 8 — ubah interval BTC jadi 8 jam
/analyze BTC — analisis sekarang
/confidence 70 — ubah min confidence
/setmodel analyst MODEL — ganti model analyst
/setmodel reasoning MODEL — ganti model reasoning
/setmodel provider PROVIDER — ganti provider LLM
/cost — estimasi biaya API
/stop — jeda semua analisis
/start — aktifkan kembali
/restart — restart bot
/help — tampilkan menu ini"""
    send_msg(msg, chat_id)

def cmd_status(chat_id):
    watchlist = get_watchlist()
    paper = os.getenv("PAPER_TRADING", "true").lower() == "true"
    mode = "📋 PAPER TRADING" if paper else "💰 LIVE TRADING"
    msg = f"📊 NEXUS AI — Status\n\n"
    msg += f"Mode: {mode}\n"
    msg += f"Min Confidence: {os.getenv('MIN_CONFIDENCE', '65')}%\n\n"
    msg += "Watchlist:\n"
    for pair, interval in watchlist:
        msg += f"  ● {pair} — setiap {interval} jam\n"
    msg += f"\nModel Analyst  : {os.getenv('ANALYST_MODEL', '-')}\n"
    msg += f"Model Reasoning: {os.getenv('REASONING_MODEL', '-')}"
    send_msg(msg, chat_id)

def cmd_add(chat_id, args):
    if len(args) < 2:
        send_msg("Format: /add SYMBOL INTERVAL\nContoh: /add SOL 4", chat_id)
        return
    symbol = args[0].upper()
    try:
        interval = int(args[1])
    except:
        send_msg("Interval harus angka. Contoh: /add SOL 4", chat_id)
        return
    update_env(f"WATCH_{symbol}_USDT", str(interval))
    send_msg(f"✅ {symbol}/USDT ditambahkan\nInterval: setiap {interval} jam\n\nKetik /restart untuk apply.", chat_id)

def cmd_remove(chat_id, args):
    if len(args) < 1:
        send_msg("Format: /remove SYMBOL\nContoh: /remove SOL", chat_id)
        return
    symbol = args[0].upper()
    remove_env(f"WATCH_{symbol}_USDT")
    send_msg(f"✅ {symbol}/USDT dihapus\n\nKetik /restart untuk apply.", chat_id)

def cmd_interval(chat_id, args):
    if len(args) < 2:
        send_msg("Format: /interval SYMBOL JAM\nContoh: /interval BTC 8", chat_id)
        return
    symbol = args[0].upper()
    try:
        interval = int(args[1])
    except:
        send_msg("Interval harus angka.", chat_id)
        return
    update_env(f"WATCH_{symbol}_USDT", str(interval))
    send_msg(f"✅ {symbol}/USDT interval diubah ke {interval} jam\n\nKetik /restart untuk apply.", chat_id)

def cmd_confidence(chat_id, args):
    if len(args) < 1:
        send_msg("Format: /confidence ANGKA\nContoh: /confidence 70", chat_id)
        return
    try:
        val = int(args[0])
    except:
        send_msg("Harus angka 1-100", chat_id)
        return
    update_env("MIN_CONFIDENCE", str(val))
    send_msg(f"✅ Min confidence diubah ke {val}%\n\nKetik /restart untuk apply.", chat_id)

def cmd_setmodel(chat_id, args):
    if len(args) < 2:
        msg = """Format: /setmodel TYPE MODEL

Contoh:
/setmodel analyst claude-haiku-4-5-20251001
/setmodel reasoning claude-sonnet-4-6
/setmodel provider openrouter
/setmodel analyst google/gemini-flash-2.0

Type: analyst / reasoning / provider"""
        send_msg(msg, chat_id)
        return
    model_type = args[0].lower()
    model_name = args[1]
    if model_type == "analyst":
        update_env("ANALYST_MODEL", model_name)
        send_msg(f"✅ Analyst model diubah ke:\n{model_name}\n\nKetik /restart untuk apply.", chat_id)
    elif model_type == "reasoning":
        update_env("REASONING_MODEL", model_name)
        send_msg(f"✅ Reasoning model diubah ke:\n{model_name}\n\nKetik /restart untuk apply.", chat_id)
    elif model_type == "provider":
        update_env("LLM_PROVIDER", model_name)
        send_msg(f"✅ Provider diubah ke:\n{model_name}\n\nKetik /restart untuk apply.", chat_id)
    else:
        send_msg("Type tidak valid.\nGunakan: analyst / reasoning / provider", chat_id)

def cmd_analyze(chat_id, args):
    if len(args) < 1:
        send_msg("Format: /analyze SYMBOL\nContoh: /analyze BTC", chat_id)
        return
    symbol = args[0].upper() + "/USDT"
    send_msg(f"⏳ Memulai analisis {symbol}...\nButuh 2-5 menit.", chat_id)
    def run():
        try:
            from tradingagents.dataflows.crypto.crypto_analyzer import run_analysis
            paper = os.getenv("PAPER_TRADING", "true").lower() == "true"
            result = run_analysis(symbol, paper_trading=paper)
            if result["message"]:
                send_msg(result["message"], chat_id)
            else:
                send_msg(f"📊 {symbol}: {result['decision']} — Confidence {result['confidence']}% (di bawah threshold)", chat_id)
        except Exception as e:
            send_msg(f"❌ Error: {str(e)[:100]}", chat_id)
    threading.Thread(target=run).start()

def cmd_cost(chat_id):
    watchlist = get_watchlist()
    cost_per_cycle = 0.06
    total_day = 0
    msg = "💰 Estimasi biaya Claude API\n\n"
    for pair, interval in watchlist:
        cycles = 24 // interval
        day = cost_per_cycle * cycles
        msg += f"{pair}: ${day:.3f}/hari (${day*30:.2f}/bulan)\n"
        total_day += day
    msg += f"\nTotal: ${total_day:.3f}/hari (${total_day*30:.2f}/bulan)"
    send_msg(msg, chat_id)

def cmd_stop(chat_id):
    update_env("BOT_PAUSED", "true")
    send_msg("⏸ Bot dijeda.\nKetik /start untuk aktifkan kembali.", chat_id)

def cmd_start_bot(chat_id):
    update_env("BOT_PAUSED", "false")
    send_msg("▶️ Bot diaktifkan kembali.", chat_id)

def cmd_restart(chat_id):
    send_msg("🔄 Merestart bot...", chat_id)
    os.system("sudo systemctl restart nexus-bot")

def handle_command(text, chat_id):
    parts = text.strip().split()
    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    commands = {
        "/status": lambda: cmd_status(chat_id),
        "/add": lambda: cmd_add(chat_id, args),
        "/remove": lambda: cmd_remove(chat_id, args),
        "/interval": lambda: cmd_interval(chat_id, args),
        "/confidence": lambda: cmd_confidence(chat_id, args),
        "/setmodel": lambda: cmd_setmodel(chat_id, args),
        "/analyze": lambda: cmd_analyze(chat_id, args),
        "/cost": lambda: cmd_cost(chat_id),
        "/stop": lambda: cmd_stop(chat_id),
        "/start": lambda: cmd_start_bot(chat_id),
        "/restart": lambda: cmd_restart(chat_id),
        "/help": lambda: cmd_help(chat_id),
    }
    if cmd in commands:
        commands[cmd]()
    else:
        send_msg(f"Command tidak dikenal: {cmd}\nKetik /help untuk daftar command.", chat_id)

def run_bot():
    log.info("Telegram command bot dimulai...")
    send_msg("🤖 NEXUS AI command bot aktif! Ketik /help untuk daftar command.")
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message", {})
            text = msg.get("text", "")
            chat_id = str(msg.get("chat", {}).get("id", ""))
            if text.startswith("/"):
                log.info(f"Command: {text}")
                handle_command(text, chat_id)

if __name__ == "__main__":
    run_bot()
