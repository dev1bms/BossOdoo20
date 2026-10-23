"""Desktop screenshots of the local test Odoo for the user guide (headless Chrome + DevTools protocol).

    python dev/shot.py <steps.json> <output_dir>

steps.json: [{"name": "01-crm", "url": "/odoo/crm/1", "wait": 4, "js": "optional async JS body", "clip": [x,y,w,h]}]
Local test database only (http://localhost:8069, test admin account). Standard library only.
SHOT_BASE=<url> SHOT_LOGIN=0 captures another local site (e.g. the guide); a step may set "ready" (CSS selector).
"""
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

BASE = os.environ.get("SHOT_BASE", "http://localhost:8069")
ODOO_READY = ".o_form_view, .o_list_view, .o_kanban_view, .o_setting_container, .o_settings_container"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9339


class CDP:
    def __init__(self, ws_url):
        host_port, path = ws_url[len("ws://"):].split("/", 1)
        host, port = host_port.split(":")
        self.sock = socket.create_connection((host, int(port)))
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET /{path} HTTP/1.1\r\nHost: {host_port}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        response = b""
        while b"\r\n\r\n" not in response:
            response += self.sock.recv(4096)
        self.buffer = response.split(b"\r\n\r\n", 1)[1]
        self.next_id = 0

    def _recv_exact(self, n):
        while len(self.buffer) < n:
            self.buffer += self.sock.recv(1 << 20)
        data, self.buffer = self.buffer[:n], self.buffer[n:]
        return data

    def _recv_frame(self):
        message = b""
        while True:
            b1, b2 = self._recv_exact(2)
            length = b2 & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._recv_exact(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._recv_exact(8))[0]
            message += self._recv_exact(length)
            if b1 & 0x80:
                return message.decode()

    def call(self, method, **params):
        self.next_id += 1
        payload = json.dumps({"id": self.next_id, "method": method, "params": params}).encode()
        header = bytes([0x81])
        mask = os.urandom(4)
        if len(payload) < 126:
            header += bytes([0x80 | len(payload)])
        elif len(payload) < 65536:
            header += bytes([0x80 | 126]) + struct.pack(">H", len(payload))
        else:
            header += bytes([0x80 | 127]) + struct.pack(">Q", len(payload))
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(header + mask + masked)
        while True:
            message = json.loads(self._recv_frame())
            if message.get("id") == self.next_id:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message.get("result", {})

    def js(self, body):
        expression = f"(async () => {{ const sleep = ms => new Promise(r => setTimeout(r, ms)); {body} }})()"
        result = self.call("Runtime.evaluate", expression=expression, awaitPromise=True, returnByValue=True)
        return result.get("result", {}).get("value")


def main(steps_file, out_dir):
    steps = json.loads(Path(steps_file).read_text(encoding="utf-8"))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="boss-shot-")
    chrome = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}",
                               "--window-size=1440,900", "--force-device-scale-factor=1", "--lang=es-ES",
                               "--hide-scrollbars", "about:blank"])
    try:
        for _ in range(50):
            try:
                pages = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list").read())
                page = next(p for p in pages if p["type"] == "page")
                break
            except Exception:  # noqa: BLE001 (Chrome still starting)
                time.sleep(0.3)
        cdp = CDP(page["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Emulation.setDeviceMetricsOverride", width=1440, height=900, deviceScaleFactor=1, mobile=False)
        cdp.call("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
        if os.environ.get("SHOT_LOGIN", "1") == "1":
            cdp.call("Page.navigate", url=f"{BASE}/web/login")
            for _ in range(60):  # the login form may take a while on a freshly started server
                time.sleep(1)
                if cdp.js("return !!document.querySelector('#login');"):
                    break
            print(cdp.js("""const l = document.querySelector('#login'), p = document.querySelector('#password');
                l.value = 'admin'; p.value = 'admin'; l.form.submit(); return 'login';"""))
            for _ in range(240):  # first load after a module update regenerates the assets
                time.sleep(1)
                if cdp.js("return !location.pathname.startsWith('/web/login') && document.readyState === 'complete';"):
                    break
            else:
                sys.exit("login failed")
        for step in steps:
            width, height = step.get("size", (1440, 900))
            try:  # the window itself too: the viewport override alone is sometimes ignored by the layout
                window = cdp.call("Browser.getWindowForTarget")["windowId"]
                cdp.call("Browser.setWindowBounds", windowId=window, bounds={"width": width, "height": height})
            except RuntimeError:
                pass
            cdp.call("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=False)
            cdp.call("Page.navigate", url=BASE + step["url"])
            for _ in range(120):  # wait until the Odoo view is rendered (assets may be rebuilding)
                time.sleep(1)
                if cdp.js(f"return !!document.querySelector({json.dumps(step.get('ready', ODOO_READY))});"):
                    break
            time.sleep(step.get("wait", 5))
            if step.get("js"):
                print(step["name"], "js:", cdp.js(step["js"]))
                time.sleep(step.get("after", 1.5))
            params = {"format": "png"}
            if step.get("clip"):
                x, y, w, h = step["clip"]
                params["clip"] = {"x": x, "y": y, "width": w, "height": h, "scale": 1}
            data = cdp.call("Page.captureScreenshot", **params)["data"]
            (out / f"{step['name']}.png").write_bytes(base64.b64decode(data))
            print("saved", step["name"])
    finally:
        chrome.terminate()


if __name__ == "__main__":
    main(*sys.argv[1:])
