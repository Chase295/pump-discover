import asyncio
import websockets
import json
import time
import re
import aiohttp
import sys
import os
from aiohttp import web
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from datetime import datetime

# Konfiguration aus Environment Variables
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
BATCH_TIMEOUT = int(os.getenv("BATCH_TIMEOUT", "30"))
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://100.93.196.41:5678/webhook/discover")
N8N_WEBHOOK_METHOD = os.getenv("N8N_WEBHOOK_METHOD", "POST").upper()  # POST oder GET
WS_RETRY_DELAY = int(os.getenv("WS_RETRY_DELAY", "3"))
WS_MAX_RETRY_DELAY = int(os.getenv("WS_MAX_RETRY_DELAY", "60"))
N8N_RETRY_DELAY = int(os.getenv("N8N_RETRY_DELAY", "5"))
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8000"))
WS_PING_INTERVAL = int(os.getenv("WS_PING_INTERVAL", "20"))
WS_PING_TIMEOUT = int(os.getenv("WS_PING_TIMEOUT", "10"))
WS_CONNECTION_TIMEOUT = int(os.getenv("WS_CONNECTION_TIMEOUT", "30"))
WS_URI = os.getenv("WS_URI", "wss://pumpportal.fun/api/data")
BAD_NAMES_PATTERN = os.getenv("BAD_NAMES_PATTERN", "test|bot|rug|scam|cant|honey|faucet")

BAD_NAMES = re.compile(rf'({BAD_NAMES_PATTERN})', re.IGNORECASE)

# Logs-Buffer für API-Zugriff
log_buffer = []
MAX_LOG_BUFFER_SIZE = 1000  # Maximale Anzahl Log-Zeilen im Buffer

def add_log(message):
    """Fügt eine Log-Nachricht zum Buffer hinzu"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    log_buffer.append(log_entry)
    # Buffer begrenzen
    if len(log_buffer) > MAX_LOG_BUFFER_SIZE:
        log_buffer.pop(0)
    # Auch auf stdout ausgeben (für Docker Logs)
    print(log_entry, flush=True)

# Prometheus Metrics
coins_received = Counter("pumpfun_coins_received_total", "Anzahl empfangener Coins")
coins_filtered = Counter("pumpfun_coins_filtered_total", "Anzahl gefilterter Coins", ["reason"])
coins_sent = Counter("pumpfun_coins_sent_total", "Anzahl an n8n gesendeter Coins")
batches_sent = Counter("pumpfun_batches_sent_total", "Anzahl gesendeter Batches")
n8n_errors = Counter("pumpfun_n8n_errors_total", "n8n Fehler", ["type"])
ws_reconnects = Counter("pumpfun_ws_reconnects_total", "WebSocket Reconnects")
ws_connected = Gauge("pumpfun_ws_connected", "WebSocket Verbindungsstatus (1=connected)")
n8n_available = Gauge("pumpfun_n8n_available", "n8n Verfügbarkeit (1=available)")
buffer_size = Gauge("pumpfun_buffer_size", "Aktuelle Buffer-Größe")
batch_send_duration = Histogram("pumpfun_batch_send_duration_seconds", "Dauer für Batch-Versand")
uptime_seconds = Gauge("pumpfun_uptime_seconds", "Uptime in Sekunden")
last_coin_timestamp = Gauge("pumpfun_last_coin_timestamp", "Timestamp des letzten empfangenen Coins")
connection_duration = Gauge("pumpfun_connection_duration_seconds", "Dauer der aktuellen Verbindung")

relay_status = {
    "ws_connected": False,
    "n8n_available": True,
    "last_error": None,
    "start_time": time.time(),
    "last_coin_time": None,
    "connection_start": None,
    "last_message_time": None,
    "total_coins": 0,
    "total_batches": 0,
    "reconnect_count": 0
}

async def metrics_handler(request):
    """Prometheus Metrics Endpoint"""
    uptime_seconds.set(time.time() - relay_status["start_time"])
    if relay_status["connection_start"]:
        connection_duration.set(time.time() - relay_status["connection_start"])
    
    return web.Response(
        body=generate_latest(),
        content_type='text/plain; version=0.0.4',
        charset='utf-8'
    )

async def health_check(request):
    """Health Check Endpoint mit detaillierten Infos"""
    ws_status = relay_status.get("ws_connected", False)
    n8n_status = relay_status.get("n8n_available", True)
    uptime = time.time() - relay_status["start_time"]
    last_coin = relay_status.get("last_coin_time")
    last_msg = relay_status.get("last_message_time")
    
    health_data = {
        "status": "healthy" if ws_status else "degraded",
        "ws_connected": ws_status,
        "n8n_available": n8n_status,
        "uptime_seconds": int(uptime),
        "total_coins": relay_status["total_coins"],
        "total_batches": relay_status["total_batches"],
        "last_coin_ago": int(time.time() - last_coin) if last_coin else None,
        "last_message_ago": int(time.time() - last_msg) if last_msg else None,
        "reconnect_count": relay_status["reconnect_count"],
        "last_error": relay_status.get("last_error")
    }
    
    status_code = 200 if ws_status else 503
    return web.json_response(health_data, status=status_code)

async def logs_handler(request):
    """Logs Endpoint für API-Zugriff"""
    lines = int(request.query.get("lines", "100"))
    # Hole die letzten N Zeilen (neueste zuerst)
    logs = log_buffer[-lines:] if lines <= len(log_buffer) else log_buffer
    logs.reverse()  # Neueste oben
    return web.json_response({
        "logs": logs,
        "total_lines": len(log_buffer),
        "requested_lines": lines
    })

async def start_health_server():
    """Startet Health + Metrics Server"""
    app = web.Application()
    app.add_routes([
        web.get("/health", health_check),
        web.get("/metrics", metrics_handler),
        web.get("/logs", logs_handler)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", HEALTH_PORT)
    add_log(f"🏥 Health-Check Server läuft auf Port {HEALTH_PORT}")
    add_log(f"📊 Prometheus Metrics auf http://localhost:{HEALTH_PORT}/metrics")
    await site.start()

async def send_to_n8n(session, batch):
    """Sendet Batch an n8n mit Retry-Logik"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with batch_send_duration.time():
                payload = {
                    "source": "pump_fun_relay",
                    "count": len(batch),
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": batch
                }
                
                # Unterstützung für GET und POST
                if N8N_WEBHOOK_METHOD == "GET":
                    # Für GET: Daten als JSON im Query-Parameter
                    # n8n Webhooks können GET mit Body nicht, daher als Query-Parameter
                    import urllib.parse
                    json_data = json.dumps(payload)
                    # URL-safe encoding
                    encoded_data = urllib.parse.quote(json_data)
                    url_with_params = f"{N8N_WEBHOOK_URL}?data={encoded_data}"
                    
                    async with session.get(
                        url_with_params,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        status = resp.status
                else:
                    # POST (Standard)
                    async with session.post(
                        N8N_WEBHOOK_URL,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        status = resp.status
                
                # Status-Verarbeitung (gleich für GET und POST)
                if status:
                    if status == 200:
                        add_log(f"📦 Paket ({len(batch)} Coins) an n8n übergeben! ✅")
                        relay_status["n8n_available"] = True
                        relay_status["total_batches"] += 1
                        n8n_available.set(1)
                        batches_sent.inc()
                        coins_sent.inc(len(batch))
                        return True
                    elif status == 404:
                        add_log(f"❌ n8n Fehler 404: Bitte in n8n auf 'Execute Workflow' klicken!")
                        relay_status["n8n_available"] = False
                        relay_status["last_error"] = "n8n_404"
                        n8n_available.set(0)
                        n8n_errors.labels(type="404").inc()
                        return False
                    else:
                        add_log(f"⚠️ n8n Status: {status} (Retry {retry_count + 1}/{max_retries})")
                        n8n_errors.labels(type=f"status_{status}").inc()
                        retry_count += 1
        except asyncio.TimeoutError:
            add_log(f"⚠️ n8n Timeout (Retry {retry_count + 1}/{max_retries})")
            relay_status["n8n_available"] = False
            relay_status["last_error"] = "n8n_timeout"
            n8n_available.set(0)
            n8n_errors.labels(type="timeout").inc()
            retry_count += 1
        except aiohttp.ClientError as e:
            add_log(f"⚠️ n8n Connection Error: {e} (Retry {retry_count + 1}/{max_retries})")
            relay_status["n8n_available"] = False
            relay_status["last_error"] = f"n8n_connection: {str(e)[:50]}"
            n8n_available.set(0)
            n8n_errors.labels(type="connection").inc()
            retry_count += 1
        except Exception as e:
            add_log(f"⚠️ n8n Unerwarteter Fehler: {e}")
            relay_status["n8n_available"] = False
            relay_status["last_error"] = f"n8n_unknown: {str(e)[:50]}"
            n8n_available.set(0)
            n8n_errors.labels(type="unknown").inc()
            return False
        
        if retry_count < max_retries:
            await asyncio.sleep(N8N_RETRY_DELAY * retry_count)
    
    relay_status["n8n_available"] = False
    relay_status["last_error"] = "n8n_max_retries"
    n8n_available.set(0)
    add_log(f"❌ n8n nicht erreichbar nach {max_retries} Versuchen")
    return False

async def listen_and_relay():
    """Hauptfunktion mit verbesserter Verbindungsstabilität"""
    add_log("🚀 Starte Relay (Mit Spam-Burst-Filter & Prometheus Metrics)...")
    buffer = []
    last_flush = time.time()
    reconnect_count = 0
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                    add_log(f"🔌 Verbinde zu Pump.fun... (Versuch #{reconnect_count + 1})")
                
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                async with websockets.connect(
                    WS_URI,
                    ping_interval=WS_PING_INTERVAL,
                    ping_timeout=WS_PING_TIMEOUT,
                    close_timeout=10,
                    max_size=2**23,
                    compression=None,
                    ssl=ssl_context
                ) as ws:
                    relay_status["ws_connected"] = True
                    relay_status["connection_start"] = time.time()
                    relay_status["last_error"] = None
                    ws_connected.set(1)
                    reconnect_count = 0
                    relay_status["reconnect_count"] = 0
                    
                    await ws.send(json.dumps({"method": "subscribeNewToken"}))
                    add_log("✅ Verbunden! Warte auf Coins...")
                    
                    last_message_time = time.time()
                    
                    while True:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                            last_message_time = time.time()
                            relay_status["last_message_time"] = last_message_time
                            
                            data = json.loads(msg)
                            coins_received.inc()
                            
                            if not data.get("mint"):
                                continue
                            
                            name = data.get("name", "").strip()
                            symbol = data.get("symbol", "???").strip()
                            
                            if BAD_NAMES.search(name):
                                coins_filtered.labels(reason="bad_name").inc()
                                continue
                            
                            is_spam_burst = False
                            for buffered_coin in buffer:
                                if (buffered_coin.get("name", "").strip() == name or 
                                    buffered_coin.get("symbol", "").strip() == symbol):
                                    is_spam_burst = True
                                    break
                            
                            if is_spam_burst:
                                print(f"♻️ Spam-Burst: {symbol}", flush=True)
                                coins_filtered.labels(reason="spam_burst").inc()
                                continue
                            
                            # Berechne price_sol und füge pool_address hinzu
                            v_tokens = data.get("vTokensInBondingCurve", 0)
                            market_cap = data.get("marketCapSol", 0)
                            
                            # price_sol = marketCapSol / vTokensInBondingCurve (wenn vTokens > 0)
                            if v_tokens and v_tokens > 0:
                                price_sol = market_cap / v_tokens
                            else:
                                price_sol = 0
                            
                            # Füge berechnete Felder hinzu
                            data["price_sol"] = price_sol
                            data["pool_address"] = data.get("bondingCurveKey", "")
                            
                            buffer.append(data)
                            relay_status["last_coin_time"] = time.time()
                            relay_status["total_coins"] += 1
                            last_coin_timestamp.set(time.time())
                            buffer_size.set(len(buffer))
                            add_log(f"➕ {symbol}")
                            
                        except asyncio.TimeoutError:
                            if time.time() - last_message_time > WS_CONNECTION_TIMEOUT:
                                add_log(f"⚠️ Keine Nachrichten seit {WS_CONNECTION_TIMEOUT}s - Reconnect")
                                raise websockets.exceptions.ConnectionClosed(1006, "Timeout")
                        
                        except websockets.exceptions.ConnectionClosed as e:
                            add_log(f"🔌 WebSocket Verbindung geschlossen: {e}")
                            relay_status["ws_connected"] = False
                            relay_status["last_error"] = f"ws_closed: {str(e)[:100]}"
                            ws_connected.set(0)
                            break
                        
                        except json.JSONDecodeError as e:
                            add_log(f"⚠️ JSON Fehler: {e}")
                            continue
                        
                        except Exception as e:
                            add_log(f"⚠️ WS Receive Error: {e}")
                            relay_status["last_error"] = f"ws_error: {str(e)[:100]}"
                            break
                        
                        is_full = len(buffer) >= BATCH_SIZE
                        is_timeout = (time.time() - last_flush) > BATCH_TIMEOUT
                        
                        if buffer and (is_full or is_timeout):
                            add_log(f"🚚 Sende {len(buffer)} Coins an n8n...")
                            success = await send_to_n8n(session, buffer)
                            if success:
                                buffer = []
                                buffer_size.set(0)
                            last_flush = time.time()
                            
            except websockets.exceptions.WebSocketException as e:
                relay_status["ws_connected"] = False
                relay_status["last_error"] = f"ws_exception: {str(e)[:100]}"
                ws_connected.set(0)
                ws_reconnects.inc()
                add_log(f"❌ WebSocket Exception: {e}")
                reconnect_count += 1
                relay_status["reconnect_count"] = reconnect_count
            
            except Exception as e:
                relay_status["ws_connected"] = False
                relay_status["last_error"] = f"unexpected: {str(e)[:100]}"
                ws_connected.set(0)
                ws_reconnects.inc()
                add_log(f"❌ Unerwarteter Fehler: {e}")
                reconnect_count += 1
                relay_status["reconnect_count"] = reconnect_count
            
            if buffer:
                add_log(f"⚠️ Buffer nicht leer ({len(buffer)} Coins). Sende vor Reconnect...")
                await send_to_n8n(session, buffer)
                buffer = []
                buffer_size.set(0)
                last_flush = time.time()
            
            delay = min(WS_RETRY_DELAY * (1 + reconnect_count * 0.5), WS_MAX_RETRY_DELAY)
            add_log(f"⏳ Reconnect in {delay:.1f}s...")
            await asyncio.sleep(delay)

async def main():
    """Hauptfunktion"""
    print(f"🔧 Konfiguration:", flush=True)
    print(f"  - BATCH_SIZE: {BATCH_SIZE}", flush=True)
    print(f"  - BATCH_TIMEOUT: {BATCH_TIMEOUT}s", flush=True)
    print(f"  - WS_PING_INTERVAL: {WS_PING_INTERVAL}s", flush=True)
    print(f"  - WS_PING_TIMEOUT: {WS_PING_TIMEOUT}s", flush=True)
    print(f"  - WS_CONNECTION_TIMEOUT: {WS_CONNECTION_TIMEOUT}s", flush=True)
    print(f"  - N8N_WEBHOOK_URL: {N8N_WEBHOOK_URL}", flush=True)
    await asyncio.gather(listen_and_relay(), start_health_server())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutdown...", flush=True)

