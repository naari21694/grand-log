"""Grand Log dashboard: a clean tile view of everything you have saved.

A tiny stdlib web server, no extra dependencies. It serves a single-page tile grid plus a
small JSON API over the store. It works in any phone browser, and as a Telegram Mini App
when opened from the bot's /dashboard button.

    python -m pipeline.web        # then open http://localhost:8080
For a Telegram Mini App, expose it over HTTPS (a tunnel) and set WEBAPP_URL in .env.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import config, store
from .routing import NAMES

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Grand Log</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
  :root { color-scheme: light dark; --bg:#0f1115; --card:#171a21; --fg:#e8eaed; --muted:#9aa0aa; --line:#262a33; --accent:#26d0ce; }
  * { box-sizing:border-box; }
  body { margin:0; font:15px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; background:var(--bg); color:var(--fg); }
  header { position:sticky; top:0; background:var(--bg); padding:16px 16px 8px; border-bottom:1px solid var(--line); }
  h1 { margin:0 0 10px; font-size:20px; font-weight:700; }
  input { width:100%; padding:10px 12px; border:1px solid var(--line); border-radius:10px; background:var(--card); color:var(--fg); font-size:15px; }
  .chips { display:flex; gap:8px; margin-top:10px; overflow-x:auto; }
  .chip { padding:6px 12px; border:1px solid var(--line); border-radius:999px; background:var(--card); color:var(--muted); white-space:nowrap; cursor:pointer; font-size:13px; }
  .chip.on { color:var(--bg); background:var(--accent); border-color:var(--accent); }
  main { padding:14px 16px 40px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:12px; }
  .tile { background:var(--card); border:1px solid var(--line); border-radius:14px; overflow:hidden; cursor:pointer; display:flex; flex-direction:column; }
  .tile:active { transform:scale(.98); }
  .thumb { aspect-ratio:1; width:100%; object-fit:cover; background:#1f2330; display:grid; place-items:center; font-size:30px; }
  .body { padding:9px 10px 11px; }
  .title { font-weight:600; font-size:14px; line-height:1.25; max-height:2.5em; overflow:hidden; }
  .meta { color:var(--muted); font-size:12px; margin-top:4px; }
  .empty { color:var(--muted); text-align:center; padding:60px 20px; }
</style>
</head>
<body>
<header>
  <h1>&#127988; Grand Log</h1>
  <input id="q" placeholder="Search everything you saved" autocomplete="off">
  <div class="chips" id="chips"></div>
</header>
<main><div class="grid" id="grid"></div><div class="empty" id="empty" hidden>Nothing here yet. Share a reel to your bot.</div></main>
<script>
const tg = window.Telegram && window.Telegram.WebApp;
if (tg) {
  tg.ready(); tg.expand();
  const p = tg.themeParams || {}, s = document.documentElement.style;
  if (p.bg_color) s.setProperty('--bg', p.bg_color);
  if (p.secondary_bg_color) s.setProperty('--card', p.secondary_bg_color);
  if (p.text_color) s.setProperty('--fg', p.text_color);
  if (p.hint_color) s.setProperty('--muted', p.hint_color);
  if (p.button_color) s.setProperty('--accent', p.button_color);
}
const EMOJI = {recipe:"\\u{1F373}", place:"\\u{1F5FE}", home:"\\u{1F3E0}", saved:"\\u{1F4CC}"};
const TOKEN = new URLSearchParams(location.search).get("token") || "";
const api = p => p + (p.includes("?") ? "&" : "?") + "token=" + encodeURIComponent(TOKEN);
let filter = "all", items = [];
const grid = document.getElementById("grid"), empty = document.getElementById("empty");
function open(url){ if(!url) return; if(tg && tg.openLink) tg.openLink(url); else window.open(url, "_blank"); }
function esc(s){ const d=document.createElement("div"); d.textContent = s==null ? "" : s; return d.innerHTML; }
function render(){
  const list = items.filter(i => filter==="all" || i.bucket===filter);
  grid.innerHTML = ""; empty.hidden = list.length > 0;
  for(const i of list){
    const tile = document.createElement("div");
    tile.className = "tile"; tile.onclick = () => open(i.link);
    const thumb = i.has_thumb ? `<img class="thumb" src="${api('/thumb?id='+i.id)}" alt="">`
                              : `<div class="thumb">${EMOJI[i.bucket]||"\\u{1F4CC}"}</div>`;
    tile.innerHTML = thumb + `<div class="body"><div class="title">${esc(i.title||"Saved")}</div>`
      + `<div class="meta">${EMOJI[i.bucket]||""} ${esc(i.crew)}${i.summary?(" \\u00B7 "+esc(i.summary)):""}</div></div>`;
    grid.appendChild(tile);
  }
}
function chips(){
  const c = document.getElementById("chips"); c.innerHTML = "";
  for(const [k,label] of [["all","All"],["recipe","\\u{1F373} Baratie"],["place","\\u{1F5FE} Log Pose"],["home","\\u{1F3E0} Going Merry"],["saved","\\u{1F4CC} Saved"]]){
    const b=document.createElement("div"); b.className="chip"+(k===filter?" on":"");
    b.textContent=label; b.onclick=()=>{ filter=k; chips(); render(); }; c.appendChild(b);
  }
}
async function load(q=""){ const r = await fetch(api("/api/items"+(q?("?q="+encodeURIComponent(q)):""))); items = await r.json(); render(); }
let timer; document.getElementById("q").addEventListener("input", e=>{ clearTimeout(timer); timer=setTimeout(()=>load(e.target.value.trim()),250); });
chips(); load();
</script>
</body>
</html>
"""


def _items_payload(q: str = "") -> list[dict]:
    rows = store.search(q, limit=200) if q else store.recent(200)
    return [{"id": row["id"], "bucket": row["bucket"], "crew": NAMES.get(row["bucket"], row["bucket"]),
             "title": row["title"], "summary": row["summary"], "link": row["link"],
             "has_thumb": bool(row["thumb"])} for row in rows]


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if config.DASHBOARD_TOKEN:
            token = parse_qs(parsed.query).get("token", [""])[0]
            if token != config.DASHBOARD_TOKEN:
                self._send(401, b"unauthorized", "text/plain")
                return
        if parsed.path == "/":
            self._send(200, _PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif parsed.path == "/api/items":
            q = parse_qs(parsed.query).get("q", [""])[0]
            self._send(200, json.dumps(_items_payload(q)).encode("utf-8"), "application/json")
        elif parsed.path == "/thumb":
            self._thumb(parse_qs(parsed.query).get("id", [""])[0])
        else:
            self._send(404, b"not found", "text/plain")

    def _thumb(self, item_id: str) -> None:
        try:
            item = store.get(int(item_id))
        except ValueError:
            item = None
        path = (item or {}).get("thumb") or ""
        if path and os.path.exists(path):
            with open(path, "rb") as fh:
                self._send(200, fh.read(), "image/jpeg")
        else:
            self._send(404, b"", "image/jpeg")

    def log_message(self, *args) -> None:  # keep the console quiet
        pass


def main() -> None:
    store.init_db()
    server = ThreadingHTTPServer((config.DASHBOARD_HOST, config.DASHBOARD_PORT), _Handler)
    print(f"Grand Log dashboard on http://{config.DASHBOARD_HOST}:{config.DASHBOARD_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
