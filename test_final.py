import subprocess, urllib.request, json, time, sys

PORT = 8509
proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "app.py",
     "--server.headless", "true", "--server.port", str(PORT),
     "--browser.gatherUsageStats", "false"],
    cwd="/workspace",
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)

time.sleep(10)

try:
    # 测试 /api/health
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=3)
        body = resp.read().decode()
        print(f"GET /api/health: status={resp.status}")
        print(f"  body: {body[:200]}")
    except Exception as e:
        print(f"GET /api/health: {type(e).__name__}: {str(e)[:100]}")

    # 测试 POST /api/send-email
    try:
        payload = json.dumps({
            "email_to": "jeziyou@qq.com",
            "filename": "test_wsgi_mount.pdf",
            "project_name": "WSGI Mount测试",
            "file_content": "",
            "file_size": 0
        }).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/api/send-email",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=10)
        body = resp.read().decode()
        print(f"POST /api/send-email: status={resp.status}")
        print(f"  body: {body[:300]}")
    except Exception as e:
        print(f"POST /api/send-email: {type(e).__name__}: {str(e)[:100]}")

    # 测试 CORS 预检
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/api/send-email",
            method="OPTIONS"
        )
        resp = urllib.request.urlopen(req, timeout=3)
        print(f"OPTIONS /api/send-email: status={resp.status}")
        print(f"  CORS headers: {[h for h in resp.headers.items() if 'access-control' in h[0].lower()]}")
    except Exception as e:
        print(f"OPTIONS /api/send-email: {type(e).__name__}: {str(e)[:100]}")

finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except:
        proc.kill()
