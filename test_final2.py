import subprocess, urllib.request, json, time, sys

PORT = 8510
proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "app.py",
     "--server.headless", "true", "--server.port", str(PORT),
     "--browser.gatherUsageStats", "false"],
    cwd="/workspace",
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)

time.sleep(12)

try:
    # Test /api/health
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=3)
        body = resp.read().decode()
        print(f"GET /api/health: status={resp.status}")
        print(f"  body: {body[:200]}")
        print(f"  content-type: {resp.headers.get('content-type')}")
    except Exception as e:
        print(f"GET /api/health: {type(e).__name__}: {str(e)[:100]}")

    # Test POST /api/send-email
    try:
        payload = json.dumps({
            "email_to": "jeziyou@qq.com",
            "filename": "final_wsgi_test.pdf",
            "project_name": "WSGI Mount 最终测试",
            "file_content": "",
            "file_size": 0
        }).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/api/send-email",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=15)
        body = resp.read().decode()
        print(f"\nPOST /api/send-email: status={resp.status}")
        print(f"  body: {body[:300]}")
    except Exception as e:
        print(f"POST /api/send-email: {type(e).__name__}: {str(e)[:100]}")

finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except:
        proc.kill()
