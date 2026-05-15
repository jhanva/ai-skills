"""CDP browser control — zero-framework Chrome automation via DevTools Protocol.

Auto-discovers a running Chrome with remote debugging enabled, connects via
WebSocket, and exposes helpers for navigation, screenshots, input, tabs, and
DOM evaluation. Designed to be imported by agent-generated scripts.

Dependencies: websockets (auto-installed on first import if missing).
"""
import base64, json, os, subprocess, sys, time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

try:
    import websockets.sync.client as _ws
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "websockets"])
    import websockets.sync.client as _ws


_conn = None
_session = None
_target_id = None
_msg_id = 0
_INTERNAL = ("chrome://", "chrome-untrusted://", "devtools://", "chrome-extension://", "about:")

PROFILES = [
    Path.home() / "Library/Application Support/Google/Chrome",
    Path.home() / "Library/Application Support/Google/Chrome Canary",
    Path.home() / "Library/Application Support/Microsoft Edge",
    Path.home() / "Library/Application Support/BraveSoftware/Brave-Browser",
    Path.home() / ".config/google-chrome",
    Path.home() / ".config/chromium",
    Path.home() / ".config/microsoft-edge",
    Path.home() / "AppData/Local/Google/Chrome/User Data",
    Path.home() / "AppData/Local/Microsoft/Edge/User Data",
]


# --- connection ---

def _discover_ws_url():
    """Find Chrome's WebSocket debugger URL. Checks DevToolsActivePort files, then probes known ports."""
    if url := os.environ.get("CDP_WS_URL"):
        return url
    if cdp_url := os.environ.get("CDP_URL"):
        return json.loads(urlopen(f"{cdp_url.rstrip('/')}/json/version", timeout=5).read())["webSocketDebuggerUrl"]
    for base in PROFILES:
        try:
            lines = (base / "DevToolsActivePort").read_text().splitlines()
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            continue
        port = lines[0].strip() if lines else ""
        ws_path = lines[1].strip() if len(lines) > 1 else ""
        if not port:
            continue
        try:
            data = json.loads(urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2).read())
            return data["webSocketDebuggerUrl"]
        except Exception:
            if ws_path:
                return f"ws://127.0.0.1:{port}{ws_path}"
    for port in (9222, 9223):
        try:
            data = json.loads(urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2).read())
            return data["webSocketDebuggerUrl"]
        except Exception:
            continue
    raise RuntimeError(
        "Chrome not found. Enable remote debugging:\n"
        "  Way 1: open chrome://inspect/#remote-debugging and tick the checkbox\n"
        "  Way 2: launch Chrome with --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug"
    )


def connect(ws_url=None):
    """Connect to Chrome via CDP WebSocket. Auto-discovers if no URL given."""
    global _conn, _session, _target_id, _msg_id
    _msg_id = 0
    url = ws_url or _discover_ws_url()
    _conn = _ws.connect(url, max_size=50 * 1024 * 1024, close_timeout=5)
    targets = cdp("Target.getTargets")["targetInfos"]
    pages = [t for t in targets if t["type"] == "page" and not t.get("url", "").startswith(_INTERNAL)]
    if not pages:
        tid = cdp("Target.createTarget", url="about:blank")["targetId"]
        pages = [{"targetId": tid, "url": "about:blank"}]
    _target_id = pages[0]["targetId"]
    resp = cdp("Target.attachToTarget", targetId=_target_id, flatten=True)
    _session = resp["sessionId"]
    for domain in ("Page", "DOM", "Runtime", "Network"):
        try:
            cdp(f"{domain}.enable")
        except Exception:
            pass
    return _session


def close():
    """Close the CDP connection."""
    global _conn, _session, _target_id
    if _conn:
        try:
            _conn.close()
        except Exception:
            pass
    _conn = _session = _target_id = None


def cdp(method, **params):
    """Send a CDP command and return the result. Raises RuntimeError on CDP errors."""
    global _msg_id
    _msg_id += 1
    msg = {"id": _msg_id, "method": method, "params": params}
    if _session and not method.startswith("Target."):
        msg["sessionId"] = _session
    _conn.send(json.dumps(msg))
    while True:
        resp = json.loads(_conn.recv(timeout=30))
        if resp.get("id") == _msg_id:
            if "error" in resp:
                raise RuntimeError(f"CDP {method}: {resp['error'].get('message', resp['error'])}")
            return resp.get("result", {})


# --- navigation ---

def goto(url):
    """Navigate the current tab to a URL."""
    r = cdp("Page.navigate", url=url)
    return r

def page_info():
    """Return {url, title, w, h, sx, sy, pw, ph} — viewport dimensions + scroll + page size."""
    return json.loads(js(
        "JSON.stringify({url:location.href,title:document.title,"
        "w:innerWidth,h:innerHeight,sx:scrollX,sy:scrollY,"
        "pw:document.documentElement.scrollWidth,"
        "ph:document.documentElement.scrollHeight})"
    ))

def wait_for_load(timeout=15.0):
    """Poll until document.readyState is 'complete'."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if js("document.readyState") == "complete":
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False

def wait_for_element(selector, timeout=10.0, visible=False):
    """Poll until a CSS selector matches an element in the DOM."""
    if visible:
        expr = (
            f"(()=>{{const e=document.querySelector({json.dumps(selector)});"
            f"if(!e)return false;"
            f"if(typeof e.checkVisibility==='function')"
            f"return e.checkVisibility({{checkOpacity:true,checkVisibilityCSS:true}});"
            f"const s=getComputedStyle(e);"
            f"return s.display!=='none'&&s.visibility!=='hidden'&&s.opacity!=='0'}})()"
        )
    else:
        expr = f"!!document.querySelector({json.dumps(selector)})"
    deadline = time.time() + timeout
    while time.time() < deadline:
        if js(expr):
            return True
        time.sleep(0.3)
    return False


# --- input ---

def click_at_xy(x, y, button="left", clicks=1):
    """Click at CSS pixel coordinates. Compositor-level — traverses iframes and shadow DOM."""
    cdp("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button=button, clickCount=clicks)
    cdp("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button=button, clickCount=clicks)

def type_text(text):
    """Insert text at the current focus. Fast but bypasses framework event listeners."""
    cdp("Input.insertText", text=text)

_KEYS = {
    "Enter": (13, "Enter", "\r"), "Tab": (9, "Tab", "\t"),
    "Backspace": (8, "Backspace", ""), "Escape": (27, "Escape", ""),
    "Delete": (46, "Delete", ""), " ": (32, "Space", " "),
    "ArrowLeft": (37, "ArrowLeft", ""), "ArrowUp": (38, "ArrowUp", ""),
    "ArrowRight": (39, "ArrowRight", ""), "ArrowDown": (40, "ArrowDown", ""),
    "Home": (36, "Home", ""), "End": (35, "End", ""),
    "PageUp": (33, "PageUp", ""), "PageDown": (34, "PageDown", ""),
}

def press_key(key, modifiers=0):
    """Press a key. Modifiers: 1=Alt, 2=Ctrl, 4=Meta(Cmd), 8=Shift."""
    vk, code, text = _KEYS.get(key, (ord(key[0]) if len(key) == 1 else 0, key, key if len(key) == 1 else ""))
    base = {"key": key, "code": code, "modifiers": modifiers,
            "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk}
    cdp("Input.dispatchKeyEvent", type="keyDown", **base, **({"text": text} if text else {}))
    if text and len(text) == 1:
        cdp("Input.dispatchKeyEvent", type="char", text=text,
            **{k: v for k, v in base.items() if k != "text"})
    cdp("Input.dispatchKeyEvent", type="keyUp", **base)

def fill_input(selector, text, clear_first=True):
    """Fill a framework-managed input (React, Vue, etc.) with real key events."""
    focused = js(
        f"(()=>{{const e=document.querySelector({json.dumps(selector)});"
        f"if(!e)return false;e.focus();return true;}})()"
    )
    if not focused:
        raise RuntimeError(f"fill_input: element not found: {selector!r}")
    if clear_first:
        mods = 4 if sys.platform == "darwin" else 2
        select_all = {"key": "a", "code": "KeyA", "modifiers": mods,
                      "windowsVirtualKeyCode": 65, "nativeVirtualKeyCode": 65}
        cdp("Input.dispatchKeyEvent", type="rawKeyDown", **select_all)
        cdp("Input.dispatchKeyEvent", type="keyUp", **select_all)
        press_key("Backspace")
    for ch in text:
        press_key(ch)
    js(
        f"(()=>{{const e=document.querySelector({json.dumps(selector)});"
        f"if(!e)return;"
        f"e.dispatchEvent(new Event('input',{{bubbles:true}}));"
        f"e.dispatchEvent(new Event('change',{{bubbles:true}}));}})();"
    )

def scroll(x, y, dy=-300, dx=0):
    """Scroll at the given coordinates. Negative dy = scroll down."""
    cdp("Input.dispatchMouseEvent", type="mouseWheel", x=x, y=y, deltaX=dx, deltaY=dy)


# --- visual ---

def screenshot(path="/tmp/cdp_screenshot.png", full=False):
    """Capture the viewport (or full page) as PNG. Returns the file path."""
    r = cdp("Page.captureScreenshot", format="png", captureBeyondViewport=full)
    with open(path, "wb") as f:
        f.write(base64.b64decode(r["data"]))
    return path


# --- tabs ---

def list_tabs(include_internal=False):
    """List open browser tabs as [{targetId, title, url}, ...]."""
    out = []
    for t in cdp("Target.getTargets")["targetInfos"]:
        if t["type"] != "page":
            continue
        url = t.get("url", "")
        if not include_internal and url.startswith(_INTERNAL):
            continue
        out.append({"targetId": t["targetId"], "title": t.get("title", ""), "url": url})
    return out

def current_tab():
    """Return info about the currently attached tab."""
    info = cdp("Target.getTargetInfo", targetId=_target_id)["targetInfo"]
    return {"targetId": info["targetId"], "url": info.get("url", ""), "title": info.get("title", "")}

def switch_tab(target):
    """Switch to a tab by targetId string or dict with targetId key."""
    global _session, _target_id
    target_id = target.get("targetId") if isinstance(target, dict) else target
    cdp("Target.activateTarget", targetId=target_id)
    resp = cdp("Target.attachToTarget", targetId=target_id, flatten=True)
    _session = resp["sessionId"]
    _target_id = target_id
    for domain in ("Page", "DOM", "Runtime", "Network"):
        try:
            cdp(f"{domain}.enable")
        except Exception:
            pass
    return _session

def new_tab(url="about:blank"):
    """Open a new tab and switch to it."""
    tid = cdp("Target.createTarget", url="about:blank")["targetId"]
    switch_tab(tid)
    if url != "about:blank":
        goto(url)
    return tid

def ensure_real_tab():
    """Switch to a real page tab if currently on an internal page."""
    tabs = list_tabs(include_internal=False)
    if not tabs:
        return None
    try:
        cur = current_tab()
        if cur["url"] and not cur["url"].startswith(_INTERNAL):
            return cur
    except Exception:
        pass
    switch_tab(tabs[0]["targetId"])
    return tabs[0]


# --- DOM / JS ---

def js(expression):
    """Evaluate JavaScript in the current tab. Returns the result value."""
    r = cdp("Runtime.evaluate", expression=expression,
            returnByValue=True, awaitPromise=True)
    result = r.get("result", {})
    if r.get("exceptionDetails") or result.get("subtype") == "error":
        desc = result.get("description") or "JS evaluation failed"
        exc = r.get("exceptionDetails", {}).get("exception", {})
        if not result.get("description") and isinstance(exc, dict):
            desc = exc.get("description") or str(exc.get("value", desc))
        raise RuntimeError(f"JS error: {desc}")
    return result.get("value")

def upload_file(selector, filepath):
    """Set files on a <input type=file> via CDP."""
    doc = cdp("DOM.getDocument", depth=-1)
    nid = cdp("DOM.querySelector", nodeId=doc["root"]["nodeId"], selector=selector)["nodeId"]
    if not nid:
        raise RuntimeError(f"upload_file: no element for {selector!r}")
    files = [filepath] if isinstance(filepath, str) else list(filepath)
    cdp("DOM.setFileInputFiles", files=files, nodeId=nid)

def handle_dialog(accept=True):
    """Accept or dismiss a pending JavaScript dialog (alert/confirm/prompt/beforeunload)."""
    cdp("Page.handleJavaScriptDialog", accept=accept)

def wait_for_idle(timeout=10.0, poll=0.5):
    """Wait until no pending network requests (heuristic: check document.readyState + quiet period)."""
    deadline = time.time() + timeout
    quiet_start = None
    while time.time() < deadline:
        try:
            ready = js("document.readyState") == "complete"
            pending = js("performance.getEntriesByType('resource').filter(e=>!e.responseEnd).length") or 0
        except Exception:
            time.sleep(poll)
            continue
        if ready and pending == 0:
            if quiet_start is None:
                quiet_start = time.time()
            elif time.time() - quiet_start >= poll:
                return True
        else:
            quiet_start = None
        time.sleep(0.2)
    return False


# --- convenience ---

def wait(seconds=1.0):
    """Sleep. Use sparingly — prefer wait_for_load() or wait_for_element()."""
    time.sleep(seconds)


if __name__ == "__main__":
    try:
        ws = _discover_ws_url()
        print(f"Chrome found: {ws}")
        connect(ws)
        info = page_info()
        print(f"Connected to: {info.get('title', '(untitled)')} — {info.get('url', '')}")
        close()
        print("Connection test passed.")
    except Exception as e:
        print(f"Connection test failed: {e}", file=sys.stderr)
        sys.exit(1)
