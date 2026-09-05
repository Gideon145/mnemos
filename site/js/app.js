// Live playground: talks to the hosted Mnemos MCP endpoint over
// streamable HTTP. Minimal MCP client, no dependencies.

const MCP_URL = "https://mnemos-production-2572.up.railway.app/mcp";

const chat = document.getElementById("pg-chat");
const form = document.getElementById("pg-form");
const input = document.getElementById("pg-text");
const status = document.getElementById("pg-status");

let sessionId = null;
let nextId = 1;
let ready = false;

function setReady(value) {
  ready = value;
  input.disabled = !value;
  form.querySelector("button").disabled = !value;
  document.querySelectorAll(".chip").forEach((c) => (c.disabled = !value));
}

function setStatus(online) {
  status.classList.toggle("online", online);
  status.lastChild.textContent = online ? " live" : " offline";
}

async function postMCP(payload, session, isRetry = false) {
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
  // Hosted sessions expire: reconnect once and replay the call.
  if (res.status === 404 && !isRetry) {
    sessionId = null;
    await initialize();
    return postMCP(payload, sessionId, true);
  }
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

async function initialize() {
  const result = await postMCP(
    {
      jsonrpc: "2.0",
      id: nextId++,
      method: "initialize",
      params: {
        protocolVersion: "2025-06-18",
        capabilities: {},
        clientInfo: { name: "mnemos-playground", version: "1.0" },
      },
    },
    null,
    true
  );
  if (!sessionId) throw new Error("no session returned");
  return result;
}

function connect() {
  return initialize();
}

async function callTool(name, args) {
  if (!sessionId) await initialize();
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
  return wrap;
}

// Typing indicator with pooling dots, like Claude.
let typingEl = null;
function showTyping() {
  if (typingEl) return;
  typingEl = document.createElement("div");
  typingEl.className = "msg bot typing";
  typingEl.innerHTML =
    '<div class="msg-name">MNEMOS</div>' +
    '<div class="msg-body"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>';
  chat.appendChild(typingEl);
  chat.scrollTop = chat.scrollHeight;
}
function hideTyping() {
  if (typingEl) {
    typingEl.remove();
    typingEl = null;
  }
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
      showTyping();
      await callTool("remember", { text: "I like short direct answers", category: "preference" });
      await callTool("remember", { text: "my contractor rate is 40 per hour", category: "preference" });
      hideTyping();
      addMsg("bot", "Stored both facts.\n\npreference: I like short direct answers\npreference: my contractor rate is 40 per hour", "remember x2");
    } else if (action === "ask") {
      addMsg("user", "What do you know about me?");
      showTyping();
      const out = await callTool("ask", { question: "what do you know about me?" });
      hideTyping();
      addMsg("bot", out.answer || out.text || "(empty)", "ask · found: " + (out.found !== undefined ? out.found : "?"));
    } else if (action === "revise") {
      addMsg("user", "Revise my contractor rate to 60 per hour.");
      showTyping();
      const out = await callTool("revise", {
        category: "preference",
        name: "my contractor rate is 40 per hour",
        new_value: "60 per hour",
        reason: "renotiated",
      });
      hideTyping();
      addMsg("bot", renderStructured(out), "revise");
    } else if (action === "blast") {
      addMsg("user", "What is the blast radius of my contractor rate?");
      showTyping();
      const out = await callTool("blast", {
        category: "preference",
        name: "my contractor rate is 40 per hour",
      });
      hideTyping();
      addMsg("bot", renderStructured(out), "blast");
    }
  } catch (err) {
    hideTyping();
    addMsg("bot", "Error: " + err.message, "failed");
  } finally {
    if (ready) chips.forEach((c) => (c.disabled = false));
  }
}

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    if (!ready) return;
    runAction(chip.dataset.action);
  });
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!ready) return;
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  addMsg("user", question);
  showTyping();
  try {
    const res = await fetch(MCP_URL.replace(/\/mcp$/, "/chat"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: question }),
    });
    const data = await res.json();
    hideTyping();
    if (!res.ok) throw new Error(data.error || "chat failed");
    addMsg("bot", data.answer || "(empty)", "mnemos · memory grounded");
  } catch (err) {
    hideTyping();
    addMsg("bot", "Error: " + err.message, "failed");
  }
});

// Copy buttons in the agent panel.
document.querySelectorAll(".copy-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(btn.dataset.copy || "");
      btn.textContent = "Copied";
      btn.classList.add("copied");
      setTimeout(() => {
        btn.textContent = "Copy";
        btn.classList.remove("copied");
      }, 1600);
    } catch {
      btn.textContent = "Blocked";
    }
  });
});

// Scroll reveal.
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("in");
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12 }
);
document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));

// Waitlist stub.
const waitlist = document.getElementById("waitlist-form");
if (waitlist) {
  waitlist.addEventListener("submit", (e) => {
    e.preventDefault();
    const note = document.getElementById("waitlist-note");
    note.textContent = "Noted. Mnemos will not forget you.";
    waitlist.reset();
  });
}

// Warm up the connection on load, then reset so every visitor starts
// with a fresh memory instead of inheriting previous visitors. Input
// stays disabled until the wipe finishes so a fast user cannot race it.
setReady(false);
connect()
  .then(async () => {
    setStatus(true);
    try {
      await callTool("reset", {});
    } catch {
      /* reset is best effort */
    }
    setReady(true);
  })
  .catch(() => {
    setStatus(false);
    setReady(true);
  });
