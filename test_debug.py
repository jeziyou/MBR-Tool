import subprocess, urllib.request, json, time, sys

PORT = 8511
proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "app.py",
     "--server.headless", "true", "--server.port", str(PORT),
     "--browser.gatherUsageStats", "false"],
    cwd="/workspace",
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True
)

time.sleep(12)

# Read streamlit output
stdout_lines = []
while proc.poll() is None:
    try:
        line = proc.stdout.readline()
        if line:
            stdout_lines.append(line.strip())
    except:
        break

print("=== Streamlit output (first 30 lines) ===")
for line in stdout_lines[:30]:
    print(line)

# Test /api/health
try:
    resp = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=3)
    body = resp.read().decode()
    is_html = body.strip().startswith('<!')
    print(f"\n/api/health: status={resp.status}, is_html={is_html}")
    if not is_html:
        print(f"  body: {body[:200]}")
except Exception as e:
    print(f"\n/api/health: {type(e).__name__}: {str(e)[:100]}")

proc.terminate()
proc.wait(timeout=5)
