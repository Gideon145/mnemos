"""Poll the Railway MCP endpoint until it serves the initialize handshake."""
import http.client
import json
import sys
import time

HOST = "mnemos-production-2572.up.railway.app"


def post(payload, session=None):
    conn = http.client.HTTPSConnection(HOST, timeout=20)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session:
        headers["Mcp-Session-Id"] = session
    conn.request("POST", "/mcp", body=json.dumps(payload).encode(), headers=headers)
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8")
    out_headers = {k.lower(): v for k, v in resp.getheaders()}
    conn.close()
    return resp.status, raw, out_headers


for attempt in range(30):
    try:
        status, raw, headers = post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "railway-check", "version": "1.0"},
                },
            }
        )
    except Exception as e:
        print(f"attempt {attempt + 1}: not up yet ({type(e).__name__})")
        time.sleep(10)
        continue
    if status != 200:
        print(f"attempt {attempt + 1}: HTTP {status} {raw[:120]}")
        time.sleep(10)
        continue
    session = headers.get("mcp-session-id")
    print("initialize OK, session:", session)
    status2, raw2, _ = post(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        session=session,
    )
    data = None
    for line in raw2.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if line.startswith("{"):
            data = json.loads(line)
            break
    if data is None:
        data = json.loads(raw2)
    tools = [t["name"] for t in data["result"]["tools"]]
    print("TOOLS:", ", ".join(tools))
    print("RAILWAY MCP LIVE:", f"https://{HOST}/mcp")
    sys.exit(0)
print("never came up")
sys.exit(1)
