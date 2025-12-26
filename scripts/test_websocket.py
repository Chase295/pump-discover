#!/usr/bin/env python3
"""
Test-Script um alle Daten vom Pump.fun WebSocket zu analysieren
"""
import asyncio
import websockets
import json
import sys
from datetime import datetime

async def test_websocket():
    """Verbinde zum WebSocket und logge alle empfangenen Daten"""
    uri = "wss://pumpportal.fun/api/data"
    
    print("🔌 Verbinde zu Pump.fun WebSocket...")
    print("=" * 80)
    
    try:
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        async with websockets.connect(
            uri,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10,
            max_size=2**23,
            ssl=ssl_context
        ) as ws:
            print("✅ Verbunden!")
            print("📡 Warte auf Daten... (Drücke Ctrl+C zum Beenden)")
            print("=" * 80)
            
            # Subscribe
            await ws.send(json.dumps({"method": "subscribeNewToken"}))
            print("📝 Subscribe-Nachricht gesendet\n")
            
            coin_count = 0
            max_coins = 5  # Nur 5 Coins analysieren für Übersicht
            
            while coin_count < max_coins:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30.0)
                    data = json.loads(msg)
                    
                    coin_count += 1
                    print(f"\n{'='*80}")
                    print(f"COIN #{coin_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"{'='*80}")
                    
                    # Vollständige Datenstruktur ausgeben
                    print("\n📦 VOLLSTÄNDIGE DATENSTRUKTUR:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                    # Alle Keys auflisten
                    print(f"\n🔑 ALLE VERFÜGBAREN FELDER ({len(data)} Felder):")
                    for key, value in sorted(data.items()):
                        value_type = type(value).__name__
                        value_preview = str(value)[:100] if value is not None else "None"
                        if len(str(value)) > 100:
                            value_preview += "..."
                        print(f"  • {key:30s} ({value_type:15s}): {value_preview}")
                    
                    # Nested Objects analysieren
                    print(f"\n🔍 VERSCHACHTELTE OBJEKTE:")
                    for key, value in data.items():
                        if isinstance(value, dict):
                            print(f"  📁 {key}:")
                            for sub_key, sub_value in value.items():
                                sub_type = type(sub_value).__name__
                                sub_preview = str(sub_value)[:80] if sub_value is not None else "None"
                                if len(str(sub_value)) > 80:
                                    sub_preview += "..."
                                print(f"      • {sub_key:25s} ({sub_type:12s}): {sub_preview}")
                        elif isinstance(value, list) and len(value) > 0:
                            print(f"  📋 {key} (Liste mit {len(value)} Einträgen):")
                            if len(value) > 0:
                                first_item = value[0]
                                if isinstance(first_item, dict):
                                    print(f"      Erster Eintrag hat {len(first_item)} Felder:")
                                    for sub_key in list(first_item.keys())[:5]:
                                        print(f"        • {sub_key}")
                                    if len(first_item) > 5:
                                        print(f"        ... und {len(first_item) - 5} weitere")
                                else:
                                    print(f"      Typ: {type(first_item).__name__}")
                    
                    print(f"\n⏳ Warte auf nächsten Coin...\n")
                    
                except asyncio.TimeoutError:
                    print("⏱️  Timeout - keine Daten erhalten")
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Fehler: {e}")
                    print(f"   Raw Message: {msg[:200]}")
                    continue
                except KeyboardInterrupt:
                    print("\n\n👋 Beendet durch Benutzer")
                    break
            
            print(f"\n{'='*80}")
            print(f"✅ Analyse abgeschlossen - {coin_count} Coins analysiert")
            print(f"{'='*80}\n")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket Fehler: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n👋 Beendet")

