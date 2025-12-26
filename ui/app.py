import streamlit as st
import requests
import json
import yaml
import os
from datetime import datetime
import time
from pathlib import Path
import re
from urllib.parse import urlparse
import psycopg2
from psycopg2 import sql

# Konfiguration
CONFIG_FILE = "/app/config/config.yaml"
ENV_FILE = "/app/.env"  # .env Datei für Docker Compose
RELAY_SERVICE = os.getenv("RELAY_SERVICE", "pump-discover-relay")  # Container-Name
RELAY_PORT = int(os.getenv("RELAY_PORT", "8000"))
COOLIFY_MODE = os.getenv("COOLIFY_MODE", "false").lower() == "true"  # Coolify-Modus (kein Docker Socket)

st.set_page_config(
    page_title="Pump Discover - Control Panel",
    page_icon="🚀",
    layout="wide"
)

def load_config():
    """Lädt Konfiguration aus YAML-Datei oder .env"""
    # Versuche zuerst YAML
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
            if config:
                return config
    
    # Fallback: Lade aus .env
    env_paths = ["/app/.env", "/app/../.env", "/app/config/.env", ".env"]
    config = {}
    env_file_found = False
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            env_file_found = True
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Konvertiere Zahlen
                        if value.isdigit():
                            config[key] = int(value)
                        else:
                            config[key] = value
            break
    
    # Wenn keine Config-Datei gefunden wurde, erstelle .env mit Default-Werten
    if not env_file_found and not config:
        default_config = get_default_config()
        # Erstelle .env Datei mit Default-Werten
        save_config(default_config)
        return default_config
    
    # Wenn Config aus .env geladen wurde, aber leer ist, verwende Defaults
    if not config:
        return get_default_config()
    
    return config

def save_config(config):
    """Speichert Konfiguration in YAML-Datei UND .env Datei"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    
    # Speichere YAML (für UI)
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    # Speichere .env (für Docker Compose / Relay Service)
    n8n_url = config.get('N8N_WEBHOOK_URL', '')
    env_content = f"""# ============================================================================
# PUMP DISCOVER - Umgebungsvariablen
# ============================================================================
# Diese Datei wird automatisch von der Streamlit UI verwaltet.
# Änderungen werden beim Service-Neustart übernommen.
# ============================================================================

# Batch-Einstellungen
BATCH_SIZE={config.get('BATCH_SIZE', 10)}
BATCH_TIMEOUT={config.get('BATCH_TIMEOUT', 30)}

# n8n Webhook (Lass leer, wenn n8n noch nicht konfiguriert ist)
N8N_WEBHOOK_URL={n8n_url}
N8N_WEBHOOK_METHOD={config.get('N8N_WEBHOOK_METHOD', 'POST')}

# WebSocket Einstellungen
WS_URI={config.get('WS_URI', 'wss://pumpportal.fun/api/data')}
WS_RETRY_DELAY={config.get('WS_RETRY_DELAY', 3)}
WS_MAX_RETRY_DELAY={config.get('WS_MAX_RETRY_DELAY', 60)}
WS_PING_INTERVAL={config.get('WS_PING_INTERVAL', 20)}
WS_PING_TIMEOUT={config.get('WS_PING_TIMEOUT', 10)}
WS_CONNECTION_TIMEOUT={config.get('WS_CONNECTION_TIMEOUT', 30)}

# n8n Retry-Einstellungen
N8N_RETRY_DELAY={config.get('N8N_RETRY_DELAY', 5)}

# Filter-Einstellungen
BAD_NAMES_PATTERN={config.get('BAD_NAMES_PATTERN', 'test|bot|rug|scam|cant|honey|faucet')}

# Health-Check Port
HEALTH_PORT={config.get('HEALTH_PORT', 8000)}

# Datenbank-Einstellungen (für UI DB-Prüfung)
DB_HOST={config.get('DB_HOST', 'localhost')}
DB_PORT={config.get('DB_PORT', 5432)}
DB_NAME={config.get('DB_NAME', 'pump_discover')}
DB_USER={config.get('DB_USER', 'postgres')}
DB_PASSWORD={config.get('DB_PASSWORD', '')}

# Docker Compose Ports
RELAY_PORT=8000
UI_PORT=8501
"""
    
    # Speichere .env Datei in Config-Volume (wird vom Relay-Service geladen)
    env_paths = [
        "/app/config/.env",  # Config-Volume (wichtig für Coolify!)
        "/app/.env",  # Fallback
        "/app/../.env",  # Projekt-Root (wenn gemountet)
    ]
    
    saved_env = False
    for env_path in env_paths:
        try:
            env_dir = os.path.dirname(env_path)
            if env_dir and env_dir != "/app":
                os.makedirs(env_dir, exist_ok=True)
            with open(env_path, 'w') as f:
                f.write(env_content)
            saved_env = True
            break
        except Exception as e:
            continue
    
    # Wenn .env nicht geschrieben werden konnte, versuche über Docker Compose
    if not saved_env:
        try:
            import subprocess
            # Schreibe temporäre .env und kopiere sie
            temp_env = "/tmp/.env"
            with open(temp_env, 'w') as f:
                f.write(env_content)
            # Versuche über docker compose exec zu kopieren (falls möglich)
        except:
            pass
    
    return True  # YAML wurde immer gespeichert

def get_default_config():
    """Gibt Standard-Konfiguration zurück"""
    return {
        "BATCH_SIZE": 10,
        "BATCH_TIMEOUT": 30,
        "N8N_WEBHOOK_URL": "",  # Leer als Default
        "N8N_WEBHOOK_METHOD": "POST",
        "WS_RETRY_DELAY": 3,
        "WS_MAX_RETRY_DELAY": 60,
        "N8N_RETRY_DELAY": 5,
        "WS_PING_INTERVAL": 20,
        "WS_PING_TIMEOUT": 10,
        "WS_CONNECTION_TIMEOUT": 30,
        "WS_URI": "wss://pumpportal.fun/api/data",
        "BAD_NAMES_PATTERN": "test|bot|rug|scam|cant|honey|faucet",
        "HEALTH_PORT": 8000,
        "DB_HOST": "localhost",
        "DB_PORT": 5432,
        "DB_NAME": "pump_discover",
        "DB_USER": "postgres",
        "DB_PASSWORD": ""  # Leer als Default
    }

def validate_url(url, allow_empty=False):
    """Validiert eine URL"""
    if allow_empty and not url:
        return True, None
    if not url:
        return False, "URL darf nicht leer sein"
    try:
        result = urlparse(url)
        if not result.scheme or not result.netloc:
            return False, "Ungültige URL-Format"
        if result.scheme not in ["http", "https", "wss", "ws"]:
            return False, f"Ungültiges Protokoll: {result.scheme}. Erlaubt: http, https, ws, wss"
        return True, None
    except Exception as e:
        return False, f"URL-Validierungsfehler: {str(e)}"

def validate_port(port):
    """Validiert einen Port"""
    try:
        port_int = int(port)
        if 1 <= port_int <= 65535:
            return True, None
        return False, "Port muss zwischen 1 und 65535 liegen"
    except ValueError:
        return False, "Port muss eine Zahl sein"

def validate_regex(pattern, allow_empty=False):
    """Validiert ein Regex-Pattern"""
    if allow_empty and not pattern:
        return True, None
    if not pattern:
        return False, "Pattern darf nicht leer sein"
    try:
        re.compile(pattern)
        return True, None
    except re.error as e:
        return False, f"Ungültiges Regex-Pattern: {str(e)}"

def get_relay_health():
    """Holt Health-Status vom Relay-Service"""
    try:
        response = requests.get(f"http://{RELAY_SERVICE}:{RELAY_PORT}/health", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_relay_metrics():
    """Holt Prometheus Metrics vom Relay-Service"""
    try:
        response = requests.get(f"http://{RELAY_SERVICE}:{RELAY_PORT}/metrics", timeout=2)
        if response.status_code == 200:
            return response.text
    except:
        pass
    return None

def reload_config():
    """Lädt die Konfiguration im Relay-Service neu (ohne Neustart)"""
    try:
        response = requests.post(f"http://{RELAY_SERVICE}:{RELAY_PORT}/reload-config", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("message", "Konfiguration wurde neu geladen")
        else:
            return False, f"Fehler: HTTP {response.status_code}"
    except Exception as e:
        return False, f"Fehler beim Neuladen: {str(e)}"

def restart_service():
    """Startet Relay-Service neu (über Docker API, damit .env neu geladen wird)"""
    # Coolify-Modus: Versuche zuerst Config-Neuladen über API
    if COOLIFY_MODE:
        success, message = reload_config()
        if success:
            return True, f"✅ {message} (ohne Neustart - funktioniert in Coolify!)"
        else:
            return False, f"⚠️ Coolify-Modus: {message}. Falls das nicht funktioniert, starte den 'api' Service im Coolify-Dashboard neu."
    
    try:
        import docker
        client = docker.from_env()
        
        # Versuche verschiedene Container-Namen
        container_names = ["pump-discover-relay", "relay", RELAY_SERVICE]
        container = None
        for name in container_names:
            try:
                container = client.containers.get(name)
                break
            except docker.errors.NotFound:
                continue
        
        if not container:
            return False, "Container 'pump-discover-relay' nicht gefunden"
        
        # Stoppe Container
        container.stop(timeout=10)
        
        # Starte Container neu (lädt .env neu)
        container.start()
        
        return True, "Service erfolgreich neu gestartet! Neue Environment Variables werden geladen."
        
    except ImportError:
        # Docker Python Client nicht verfügbar - versuche über Docker Socket direkt
        try:
            import subprocess
            import os
            
            # Prüfe ob docker compose verfügbar ist
            docker_compose_cmd = None
            for cmd in ["docker", "docker-compose"]:
                try:
                    result = subprocess.run(
                        [cmd, "--version"],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        docker_compose_cmd = cmd
                        break
                except:
                    continue
            
            if not docker_compose_cmd:
                return False, "Docker/Docker Compose nicht gefunden. Bitte manuell neu starten: docker compose restart relay"
            
            # Versuche über Docker Socket zu arbeiten
            # Finde das Projekt-Verzeichnis (wo docker-compose.yml ist)
            compose_file = "/app/../docker-compose.yml"
            if not os.path.exists(compose_file):
                compose_file = "/app/docker-compose.yml"
            
            if os.path.exists(compose_file):
                work_dir = os.path.dirname(compose_file)
                result = subprocess.run(
                    [docker_compose_cmd, "restart", "relay"],
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return True, "Service neu gestartet (via docker compose)"
                else:
                    return False, f"Docker Compose Fehler: {result.stderr}"
            else:
                return False, "docker-compose.yml nicht gefunden"
                
        except Exception as e:
            return False, f"Fehler: {str(e)}"
    except Exception as e:
        return False, f"Fehler: {str(e)}"
    except ImportError:
        # Fallback: Docker Python Client nicht verfügbar
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "compose", "restart", "relay"],
                cwd="/app",
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, "Service erfolgreich neu gestartet (via docker compose)"
            else:
                return False, f"Docker Compose Fehler: {result.stderr}"
        except Exception as e:
            return False, f"Fehler: {str(e)}"
    except Exception as e:
        return False, f"Fehler: {str(e)}"

def check_database_connection():
    """Prüft DB-Verbindung und Tabellen-Existenz"""
    # Lade DB-Config aus Config-Datei oder Environment Variables
    config = load_config()
    
    db_config = {
        'host': config.get('DB_HOST', os.getenv('DB_HOST', 'localhost')),
        'port': config.get('DB_PORT', os.getenv('DB_PORT', '5432')),
        'database': config.get('DB_NAME', os.getenv('DB_NAME', 'pump_discover')),
        'user': config.get('DB_USER', os.getenv('DB_USER', 'postgres')),
        'password': config.get('DB_PASSWORD', os.getenv('DB_PASSWORD', ''))
    }
    
    result = {
        'connected': False,
        'tables': {
            'discovered_coins': False,
            'coin_streams': False,
            'ref_coin_phases': False
        },
        'error': None,
        'configured': False
    }
    
    # Prüfe ob DB-Credentials gesetzt sind
    if not db_config.get('password'):
        result['error'] = 'DB-Credentials nicht konfiguriert (DB_PASSWORD fehlt)'
        return result
    
    result['configured'] = True
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Prüfe Tabellen-Existenz
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('discovered_coins', 'coin_streams', 'ref_coin_phases')
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        result['connected'] = True
        result['tables']['discovered_coins'] = 'discovered_coins' in existing_tables
        result['tables']['coin_streams'] = 'coin_streams' in existing_tables
        result['tables']['ref_coin_phases'] = 'ref_coin_phases' in existing_tables
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

def get_service_logs(lines=100):
    """Holt Logs vom Relay-Service"""
    # Coolify-Modus: Logs über API abrufen
    if COOLIFY_MODE:
        try:
            response = requests.get(f"http://{RELAY_SERVICE}:{RELAY_PORT}/logs?lines={lines}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logs = data.get("logs", [])
                if logs:
                    return '\n'.join(logs)
                else:
                    return "[Keine Logs verfügbar - Service startet gerade oder noch keine Logs generiert]"
            else:
                return f"❌ Fehler beim Abrufen der Logs: HTTP {response.status_code}\n\n💡 Prüfe, ob der Relay-Service läuft."
        except requests.exceptions.ConnectionError:
            return f"❌ Verbindungsfehler: Kann Relay-Service nicht erreichen (http://{RELAY_SERVICE}:{RELAY_PORT})\n\n💡 Prüfe, ob der Service läuft."
        except Exception as e:
            return f"❌ Fehler beim Abrufen der Logs über API: {str(e)}\n\n💡 Falls das nicht funktioniert, verwende die Logs im Coolify-Dashboard."
    
    # Normale Docker-Methode (wenn Docker Socket verfügbar)
    try:
        import docker
        client = docker.from_env()
        # Versuche verschiedene Container-Namen
        container_names = [RELAY_SERVICE, "pump-discover-relay", "relay"]
        container = None
        for name in container_names:
            try:
                container = client.containers.get(name)
                break
            except:
                continue
        if container:
            logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
            # Logs umdrehen: Neueste oben
            log_lines = logs.split('\n')
            log_lines.reverse()
            return '\n'.join(log_lines)
        else:
            raise Exception("Container nicht gefunden")
    except ImportError:
        # Fallback: Docker Python Client nicht verfügbar
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "compose", "logs", "--tail", str(lines), "relay"],
                cwd="/app",
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Logs umdrehen: Neueste oben
                log_lines = result.stdout.split('\n')
                log_lines.reverse()
                return '\n'.join(log_lines)
            else:
                return f"Fehler beim Abrufen der Logs: {result.stderr}"
        except Exception as e:
            return f"Fehler beim Abrufen der Logs: {str(e)}"
    except Exception as e:
        return f"Fehler beim Abrufen der Logs: {str(e)}"

# Header
st.title("🚀 Pump Discover - Control Panel")

# Tabs Navigation
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "⚙️ Konfiguration", "📋 Logs", "📈 Metriken", "ℹ️ Info"])

# Dashboard Tab
with tab1:
    st.title("📊 Dashboard")
    
    # Health Status
    health = get_relay_health()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if health:
            status = "🟢 Online" if health.get("ws_connected") else "🔴 Offline"
            st.metric("Status", status)
        else:
            st.metric("Status", "❌ Nicht erreichbar")
    
    with col2:
        if health:
            st.metric("Coins empfangen", health.get("total_coins", 0))
        else:
            st.metric("Coins empfangen", "-")
    
    with col3:
        if health:
            st.metric("Batches gesendet", health.get("total_batches", 0))
        else:
            st.metric("Batches gesendet", "-")
    
    with col4:
        if health:
            uptime = health.get("uptime_seconds", 0)
            hours = uptime // 3600
            minutes = (uptime % 3600) // 60
            st.metric("Uptime", f"{int(hours)}h {int(minutes)}m")
        else:
            st.metric("Uptime", "-")
    
    # Metriken direkt im Dashboard anzeigen
    st.subheader("📈 Live-Metriken")
    metrics = get_relay_metrics()
    
    if metrics:
        metrics_dict = {}
        for line in metrics.split('\n'):
            if line and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 2:
                    metric_name = parts[0]
                    try:
                        metric_value = float(parts[1]) if '.' in parts[1] else int(parts[1])
                        metrics_dict[metric_name] = metric_value
                    except:
                        metrics_dict[metric_name] = parts[1]
        
        # Wichtige Metriken in Spalten
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            coins_received = metrics_dict.get('pumpfun_coins_received_total', 0)
            st.metric("Coins empfangen (Total)", f"{coins_received:,}")
        
        with col_m2:
            coins_sent = metrics_dict.get('pumpfun_coins_sent_total', 0)
            st.metric("Coins gesendet (Total)", f"{coins_sent:,}")
        
        with col_m3:
            coins_filtered = metrics_dict.get('pumpfun_coins_filtered_total', 0)
            st.metric("Coins gefiltert (Total)", f"{coins_filtered:,}")
        
        with col_m4:
            batches_sent = metrics_dict.get('pumpfun_batches_sent_total', 0)
            st.metric("Batches gesendet (Total)", f"{batches_sent:,}")
        
        col_m5, col_m6, col_m7, col_m8 = st.columns(4)
        
        with col_m5:
            ws_connected = metrics_dict.get('pumpfun_ws_connected', 0)
            status_text = "🟢 Verbunden" if ws_connected == 1 else "🔴 Getrennt"
            st.metric("WebSocket Status", status_text)
        
        with col_m6:
            n8n_available = metrics_dict.get('pumpfun_n8n_available', 0)
            status_text = "🟢 Verfügbar" if n8n_available == 1 else "🔴 Nicht verfügbar"
            st.metric("n8n Status", status_text)
        
        with col_m7:
            buffer_size = metrics_dict.get('pumpfun_buffer_size', 0)
            st.metric("Buffer Größe", f"{buffer_size}")
        
        with col_m8:
            ws_reconnects = metrics_dict.get('pumpfun_ws_reconnects_total', 0)
            st.metric("WebSocket Reconnects", f"{ws_reconnects}")
    else:
        st.warning("⚠️ Metriken konnten nicht abgerufen werden. Bitte prüfe, ob der Relay-Service läuft.")
    
    # Datenbank-Verbindungsprüfung
    st.subheader("🗄️ Datenbank-Status")
    db_status = check_database_connection()
    
    if not db_status['configured']:
        st.info("ℹ️ DB-Credentials nicht konfiguriert. Bitte konfiguriere die Datenbank-Verbindung im **Konfigurations-Tab** (⚙️ Konfiguration).")
    else:
        col_db1, col_db2, col_db3, col_db4 = st.columns(4)
        
        with col_db1:
            if db_status['connected']:
                st.success("✅ Verbunden")
            else:
                st.error("❌ Nicht verbunden")
                if db_status['error']:
                    st.caption(f"Fehler: {db_status['error'][:50]}")
        
        with col_db2:
            if db_status['tables']['discovered_coins']:
                st.success("✅ discovered_coins")
            else:
                st.error("❌ discovered_coins fehlt")
        
        with col_db3:
            if db_status['tables']['coin_streams']:
                st.success("✅ coin_streams")
            else:
                st.warning("⚠️ coin_streams fehlt")
        
        with col_db4:
            if db_status['tables']['ref_coin_phases']:
                st.success("✅ ref_coin_phases")
            else:
                st.warning("⚠️ ref_coin_phases fehlt")
    
    # Detaillierte Informationen
    if health:
        st.subheader("📈 Detaillierte Informationen")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**WebSocket Status:**")
            st.write(f"- Verbunden: {'✅' if health.get('ws_connected') else '❌'}")
            st.write(f"- Reconnects: {health.get('reconnect_count', 0)}")
            if health.get('last_message_ago'):
                st.write(f"- Letzte Nachricht: vor {health.get('last_message_ago')}s")
            
            st.write("**n8n Status:**")
            st.write(f"- Verfügbar: {'✅' if health.get('n8n_available') else '❌'}")
            if health.get('last_error'):
                st.write(f"- Letzter Fehler: {health.get('last_error')}")
        
        with col2:
            st.write("**Coin-Statistiken:**")
            st.write(f"- Gesamt empfangen: {health.get('total_coins', 0)}")
            st.write(f"- Gesamt Batches: {health.get('total_batches', 0)}")
            if health.get('last_coin_ago'):
                st.write(f"- Letzter Coin: vor {health.get('last_coin_ago')}s")
    
    # Neustart-Button
    st.subheader("🔧 Service-Management")
    
    # Coolify-Hinweis
    if COOLIFY_MODE:
        st.info("🌐 **Coolify-Modus aktiv:** Konfiguration wird über API neu geladen (kein Neustart nötig!)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Konfiguration neu laden", type="primary"):
            with st.spinner("Konfiguration wird neu geladen..."):
                success, message = reload_config()
                if success:
                    st.success(message)
                    st.info("💡 Die neue Konfiguration ist jetzt aktiv! Kein Neustart nötig.")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(message)
                    if COOLIFY_MODE:
                        st.info("💡 **Hinweis:** Falls das nicht funktioniert, starte den 'api' Service im Coolify-Dashboard neu.")
    
    with col2:
        if st.button("🔄 Seite aktualisieren"):
            st.rerun()
    
    # Auto-Refresh
    if st.checkbox("🔄 Auto-Refresh (5s)"):
        time.sleep(5)
        st.rerun()

# Konfiguration Tab
with tab2:
    
    config = load_config()
    
    st.info("💡 Änderungen werden in der Konfigurationsdatei gespeichert. Ein Service-Neustart ist erforderlich, damit die Änderungen wirksam werden.")
    
    with st.form("config_form"):
        st.subheader("📦 Batch-Einstellungen")
        config["BATCH_SIZE"] = st.number_input("Batch Größe", min_value=1, max_value=100, value=config.get("BATCH_SIZE", 10))
        config["BATCH_TIMEOUT"] = st.number_input("Batch Timeout (Sekunden)", min_value=1, max_value=300, value=config.get("BATCH_TIMEOUT", 30))
        
        st.subheader("🔗 n8n Einstellungen")
        config["N8N_WEBHOOK_URL"] = st.text_input("n8n Webhook URL", value=config.get("N8N_WEBHOOK_URL", ""), help="Lass leer, wenn n8n noch nicht konfiguriert ist")
        if config["N8N_WEBHOOK_URL"]:
            url_valid, url_error = validate_url(config["N8N_WEBHOOK_URL"], allow_empty=True)
            if not url_valid:
                st.error(f"❌ {url_error}")
        config["N8N_WEBHOOK_METHOD"] = st.selectbox("n8n Webhook Methode", ["POST", "GET"], index=["POST", "GET"].index(config.get("N8N_WEBHOOK_METHOD", "POST")))
        config["N8N_RETRY_DELAY"] = st.number_input("n8n Retry Delay (Sekunden)", min_value=1, max_value=60, value=config.get("N8N_RETRY_DELAY", 5))
        
        st.subheader("🌐 WebSocket Einstellungen")
        config["WS_URI"] = st.text_input("WebSocket URI", value=config.get("WS_URI", ""))
        if config["WS_URI"]:
            ws_valid, ws_error = validate_url(config["WS_URI"], allow_empty=False)
            if not ws_valid:
                st.error(f"❌ {ws_error}")
        config["WS_RETRY_DELAY"] = st.number_input("WS Retry Delay (Sekunden)", min_value=1, max_value=300, value=config.get("WS_RETRY_DELAY", 3))
        config["WS_MAX_RETRY_DELAY"] = st.number_input("WS Max Retry Delay (Sekunden)", min_value=1, max_value=600, value=config.get("WS_MAX_RETRY_DELAY", 60))
        config["WS_PING_INTERVAL"] = st.number_input("WS Ping Interval (Sekunden)", min_value=1, max_value=300, value=config.get("WS_PING_INTERVAL", 20))
        config["WS_PING_TIMEOUT"] = st.number_input("WS Ping Timeout (Sekunden)", min_value=1, max_value=300, value=config.get("WS_PING_TIMEOUT", 10))
        config["WS_CONNECTION_TIMEOUT"] = st.number_input("WS Connection Timeout (Sekunden)", min_value=1, max_value=600, value=config.get("WS_CONNECTION_TIMEOUT", 30))
        
        st.subheader("🚫 Filter-Einstellungen")
        config["BAD_NAMES_PATTERN"] = st.text_input("Bad Names Pattern (Regex)", value=config.get("BAD_NAMES_PATTERN", ""), help="Regex-Pattern für zu filternde Namen (z.B. 'test|bot|rug')")
        if config["BAD_NAMES_PATTERN"]:
            regex_valid, regex_error = validate_regex(config["BAD_NAMES_PATTERN"], allow_empty=True)
            if not regex_valid:
                st.error(f"❌ {regex_error}")
        
        st.subheader("🗄️ Datenbank-Einstellungen")
        config["DB_HOST"] = st.text_input("DB Host", value=config.get("DB_HOST", "localhost"), help="PostgreSQL Host-Adresse")
        config["DB_PORT"] = st.number_input("DB Port", min_value=1, max_value=65535, value=int(config.get("DB_PORT", 5432)))
        config["DB_NAME"] = st.text_input("DB Name", value=config.get("DB_NAME", "pump_discover"), help="Datenbank-Name")
        config["DB_USER"] = st.text_input("DB User", value=config.get("DB_USER", "postgres"), help="Datenbank-Benutzer")
        config["DB_PASSWORD"] = st.text_input("DB Password", value=config.get("DB_PASSWORD", ""), type="password", help="Datenbank-Passwort")
        
        st.subheader("🔧 Sonstige Einstellungen")
        config["HEALTH_PORT"] = st.number_input("Health Port", min_value=1000, max_value=65535, value=config.get("HEALTH_PORT", 8000))
        port_valid, port_error = validate_port(config["HEALTH_PORT"])
        if not port_valid:
            st.error(f"❌ {port_error}")
        
        col1, col2 = st.columns(2)
        with col1:
            save_button = st.form_submit_button("💾 Konfiguration speichern", type="primary")
        with col2:
            reset_button = st.form_submit_button("🔄 Auf Standard zurücksetzen")
        
        if save_button:
            # Validierung vor dem Speichern
            errors = []
            
            # URL-Validierung
            if config["N8N_WEBHOOK_URL"]:
                url_valid, url_error = validate_url(config["N8N_WEBHOOK_URL"], allow_empty=True)
                if not url_valid:
                    errors.append(f"n8n Webhook URL: {url_error}")
            
            ws_valid, ws_error = validate_url(config["WS_URI"], allow_empty=False)
            if not ws_valid:
                errors.append(f"WebSocket URI: {ws_error}")
            
            # Port-Validierung
            port_valid, port_error = validate_port(config["HEALTH_PORT"])
            if not port_valid:
                errors.append(f"Health Port: {port_error}")
            
            # Regex-Validierung
            if config["BAD_NAMES_PATTERN"]:
                regex_valid, regex_error = validate_regex(config["BAD_NAMES_PATTERN"], allow_empty=True)
                if not regex_valid:
                    errors.append(f"Bad Names Pattern: {regex_error}")
            
            if errors:
                st.error("❌ **Validierungsfehler:**")
                for error in errors:
                    st.error(f"  - {error}")
            else:
                result = save_config(config)
                if result:
                    st.session_state.config_saved = True
                    st.success("✅ Konfiguration gespeichert!")
                    st.warning("⚠️ **WICHTIG:** Die `.env` Datei wurde aktualisiert. Bitte Relay-Service neu starten, damit die Änderungen wirksam werden!")
        
        if reset_button:
            default_config = get_default_config()
            if save_config(default_config):
                st.session_state.config_saved = True
                st.success("✅ Konfiguration auf Standard zurückgesetzt!")
                st.warning("⚠️ Bitte Service neu starten, damit die Änderungen wirksam werden.")
                st.rerun()
    
    # DB-Verbindungstest (außerhalb des Forms)
    st.divider()
    st.subheader("🔍 Datenbank-Verbindung testen")
    if st.button("🔍 DB-Verbindung testen", type="secondary", key="db_test_button"):
        with st.spinner("Teste Datenbank-Verbindung..."):
            db_status = check_database_connection()
            if db_status['connected']:
                st.success("✅ Datenbank-Verbindung erfolgreich!")
                if db_status['tables']['discovered_coins']:
                    st.success("✅ Tabelle 'discovered_coins' vorhanden")
                else:
                    st.warning("⚠️ Tabelle 'discovered_coins' fehlt")
                if db_status['tables']['coin_streams']:
                    st.success("✅ Tabelle 'coin_streams' vorhanden")
                else:
                    st.info("ℹ️ Tabelle 'coin_streams' fehlt (optional)")
                if db_status['tables']['ref_coin_phases']:
                    st.success("✅ Tabelle 'ref_coin_phases' vorhanden")
                else:
                    st.info("ℹ️ Tabelle 'ref_coin_phases' fehlt (optional)")
            else:
                st.error(f"❌ Datenbank-Verbindung fehlgeschlagen: {db_status.get('error', 'Unbekannter Fehler')}")
    
    # Neustart-Button außerhalb des Forms (wenn Konfiguration gespeichert wurde)
    if st.session_state.get("config_saved", False):
        st.divider()
        st.subheader("🔄 Service-Neustart")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info("💡 Die Konfiguration wurde gespeichert. Starte den Relay-Service neu, damit die neuen Werte geladen werden.")
        with col2:
            if st.button("🔄 Konfiguration neu laden", type="primary", use_container_width=True, key="reload_config_button"):
                with st.spinner("Konfiguration wird neu geladen..."):
                    success, message = reload_config()
                    if success:
                        st.success(message)
                        st.info("💡 Die neue Konfiguration ist jetzt aktiv! Kein Neustart nötig.")
                        st.session_state.config_saved = False  # Reset Flag
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
                        if COOLIFY_MODE:
                            st.info("💡 **Coolify:** Falls das nicht funktioniert, starte den 'api' Service im Coolify-Dashboard neu.")
                        else:
                            st.info("💡 Du kannst den Service auch manuell neu starten: `docker compose restart relay`")
    
    # Aktuelle Konfiguration anzeigen
    st.subheader("📄 Aktuelle Konfiguration")
    st.json(config)

# Logs Tab
with tab3:
    st.subheader("📋 Service Logs")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        lines = st.number_input("Anzahl Zeilen", min_value=10, max_value=1000, value=100, step=10, key="logs_lines_input")
    
    with col2:
        refresh_logs = st.button("🔄 Logs aktualisieren", key="refresh_logs_button")
        if refresh_logs:
            st.rerun()
    
    # Logs abrufen
    logs = get_service_logs(lines=lines)
    
    # Stelle sicher, dass Logs als String vorliegen
    if isinstance(logs, list):
        logs = '\n'.join(logs)
    
    # Zeige Logs an (neueste oben)
    st.text_area(
        "Service Logs (neueste oben)",
        logs,
        height=600,
        key="logs_display",
        help="Die neuesten Logs stehen oben, die ältesten unten."
    )
    
    # Auto-Refresh
    auto_refresh = st.checkbox("🔄 Auto-Refresh Logs (10s)", key="auto_refresh_logs")
    if auto_refresh:
        time.sleep(10)
        st.rerun()

# Metriken Tab (wird jetzt im Dashboard angezeigt)
with tab4:
    st.info("💡 Die Metriken werden jetzt direkt im Dashboard angezeigt. Dieser Tab zeigt die vollständigen Raw-Metriken.")
    
    if st.button("🔄 Metriken aktualisieren"):
        st.rerun()
    
    metrics = get_relay_metrics()
    
    if metrics:
        # Vollständige Metriken
        st.subheader("📄 Vollständige Prometheus Metriken (Raw)")
        st.code(metrics, language="text")
        
        # Metriken als JSON parsen (für erweiterte Ansicht)
        st.subheader("📊 Metriken als strukturierte Daten")
        metrics_dict = {}
        for line in metrics.split('\n'):
            if line and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 2:
                    metric_name = parts[0]
                    try:
                        metric_value = float(parts[1]) if '.' in parts[1] else int(parts[1])
                        metrics_dict[metric_name] = metric_value
                    except:
                        metrics_dict[metric_name] = parts[1]
        
        st.json(metrics_dict)
    else:
        st.error("❌ Metriken konnten nicht abgerufen werden. Bitte prüfe, ob der Relay-Service läuft.")
    
    if st.checkbox("🔄 Auto-Refresh Metriken (5s)"):
        time.sleep(5)
        st.rerun()

# Info Tab
with tab5:
    st.title("ℹ️ Projekt-Informationen")
    
    # Projekt-Übersicht
    st.header("📋 Was macht dieses Projekt?")
    st.markdown("""
    **Pump Discover** ist ein Echtzeit-Monitoring-System für neu erstellte Tokens auf Pump.fun.
    
    Das System:
    - ✅ Empfängt neue Token-Erstellungen über WebSocket in Echtzeit
    - ✅ Führt erste Filterung durch (Spam, Bad Names, etc.)
    - ✅ Sendet gefilterte Tokens an n8n für weitere Verarbeitung
    - ✅ Speichert Token-Daten in einer PostgreSQL-Datenbank
    - ✅ Bietet eine Web-UI für Monitoring und Konfiguration
    """)
    
    # Datenfluss
    st.header("🔄 Datenfluss")
    st.code("""
    Pump.fun WebSocket (wss://pumpportal.fun/api/data)
            ↓
    Python Relay Service (relay/main.py)
            ├─ Filterung: Bad Names, Spam-Burst
            ├─ Batching: Sammelt Coins in Batches
            └─ Weiterleitung an n8n
            ↓
    n8n Workflow
            ├─ Empfängt Batches vom Relay
            ├─ Ruft API-Daten ab (RugCheck, etc.)
            ├─ Parst Metadata (IPFS/RapidLaunch)
            ├─ Führt weitere Filterung durch
            └─ Speichert in Datenbank
            ↓
    PostgreSQL Datenbank
            └─ discovered_coins Tabelle
    """, language="text")
    
    # Weitergegebene Informationen
    st.header("📤 Welche Informationen werden weitergegeben?")
    
    st.subheader("1️⃣ WebSocket-Daten (vom Relay an n8n)")
    st.markdown("""
    Der Relay-Service sendet folgende Daten für jeden Token:
    
    | Feld | Beschreibung | Beispiel |
    |------|--------------|----------|
    | `mint` | Token-Adresse (Mint) | `7GggZA5GEHqTyiuFBTsWiU5uz7HDvSBMH11UB8GDpump` |
    | `name` | Token-Name | `wifmas` |
    | `symbol` | Token-Symbol | `wifmas` |
    | `signature` | Transaktions-Signatur | `UEFn9JFNHYaUVDvmq66EBPFVKENsP4bS1Q75hXkvzQgWbKnKWdymxnRE3RZeG23Fm1AXwL1FByK59mdRioC4o7H` |
    | `traderPublicKey` | Creator Public Key | `DxGLoNf279eyYqTRTYqPZTtiB5BbF4fqRtfjfrvQyiwt` |
    | `bondingCurveKey` | Bonding Curve Adresse | `BMyRVLmarQUvTJ7YwkH3cQsg1VgSX3fV6AKgSYNb1joR` |
    | `pool_address` | Pool-Adresse | `BMyRVLmarQUvTJ7YwkH3cQsg1VgSX3fV6AKgSYNb1joR` |
    | `vTokensInBondingCurve` | Virtuelle Tokens | `1006714285.776477` |
    | `vSolInBondingCurve` | Virtuelles SOL | `31.975308639999987` |
    | `initialBuy` | Initiale Token-Anzahl | `66285714.223523` |
    | `solAmount` | Initialer SOL-Betrag | `1.97530864` |
    | `marketCapSol` | Market Cap in SOL | `31.762049165059267` |
    | `price_sol` | Preis in SOL (berechnet) | `3.155021202521354e-8` |
    | `uri` | Metadata URI | `https://ipfs.io/ipfs/...` |
    | `is_mayhem_mode` | Mayhem Mode Flag | `false` |
    | `pool` | Pool-Typ | `pump` |
    | `phaseId` | Phase ID | `1` |
    """)
    
    st.subheader("2️⃣ API-Daten (in n8n abgerufen)")
    st.markdown("""
    Zusätzlich werden in n8n folgende Daten von externen APIs abgerufen:
    
    | Feld | Quelle | Beschreibung |
    |------|--------|--------------|
    | `token.decimals` | RugCheck API | Token Decimals (z.B. `6`) |
    | `token.supply` | RugCheck API | Token Supply (raw, mit decimals) |
    | `deployPlatform` | RugCheck API | Deployment Platform (z.B. `"rapidlaunch"`) |
    | `score` / `score_normalised` | RugCheck API | Risiko-Score (0-100) |
    | `topHolders` | RugCheck API | Top Holders Array (für Berechnung) |
    | `metadata.isMutable` | RugCheck API | **NEU:** Kann Dev Metadata nachträglich ändern? → `metadata_is_mutable` |
    | `mintAuthority.enabled` | RugCheck API | **NEU:** Kann Dev neue Tokens drucken? → `mint_authority_enabled` |
    """)
    
    st.subheader("3️⃣ Berechnete Felder (im Relay)")
    st.markdown("""
    Der Relay-Service berechnet folgende Felder automatisch:
    
    | Feld | Berechnung | Beschreibung |
    |------|------------|--------------|
    | `price_sol` | `marketCapSol / vTokensInBondingCurve` | Preis in SOL |
    | `pool_address` | `bondingCurveKey` | Pool-Adresse |
    | `social_count` | **NEU:** Anzahl vorhandener Social-Links (0-4) | Twitter + Telegram + Website + Discord |
    """)
    
    st.subheader("4️⃣ Metadata-Daten (aus URI geparst)")
    st.markdown("""
    Die Metadata-URI wird in n8n geparst und liefert:
    
    - `description` - Token-Beschreibung
    - `image` - Bild-URL
    - `twitter` - Twitter/X URL
    - `telegram` - Telegram URL
    - `website` - Website URL
    - `discord` - Discord URL
    """)
    
    # Datenbankschema
    st.header("🗄️ Datenbankschema")
    
    st.subheader("Tabelle: `discovered_coins`")
    st.markdown("""
    Diese Tabelle speichert den **initialen Snapshot** jedes entdeckten Tokens.
    Metriken (die sich ändern) werden in einer separaten Tabelle gespeichert (alle 5 Sekunden).
    """)
    
    with st.expander("📋 Vollständiges Schema anzeigen"):
        st.markdown("""
        #### 1. Identifikation
        - `token_address` (PRIMARY KEY) - Mint-Adresse
        - `blockchain_id` - Blockchain ID (1 = Solana)
        - `symbol` - Token-Symbol
        - `name` - Token-Name
        - `token_decimals` - Token Decimals (vom API)
        - `token_supply` - Token Supply (vom API)
        - `deploy_platform` - Deployment Platform (vom API)
        
        #### 2. Transaktions-Informationen
        - `signature` - Transaktions-Signatur
        - `trader_public_key` - Creator Public Key
        
        #### 3. Bonding Curve & Pool
        - `bonding_curve_key` - Bonding Curve Adresse
        - `pool_address` - Pool-Adresse
        - `pool_type` - Pool-Typ (meist "pump")
        - `v_tokens_in_bonding_curve` - Virtuelle Tokens
        - `v_sol_in_bonding_curve` - Virtuelles SOL
        
        #### 4. Initial Buy
        - `initial_buy_sol` - SOL Betrag beim initialen Buy
        - `initial_buy_tokens` - Anzahl Tokens beim initialen Buy
        
        #### 5. Zeitstempel
        - `discovered_at` - Wann wurde der Coin entdeckt
        - `token_created_at` - Wann wurde der Token erstellt
        
        #### 6. Preis & Market Cap
        - `price_sol` - Preis in SOL
        - `market_cap_sol` - Market Cap in SOL
        - `liquidity_sol` - Liquidität in SOL
        
        #### 7. Graduation
        - `open_market_cap_sol` - Fester Wert für Graduierung (85,000 SOL)
        - `phase_id` - Phase ID
        
        #### 8. Status Flags
        - `is_mayhem_mode` - Mayhem Mode Flag
        - `is_graduated` - Ob bereits graduiert
        - `is_active` - Ob noch aktiv
        
        #### 9. Risiko & Analyse
        - `risk_score` - Risiko-Score (0-100)
        - `top_10_holders_pct` - Prozentualer Anteil der Top-10-Holder
        - `has_socials` - Ob Social Media vorhanden
        - `social_count` - **NEU:** Anzahl Social-Links (0-4): Twitter + Telegram + Website + Discord
        - `metadata_is_mutable` - **NEU:** Kann Dev Metadata nachträglich ändern? (aus RugCheck API)
        - `mint_authority_enabled` - **NEU:** Kann Dev neue Tokens drucken? (aus RugCheck API)
        - `image_hash` - **NEU:** pHash des Bildes (64 Zeichen) - für Lazy Scam Detection
        
        #### 10. Metadata & Social Media
        - `metadata_uri` - URI zur Metadata
        - `description` - Token-Beschreibung
        - `image_url` - Bild-URL
        - `twitter_url` - Twitter/X URL
        - `telegram_url` - Telegram URL
        - `website_url` - Website URL
        - `discord_url` - Discord URL
        
        #### 11. Management & Klassifizierung
        - `final_outcome` - Ergebnis (PENDING, GRADUATED, RUG, etc.)
        - `classification` - Klassifizierung
        - `status_note` - Notiz zum Status
        """)
    
    # Daten-Mapping
    st.header("🗺️ Daten-Mapping: Was wird wo gefüllt?")
    
    st.subheader("WebSocket → Datenbank")
    st.markdown("""
    | WebSocket Feld | SQL Feld | Gefüllt von |
    |----------------|----------|-------------|
    | `mint` | `token_address` | WebSocket |
    | `name` | `name` | WebSocket |
    | `symbol` | `symbol` | WebSocket |
    | `signature` | `signature` | WebSocket |
    | `traderPublicKey` | `trader_public_key` | WebSocket |
    | `bondingCurveKey` | `bonding_curve_key` | WebSocket |
    | `pool_address` | `pool_address` | WebSocket (berechnet) |
    | `vTokensInBondingCurve` | `v_tokens_in_bonding_curve` | WebSocket |
    | `vSolInBondingCurve` | `v_sol_in_bonding_curve` | WebSocket |
    | `solAmount` | `initial_buy_sol` | WebSocket |
    | `initialBuy` | `initial_buy_tokens` | WebSocket |
    | `marketCapSol` | `market_cap_sol` | WebSocket |
    | `price_sol` | `price_sol` | WebSocket (berechnet) |
    | `social_count` | `social_count` | **NEU:** Relay (berechnet: 0-4) |
    | `uri` | `metadata_uri` | WebSocket |
    | `is_mayhem_mode` | `is_mayhem_mode` | WebSocket |
    | `pool` | `pool_type` | WebSocket |
    | `phaseId` | `phase_id` | WebSocket |
    | `vSolInBondingCurve` | `liquidity_sol` | WebSocket (gleicher Wert) |
    """)
    
    st.subheader("API → Datenbank")
    st.markdown("""
    | API Feld | SQL Feld | Gefüllt von |
    |----------|----------|-------------|
    | `token.decimals` | `token_decimals` | RugCheck API (in n8n) |
    | `token.supply` | `token_supply` | RugCheck API (in n8n) |
    | `deployPlatform` | `deploy_platform` | RugCheck API (in n8n) |
    | `score` / `score_normalised` | `risk_score` | RugCheck API (in n8n) |
    | `topHolders[]` | `top_10_holders_pct` | RugCheck API (in n8n, berechnet) |
    | `metadata.isMutable` | `metadata_is_mutable` | **NEU:** RugCheck API (in n8n) |
    | `mintAuthority.enabled` | `mint_authority_enabled` | **NEU:** RugCheck API (in n8n) |
    """)
    
    st.subheader("Metadata → Datenbank")
    st.markdown("""
    | Metadata Feld | SQL Feld | Gefüllt von |
    |---------------|----------|-------------|
    | `description` | `description` | Metadata URI (in n8n geparst) |
    | `image` | `image_url` | Metadata URI (in n8n geparst) |
    | `twitter` | `twitter_url` | Metadata URI (in n8n geparst) |
    | `telegram` | `telegram_url` | Metadata URI (in n8n geparst) |
    | `website` | `website_url` | Metadata URI (in n8n geparst) |
    | `discord` | `discord_url` | Metadata URI (in n8n geparst) |
    | (berechnet) | `has_socials` | Metadata URI (in n8n, wenn URLs vorhanden) |
    | (berechnet) | `social_count` | **NEU:** Relay (Anzahl vorhandener Social-Links: 0-4) |
    | (berechnet) | `image_hash` | **NEU:** Optional in n8n (pHash des Bildes für Lazy Scam Detection) |
    """)
    
    st.subheader("Default-Werte")
    st.markdown("""
    | SQL Feld | Default-Wert | Setzt |
    |----------|--------------|-------|
    | `discovered_at` | `NOW()` | Datenbank |
    | `open_market_cap_sol` | `85000` | Datenbank |
    | `blockchain_id` | `1` | Datenbank |
    | `is_active` | `TRUE` | Datenbank |
    | `final_outcome` | `'PENDING'` | Datenbank |
    | `classification` | `'UNKNOWN'` | Datenbank |
    | `pool_type` | `'pump'` | Datenbank |
    """)
    
    # Zusammenfassung
    st.header("📊 Zusammenfassung")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("WebSocket Felder", "17", "Direkt vom Relay (+ social_count)")
    
    with col2:
        st.metric("API Felder", "6-8", "In n8n abgerufen (+ 2 neue Flags)")
    
    with col3:
        st.metric("Metadata Felder", "7-9", "In n8n geparst (+ image_hash optional)")
    
    st.info("""
    **Wichtig:** 
    - Die `discovered_coins` Tabelle speichert nur den **initialen Snapshot**
    - **NEU:** `social_count` wird im Relay berechnet und direkt an n8n gesendet
    - **NEU:** `metadata_is_mutable` und `mint_authority_enabled` werden in n8n aus der RugCheck API geholt
    - **NEU:** `image_hash` kann optional in n8n berechnet werden (pHash für Lazy Scam Detection)
    - Metriken (die sich ändern) werden in einer separaten Tabelle gespeichert
    - Alle Felder werden in n8n zusammengeführt und in die Datenbank geschrieben
    """)
    
    # Technische Details
    st.header("🔧 Technische Details")
    
    st.subheader("Services")
    st.markdown("""
    - **Relay Service** (`relay/main.py`): Empfängt WebSocket-Daten, filtert, sendet an n8n
    - **UI Service** (`ui/app.py`): Streamlit Web-Interface für Monitoring und Konfiguration
    - **n8n Workflow**: Empfängt Batches, ruft APIs ab, parst Metadata, speichert in DB
    """)
    
    st.subheader("Ports")
    st.markdown("""
    - **Web UI**: Port `8500` (extern) → `8501` (intern)
    - **API/Relay**: Port `8010` (extern) → `8000` (intern)
    """)
    
    st.subheader("Endpoints")
    st.markdown("""
    - `GET /health` - Health Check (Status, Uptime, etc.)
    - `GET /metrics` - Prometheus Metrics
    """)

