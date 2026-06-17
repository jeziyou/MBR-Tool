import urllib.request, json, time

time.sleep(1)

for path in ["/", "/api/health"]:
    try:
        resp = urllib.request.urlopen(f"http://localhost:8505{path}", timeout=3)
        print(f"GET {path}: status={resp.status}, body_len={len(resp.read())}")
    except Exception as e:
        print(f"GET {path}: {type(e).__name__}: {str(e)[:80]}")

# POST test
try:
    payload = json.dumps({"email_to": "jeziyou@qq.com", "filename": "test.pdf", "project_name": "Test", "file_size": 100}).encode()
    req = urllib.request.Request(
        "http://localhost:8505/api/send-email",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=5)
    body = resp.read()
    print(f"POST /api/send-email: status={resp.status}")
    print("Body:", body[:200])
except Exception as e:
    print(f"POST /api/send-email: {type(e).__name__}: {str(e)[:100]}")
