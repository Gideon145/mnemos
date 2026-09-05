// Live playground: talks to the hosted Mnemos MCP endpoint over
// streamable HTTP. Minimal MCP client, no dependencies.

const MCP_URL = "https://mnemos-production-2572.up.railway.app/mcp";

const chat = document.getElementById("pg-chat");
const form = document.getElementById("pg-form");
const input = document.getElementById("pg-text");
const status = document.getElementById("pg-status");

let sessionId = null;
let nextId = 1;

function setStatus(online) {
  status.classList.toggle("online", online);
  status.lastChild.textContent = online ? " live" : " offline";
}

async function postMCP(payload, session) {
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json, text/event-stream",
  };
  if (session) headers["Mcp-Session-Id"] = session;
  const res = await fetch(MCP_URL, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  const raw = await res.text();
  if (res.headers.get("Mcp-Session-Id")) {
    sessionId = res.headers.get("Mcp-Session-Id");
  }
  // Responses may be SSE framed or plain JSON.
  for (const line of raw.split("\n")) {
    let candidate = line.trim();
    if (candidate.startsWith("data:")) candidate = candidate.slice(5).trim();
    if (candidate.startsWith("{")) return JSON.parse(candidate);
  }
  return JSON.parse(raw);
}

async function connect() {
  const result = await postMCP({
    jsonrpc: "2.0",
    id: nextId++,
    method: "initialize",
    params: {
      protocolVersion: "2025-06-18",
      capabilities: {},
      clientInfo: { name: "mnemos-playground", version: "1.0" },
    },
  });
  if (!sessionId) throw new Error("no session returned");
  return result;
}

async function callTool(name, args) {
  const payload = await postMCP(
    { jsonrpc: "2.0", id: nextId++, method: "tools/call", params: { name, arguments: args } },
    sessionId
  );
  if (payload.error) throw new Error(payload.error.message || "tool error");
  const content = payload.result && payload.result.content;
  const structured = payload.result && payload.result.structuredContent;
  if (structured && Object.keys(structured).length) return structured;
  if (Array.isArray(content) && content.length) {
    const text = content.map((c) => c.text || "").join("\n");
    return { text };
  }
  return { text: "(empty result)" };
}

function addMsg(role, text, meta) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + role;
  const name = document.createElement("div");
  name.className = "msg-name";
  name.textContent = role === "user" ? "YOU" : "MNEMOS";
  const body = document.createElement("div");
  body.className = "msg-body";
  body.textContent = text;
  wrap.appendChild(name);
  wrap.appendChild(body);
  if (meta) {
    const m = document.createElement("div");
    m.className = "msg-meta";
    m.textContent = meta;
    wrap.appendChild(m);
  }
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
}

function renderStructured(data) {
  const lines = [];
  for (const [key, value] of Object.entries(data)) {
    const v = Array.isArray(value)
      ? value.length
        ? value.join(", ")
        : "(none)"
      : typeof value === "object" && value !== null
        ? JSON.stringify(value)
        : String(value);
    lines.push(key + ": " + v);
  }
  return lines.join("\n");
}

async function runAction(action) {
  const chips = document.querySelectorAll(".chip");
  chips.forEach((c) => (c.disabled = true));
  try {
    if (!sessionId) {
      await connect();
      setStatus(true);
    }
    if (action === "teach") {
      addMsg("user", "Teach me two facts.");
      await callTool("remember", { text: "I like short direct answers", category: "preference" });
      await callTool("remember", { text: "my contractor rate is 40 per hour", category: "preference" });
      addMsg("bot", "Stored both facts.\n\npreference: I like short direct answers\npreference: my contractor rate is 40 per hour", "remember x2");
    } else if (action === "ask") {
      addMsg("user", "What do you know about me?");
      const out = await callTool("ask", { question: "what do you know about me?" });
      addMsg("bot", out.answer || out.text || "(empty)", "ask · found: " + (out.found !== undefined ? out.found : "?"));
    } else if (action === "revise") {
      addMsg("user", "Revise my contractor rate to 60 per hour.");
      const out = await callTool("revise", {
        category: "preference",
        name: "my contractor rate is 40 per hour",
        new_value: "60 per hour",
        reason: "renotiated",
      });
      addMsg("bot", renderStructured(out), "revise");
    } else if (action === "blast") {
      addMsg("user", "What is the blast radius of my contractor rate?");
      const out = await callTool("blast", {
        category: "preference",
        name: "my contractor rate is 40 per hour",
      });
      addMsg("bot", renderStructured(out), "blast");
    }
  } catch (err) {
    addMsg("bot", "Error: " + err.message, "failed");
  } finally {
    chips.forEach((c) => (c.disabled = false));
  }
}

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => runAction(chip.dataset.action));
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  addMsg("user", question);
  try {
    if (!sessionId) {
      await connect();
      setStatus(true);
    }
    const out = await callTool("ask", { question });
    addMsg("bot", out.answer || out.text || "(empty)", "ask");
  } catch (err) {
    addMsg("bot", "Error: " + err.message, "failed");
  }
});

// Warm up the connection on load.
connect()
  .then(() => setStatus(true))
  .catch(() => setStatus(false));
