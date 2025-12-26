#!/usr/bin/env python3
"""
Prüft ob openMarketCap in den WebSocket-Daten vorhanden ist
"""
import asyncio
import websockets
import json
import ssl

async def check_all_fields():
    uri = 'wss://pumpportal.fun/api/data'
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    print("🔍 Suche nach 'openMarketCap' oder ähnlichen Feldern...\n")
    
    async with websockets.connect(uri, ping_interval=20, ping_timeout=10, ssl=ssl_context) as ws:
        await ws.send(json.dumps({'method': 'subscribeNewToken'}))
        
        coin_count = 0
        while coin_count < 5:
            msg = await asyncio.wait_for(ws.recv(), timeout=30.0)
            data = json.loads(msg)
            
            if 'message' in data:
                continue
            
            coin_count += 1
            print(f"=== COIN #{coin_count}: {data.get('name', 'N/A')} ({data.get('symbol', 'N/A')}) ===")
            
            # Suche nach allen Feldern die "open", "cap", "graduat", "target" enthalten
            relevant_fields = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(term in key_lower for term in ['open', 'cap', 'graduat', 'target', 'threshold', 'goal']):
                    relevant_fields[key] = value
            
            if relevant_fields:
                print("✅ Gefundene relevante Felder:")
                for key, value in relevant_fields.items():
                    print(f"  • {key}: {value}")
            else:
                print("❌ Keine 'openMarketCap' oder ähnliche Felder gefunden")
            
            print(f"\n📊 Aktuelle marketCapSol: {data.get('marketCapSol', 'N/A')}")
            print(f"🎯 Open Market Cap (fest): ~85,000 SOL (~$1.8M USD)")
            print(f"📈 Noch bis Graduierung: ~{85000 - data.get('marketCapSol', 0):,.0f} SOL\n")
            
            if coin_count >= 3:
                break

asyncio.run(check_all_fields())

