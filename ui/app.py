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

# Docker Compose Ports
RELAY_PORT=8000
UI_PORT=8501
"""
    
    # Speichere .env Datei
    # Die .env Datei sollte als Volume gemountet sein: ./.env:/app/.env:rw
    env_paths = [
        "/app/.env",  # Gemountete .env Datei
        "/app/../.env",  # Projekt-Root (wenn gemountet)
        "/app/config/.env",  # Fallback
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
        "HEALTH_PORT": 8000
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

def restart_service():
    """Startet Relay-Service neu (über Docker API, damit .env neu geladen wird)"""
    # Coolify-Modus: Kein Docker Socket verfügbar
    if COOLIFY_MODE:
        return False, "⚠️ Coolify-Modus: Service-Neustart muss über das Coolify-Dashboard erfolgen. Gehe zu deinem Coolify-Dashboard und starte den 'api' Service neu."
    
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

def get_service_logs(lines=100):
    """Holt Logs vom Relay-Service"""
    # Coolify-Modus: Kein Docker Socket verfügbar
    if COOLIFY_MODE:
        return f"""⚠️ Coolify-Modus: Logs können nicht direkt abgerufen werden.

📋 **Logs anzeigen:**
1. Gehe zu deinem Coolify-Dashboard
2. Wähle den 'api' Service
3. Klicke auf "Logs" um die Logs anzuzeigen

💡 **Alternative:** Du kannst die Logs auch über die Coolify-API abrufen.
"""
    
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
            return logs
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
                return result.stdout
            else:
                return f"Fehler beim Abrufen der Logs: {result.stderr}"
        except Exception as e:
            return f"Fehler beim Abrufen der Logs: {str(e)}"
    except Exception as e:
        return f"Fehler beim Abrufen der Logs: {str(e)}"

# Header
st.title("🚀 Pump Discover - Control Panel")

# Tabs Navigation
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "⚙️ Konfiguration", "📋 Logs", "📈 Metriken"])

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
        st.info("🌐 **Coolify-Modus aktiv:** Service-Neustart muss über das Coolify-Dashboard erfolgen.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Service neu starten", type="primary", disabled=COOLIFY_MODE):
            with st.spinner("Service wird neu gestartet..."):
                success, message = restart_service()
                if success:
                    st.success(message)
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(message)
                    if COOLIFY_MODE:
                        st.info("💡 **Hinweis:** In Coolify musst du den Service über das Dashboard neu starten.")
    
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
    
    # Neustart-Button außerhalb des Forms (wenn Konfiguration gespeichert wurde)
    if st.session_state.get("config_saved", False):
        st.divider()
        st.subheader("🔄 Service-Neustart")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info("💡 Die Konfiguration wurde gespeichert. Starte den Relay-Service neu, damit die neuen Werte geladen werden.")
        with col2:
            if st.button("🔄 Relay-Service neu starten", type="primary", use_container_width=True, disabled=COOLIFY_MODE):
                with st.spinner("Relay-Service wird neu gestartet..."):
                    success, message = restart_service()
                    if success:
                        st.success(message)
                        st.info("⏳ Bitte warte 5-10 Sekunden, bis der Service vollständig neu gestartet ist.")
                        st.session_state.config_saved = False  # Reset Flag
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.error(message)
                        if COOLIFY_MODE:
                            st.info("💡 **Coolify:** Gehe zu deinem Coolify-Dashboard und starte den 'api' Service neu, damit die neuen Environment Variables geladen werden.")
                        else:
                            st.info("💡 Du kannst den Service auch manuell neu starten: `docker compose restart relay`")
    
    # Aktuelle Konfiguration anzeigen
    st.subheader("📄 Aktuelle Konfiguration")
    st.json(config)

# Logs Tab
with tab3:
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        lines = st.number_input("Anzahl Zeilen", min_value=10, max_value=1000, value=100, step=10)
    
    with col2:
        if st.button("🔄 Logs aktualisieren"):
            st.rerun()
    
    logs = get_service_logs(lines=lines)
    st.text_area("Service Logs", logs, height=600, key="logs_display")
    
    if st.checkbox("🔄 Auto-Refresh Logs (10s)"):
        time.sleep(10)
        st.rerun()

# Metriken Tab
with tab4:
    
    if st.button("🔄 Metriken aktualisieren"):
        st.rerun()
    
    metrics = get_relay_metrics()
    
    if metrics:
        # Parse und zeige wichtige Metriken
        st.subheader("📈 Wichtige Metriken")
        
        metrics_dict = {}
        for line in metrics.split('\n'):
            if line and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 2:
                    metric_name = parts[0]
                    metric_value = parts[1]
                    metrics_dict[metric_name] = metric_value
        
        # Wichtige Metriken anzeigen
        important_metrics = [
            'pumpfun_coins_received_total',
            'pumpfun_coins_sent_total',
            'pumpfun_coins_filtered_total',
            'pumpfun_batches_sent_total',
            'pumpfun_ws_reconnects_total',
            'pumpfun_ws_connected',
            'pumpfun_n8n_available',
            'pumpfun_buffer_size',
            'pumpfun_uptime_seconds'
        ]
        
        cols = st.columns(3)
        col_idx = 0
        for metric in important_metrics:
            if metric in metrics_dict:
                with cols[col_idx % 3]:
                    st.metric(metric.replace('pumpfun_', '').replace('_', ' ').title(), metrics_dict[metric])
                col_idx += 1
        
        # Vollständige Metriken
        st.subheader("📄 Vollständige Metriken (Raw)")
        st.code(metrics, language="text")
    else:
        st.error("❌ Metriken konnten nicht abgerufen werden. Bitte prüfe, ob der Relay-Service läuft.")
    
    if st.checkbox("🔄 Auto-Refresh Metriken (5s)"):
        time.sleep(5)
        st.rerun()

