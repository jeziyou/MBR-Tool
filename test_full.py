import subprocess, urllib.request, json, time, sys, os

PORT = 8508
proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "test_inject.py",
     "--server.headless", "true", "--server.port", str(PORT),
     "--browser.gatherUsageStats", "false"],
    cwd="/workspace",
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)

time.sleep(10)

try:
    resp = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=3)
    body = resp.read().decode()
    print(f"GET /api/health: status={resp.status}, body={body[:200]}")
except Exception as e:
    print(f"GET /api/health: {type(e).__name__}: {str(e)[:100]}")

try:
    payload = json.dumps({"email_to": "jeziyou@qq.com", "filename": "t.pdf", "project_name": "Test", "file_size": 100}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/api/send-email", data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, timeout=5)
    print(f"POST /api/send-email: status={resp.status}, body={resp.read().decode()[:200]}")
except Exception as e:
    print(f"POST /api/send-email: {type(e).__name__}: {str(e)[:100]}")
finally:
    proc.terminate()
    proc.wait(timeout=5)
