"""List hosted tools and optionally call reset."""
import http.client
import json
import sys

HOST = "mnemos-production-2572.up.railway.app"


def post(payload, session=None):
    conn = http.client.HTTPSConnection(HOST, timeout=30)
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
    data = None
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if line.startswith("{"):
            data = json.loads(line)
            break
    return resp.status, data, out_headers


status, init, headers = post(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "probe", "version": "1"},
        },
    }
)
session = headers.get("mcp-session-id")
print("init:", status, "session:", session)
status2, tools, _ = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, session)
names = [t["name"] for t in (tools or {}).get("result", {}).get("tools", [])]
print("tools:", names)
if "reset" in names and len(sys.argv) > 1 and sys.argv[1] == "reset":
    status3, out, _ = post(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "reset", "arguments": {}},
        },
        session,
    )
    print("reset:", status3, json.dumps(out)[:200])
