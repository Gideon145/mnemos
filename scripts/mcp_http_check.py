"""Protocol check: POST tools/list to the HTTP MCP endpoint."""
import http.client
import json
import os
import subprocess
import sys
import time

PORT = "8765"
env = dict(os.environ)
env["PORT"] = PORT
proc = subprocess.Popen(
    [
        r"C:\Users\vergio\Dev\mnemos\.venv\Scripts\mnemos.exe",
        "mcp",
        "--http",
    ],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
time.sleep(4)
if proc.poll() is not None:
    out = proc.stdout.read().decode() + proc.stderr.read().decode()
    print("server exited early:", out[:500])
    sys.exit(1)


def post(payload: dict, session: str | None = None) -> tuple[int, dict, dict]:
    conn = http.client.HTTPConnection("127.0.0.1", int(PORT), timeout=15)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session:
        headers["Mcp-Session-Id"] = session
    body = json.dumps(payload).encode()
    conn.request("POST", "/mcp", body=body, headers=headers)
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8")
    data = {}
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if line.startswith("{"):
            data = json.loads(line)
            break
    if not data:
        data = json.loads(raw)
    out_headers = {k: v for k, v in resp.getheaders()}
    conn.close()
    return resp.status, data, out_headers


try:
    status, init_data, init_headers = post(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "protocol-check", "version": "1.0"},
            },
        }
    )
    if status != 200:
        print("initialize HTTP", status, init_data)
        sys.exit(1)
    session = next(
        (v for k, v in init_headers.items() if k.lower() == "mcp-session-id"),
        None,
    )
    print("initialize OK, session:", session)
    if not session:
        print("no session header returned")
        sys.exit(1)

    status, tools_data, _ = post(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        session=session,
    )
    tools = [t["name"] for t in tools_data.get("result", {}).get("tools", [])]
    print("TOOLS:", ", ".join(tools))
    print("HTTP MCP OK" if len(tools) >= 11 else "MISSING TOOLS")
    sys.exit(0 if len(tools) >= 11 else 1)
finally:
    proc.kill()
