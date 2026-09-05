"""One-off: verify CORS headers on the HTTP MCP endpoint."""
import http.client
import json
import os
import subprocess
import sys
import time

PORT = "8766"
env = dict(os.environ)
env["PORT"] = PORT
proc = subprocess.Popen(
    [r"C:\Users\vergio\Dev\mnemos\.venv\Scripts\mnemos.exe", "mcp", "--http"],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
time.sleep(4)
try:
    conn = http.client.HTTPConnection("127.0.0.1", int(PORT), timeout=15)
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "cors-check", "version": "1.0"},
            },
        }
    ).encode()
    conn.request(
        "POST",
        "/mcp",
        body=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Origin": "http://localhost:3000",
        },
    )
    resp = conn.getresponse()
    resp.read()
    headers = {k.lower(): v for k, v in resp.getheaders()}
    print("status:", resp.status)
    print("allow-origin:", headers.get("access-control-allow-origin"))
    print("expose:", headers.get("access-control-expose-headers"))
    print("session:", headers.get("mcp-session-id"))
    ok = (
        headers.get("access-control-allow-origin") == "*"
        and "Mcp-Session-Id" in headers.get("access-control-expose-headers", "")
        and headers.get("mcp-session-id")
    )
    print("CORS OK" if ok else "CORS MISSING")
    sys.exit(0 if ok else 1)
finally:
    proc.kill()
