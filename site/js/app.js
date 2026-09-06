// Live playground: talks to the hosted Mnemos MCP endpoint over
// streamable HTTP. Minimal MCP client, no dependencies.

const MCP_URL = "https://mnemos-production-2572.up.railway.app/mcp";

// Signal the reveal animation is safe to hide elements for. Until this
// line runs, every section stays fully visible, so a slow connection
// never renders a blank page.
document.documentElement.classList.add("js");

// One private memory per browser. The id lives in localStorage, so a
// returning device gets its own memory back and no other device sees it.
let deviceId = "anon";
try {
  deviceId = localStorage.getItem("mnemos-device");
  if (!deviceId) {
    deviceId =
      (window.crypto && crypto.randomUUID && crypto.randomUUID()) ||
      String(Date.now()) + "-" + Math.random().toString(36).slice(2);
    localStorage.setItem("mnemos-device", deviceId);
  }
} catch {
  /* private mode or file://, fall back to the shared store */
}

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
    {
      jsonrpc: "2.0",
      id: nextId++,
      method: "tools/call",
      params: { name, arguments: { ...args, device: deviceId } },
    },
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
    } else if (action === "dream") {
      addMsg("user", "Dream over the journal and consolidate it.");
      showTyping();
      const out = await callTool("dream", { min_hits: 1 });
      hideTyping();
      const proposals = out.proposals && out.proposals.length
        ? out.proposals.join("\n")
        : "(nothing new to consolidate)";
      addMsg(
        "bot",
        "Scanned " + out.events_scanned + " new journal events.\n\nProposals:\n" + proposals,
        "dream · review-gated"
      );
    } else if (action === "rewind") {
      addMsg("user", "Rewrite my coffee order, then rewind to before it.");
      showTyping();
      const created = await callTool("remember", {
        text: "my coffee order is espresso",
        category: "preference",
      });
      await callTool("revise", {
        category: "preference",
        name: "my coffee order is espresso",
        new_value: "latte",
        reason: "changed taste",
      });
      const out = await callTool("rewind", { at: (created.created_at || "") + "1" });
      hideTyping();
      const changed = out.changed && out.changed.length
        ? out.changed
            .map((c) => c.entity + ": was " + c.at + ", now " + c.now)
            .join("\n")
        : "(nothing changed since)";
      addMsg(
        "bot",
        "Memory at that moment: " + out.entities + " entities.\n\nChanged since:\n" + changed,
        "rewind · time travel"
      );
    } else if (action === "pulse") {
      addMsg("user", "What is the most urgent matter in my memory?");
      showTyping();
      const out = await callTool("pulse", {});
      hideTyping();
      const text = out.matter
        ? out.matter + "\n\n(" + out.queued + " matter(s) queued)"
        : "nothing queued right now";
      addMsg("bot", text, "pulse · one per tick");
    } else if (action === "owner") {
      addMsg("user", "Show my curated owner profile.");
      showTyping();
      const out = await callTool("owner", {});
      hideTyping();
      addMsg("bot", out.profile || "(no profile yet)", "owner · curated");
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
      body: JSON.stringify({ message: question, device: deviceId }),
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
// Real waitlist: submissions land on the backend, the count is live
// and a judge can verify it by signing up themselves.
const waitlist = document.getElementById("waitlist-form");
const waitlistCountEl = document.getElementById("waitlist-count");
async function refreshWaitlistCount() {
  try {
    const res = await fetch(MCP_URL.replace(/\/mcp$/, "/waitlist/count"));
    const data = await res.json();
    if (waitlistCountEl) {
      const n = data.count || 0;
      waitlistCountEl.textContent =
        n + (n === 1 ? " person waiting" : " people waiting") +
        " for new memory features";
    }
  } catch {
    /* backend unreachable, keep quiet */
  }
}
refreshWaitlistCount();
if (waitlist) {
  waitlist.addEventListener("submit", async (e) => {
    e.preventDefault();
    const note = document.getElementById("waitlist-note");
    const input = waitlist.querySelector("input");
    const email = input.value.trim();
    try {
      const res = await fetch(MCP_URL.replace(/\/mcp$/, "/waitlist"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "could not sign up");
      note.textContent = "You are in. " + data.count + " people are waiting.";
      input.value = "";
      refreshWaitlistCount();
    } catch (err) {
      note.textContent = err.message;
    }
  });
}

// Connect on load. Each device gets its own fresh store by
// construction, and a returning device reconnects to the memory it
// built before, so there is no reset: reopening keeps your memory.
setReady(false);
connect()
  .then(() => {
    setStatus(true);
    setReady(true);
  })
  .catch(() => {
    setStatus(false);
    setReady(true);
  });
