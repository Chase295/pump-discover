#!/usr/bin/env python3
"""
Test-Script um Metadata von den URIs zu analysieren
"""
import asyncio
import websockets
import json
import ssl
import requests

def fetch_metadata(uri):
    """Holt Metadata von einer URI"""
    try:
        resp = requests.get(uri, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            return None
    except Exception as e:
        return {"error": str(e)}

async def test_metadata():
    """Testet Metadata von mehreren Coins"""
    uri = "wss://pumpportal.fun/api/data"
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    print("🔌 Verbinde zu Pump.fun WebSocket...")
    print("=" * 80)
    
    try:
        async with websockets.connect(
            uri,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10,
            max_size=2**23,
            ssl=ssl_context
        ) as ws:
            print("✅ Verbunden!")
            await ws.send(json.dumps({"method": "subscribeNewToken"}))
            
            coin_count = 0
            max_coins = 3
            
            while coin_count < max_coins:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30.0)
                    data = json.loads(msg)
                    
                    # Skip subscription confirmation
                    if "message" in data:
                        continue
                    
                    if not data.get("uri"):
                        continue
                    
                    coin_count += 1
                    metadata_uri = data.get("uri")
                    
                    print(f"\n{'='*80}")
                    print(f"COIN #{coin_count} - {data.get('name', 'Unknown')} ({data.get('symbol', '???')})")
                    print(f"{'='*80}")
                    print(f"📎 Metadata URI: {metadata_uri}")
                    
                    # Fetch metadata
                    print(f"⏳ Lade Metadata...")
                    metadata = fetch_metadata(metadata_uri)
                    
                    if metadata and "error" not in metadata:
                        print(f"\n📦 METADATA INHALT:")
                        print(json.dumps(metadata, indent=2, ensure_ascii=False))
                        
                        print(f"\n🔑 METADATA FELDER ({len(metadata)} Felder):")
                        for key, value in sorted(metadata.items()):
                            value_type = type(value).__name__
                            if isinstance(value, str):
                                value_preview = value[:80] + "..." if len(value) > 80 else value
                            elif isinstance(value, (dict, list)):
                                value_preview = f"[{type(value).__name__} mit {len(value)} Einträgen]"
                            else:
                                value_preview = str(value)[:80]
                            print(f"  • {key:25s} ({value_type:12s}): {value_preview}")
                    else:
                        print(f"❌ Konnte Metadata nicht laden: {metadata}")
                    
                except asyncio.TimeoutError:
                    print("⏱️  Timeout")
                    break
                except json.JSONDecodeError:
                    continue
                except KeyboardInterrupt:
                    break
            
            print(f"\n{'='*80}")
            print(f"✅ Analyse abgeschlossen")
            print(f"{'='*80}\n")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test_metadata())
    except KeyboardInterrupt:
        print("\n👋 Beendet")
