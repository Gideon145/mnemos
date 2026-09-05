"""Probe the hosted /chat endpoint like a first user."""
import http.client
import json
import sys
import time

HOST = "mnemos-production-2572.up.railway.app"

for attempt in range(30):
    try:
        conn = http.client.HTTPSConnection(HOST, timeout=40)
        conn.request(
            "POST",
            "/chat",
            body=json.dumps({"message": "how are you?"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        conn.close()
        if resp.status == 200:
            data = json.loads(raw)
            print("RAW:", raw[:400])
            print("CHAT OK:", data.get("answer", "")[:300])
            sys.exit(0)
        print(f"attempt {attempt + 1}: HTTP {resp.status} {raw[:140]}")
    except Exception as exc:
        print(f"attempt {attempt + 1}: not up yet ({type(exc).__name__})")
    time.sleep(10)
print("chat never came up")
sys.exit(1)
