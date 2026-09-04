"""Render the captured dispatch JSON as a branded terminal image."""
import html
import json
import sys

JSON_SRC = r"C:\Users\vergio\Dev\mnemos\docs\evidence\dispatch.json"
OUT = r"C:\Users\vergio\Dev\mnemos\docs\evidence\dispatch-terminal.html"


def main() -> int:
    data = json.loads(open(JSON_SRC, encoding="utf-8").read())
    content = data.get("content") or "no response"
    model_s = data.get("model") or "?"
    provider_s = data.get("provider") or "?"
    cost_s = data.get("cost") or "?"
    agent_s = data.get("agent_id") or "?"
    rid = data.get("response_id") or "?"

    esc = html.escape

    page = f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ width:960px; height:560px; overflow:hidden; background:#050a14; }}
  body {{ display:flex; align-items:center; justify-content:center; font-family: Consolas, 'JetBrains Mono', monospace; }}
  .term {{ width:900px; border:1px solid #1c3a4a; border-radius:10px; overflow:hidden;
           background:#071120; box-shadow:0 0 40px rgba(0,180,200,.15); }}
  .bar {{ background:#0c1c2c; padding:12px 18px; display:flex; gap:8px; align-items:center;
          border-bottom:1px solid #1c3a4a; }}
  .dot {{ width:12px; height:12px; border-radius:50%; }}
  .r {{ background:#ff5f57; }} .y {{ background:#febc2e; }} .g {{ background:#28c840; }}
  .title {{ color:#5c7a8c; font-size:13px; margin-left:12px; }}
  .body {{ padding:24px 28px; font-size:16px; line-height:1.7; }}
  .p {{ color:#39d3e8; }} .p b {{ color:#7ee8f2; }}
  .resp {{ color:#e8c56a; white-space:pre-wrap; margin-top:16px; }}
  .meta {{ color:#5c7a8c; font-size:13px; margin-top:20px; border-top:1px solid #13283a; padding-top:14px; }}
  .tag {{ color:#39d3e8; }}
</style></head><body>
<div class="term">
  <div class="bar">
    <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
    <span class="title">mnemos — dispatch to virtuals</span>
  </div>
  <div class="body">
    <div class="p">mnemos dispatch <b>"You are Mnemos, an agent with durable memory.<br>
    &nbsp;&nbsp;Confirm in one line that memory, not context, is your source of truth."</b></div>
    <div class="resp">{esc(content)}</div>
    <div class="meta">
      agent <span class="tag">{esc(agent_s)}</span> ·
      model {esc(model_s)} · provider {esc(provider_s)} ·
      billed {esc(str(cost_s))} USD to the agent wallet · response {esc(rid)}
    </div>
  </div>
</div>
</body></html>"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
