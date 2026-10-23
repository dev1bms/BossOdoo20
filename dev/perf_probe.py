"""Time from opening a page to an interactive Odoo view, in headless Chrome against the local test Odoo (dev/test.sh
serve). Each URL is opened N times with the onboarding tour of the admin user on, then off.

    python dev/perf_probe.py <runs> <url> [<url> ...]

Local test database only (http://localhost:8069, test admin account). Standard library only.
"""
import json
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, "dev")
from shot import BASE, CDP, CHROME, PORT  # noqa: E402

READY = ".o_form_view .o_form_sheet, .o_list_view .o_list_table, .o_kanban_view .o_kanban_record"


def measure(cdp, url):
    """Navigation start -> first interactive view, in ms (performance.now() of the page at that moment)."""
    cdp.call("Page.navigate", url=BASE + url)
    for _ in range(600):
        time.sleep(0.05)
        try:
            value = cdp.js(f"return document.querySelector({json.dumps(READY)}) ? Math.round(performance.now()) : null;")
        except RuntimeError:
            continue  # page being replaced
        if value:
            return value
    return None


def set_tour(cdp, enabled):
    return cdp.js(f"""
        localStorage.removeItem('current_tour'); localStorage.removeItem('current_tour.config');
        localStorage.removeItem('current_tour.index');
        const r = await fetch('/web/dataset/call_kw/res.users/switch_tour_enabled', {{method: 'POST',
            headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{jsonrpc: '2.0', method: 'call',
            params: {{model: 'res.users', method: 'switch_tour_enabled', args: [{str(enabled).lower()}], kwargs: {{}}}}}})}});
        return (await r.json()).result;""")


def resumed_tour_state(cdp):
    """Browser state found on boss20 (23/10): the CRM onboarding tour saved at step 2 (click the CRM app of the home
    screen) and resumed on every page."""
    return cdp.js("""localStorage.setItem('current_tour', 'crm_tour');
        localStorage.setItem('current_tour.config', JSON.stringify({stepDelay: 0, mode: 'manual', showPointerDuration: 0,
            debug: false, redirect: false, robot: false, fromDB: true}));
        localStorage.setItem('current_tour.index', '2'); return 'saved';""")


def main(runs, *urls):
    profile = tempfile.mkdtemp(prefix="boss-perf-")
    chrome = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}",
                               "--window-size=1366,768", "about:blank"])
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
        cdp.call("Page.navigate", url=f"{BASE}/web/login")
        for _ in range(60):
            time.sleep(1)
            if cdp.js("return !!document.querySelector('#login');"):
                break
        cdp.js("""const l = document.querySelector('#login'), p = document.querySelector('#password');
            l.value = 'admin'; p.value = 'admin'; l.form.submit(); return 1;""")
        for _ in range(240):
            time.sleep(1)
            if cdp.js("return !location.pathname.startsWith('/web/login') && document.readyState === 'complete';"):
                break
        for tour, resumed in ((False, False), (True, False), (True, True), (False, True)):
            print("tour_enabled ->", set_tour(cdp, tour))
            measure(cdp, "/odoo")  # home once: the tour starts like for a user opening Odoo
            for url in urls:
                times = []
                for _ in range(int(runs)):
                    if resumed:
                        resumed_tour_state(cdp)
                    times.append(measure(cdp, url))
                label = ("on " if tour else "off") + (" + saved step 2" if resumed else "")
                print(f"tour={label} {url}: {times} ms")
    finally:
        chrome.terminate()


if __name__ == "__main__":
    main(*sys.argv[1:])
