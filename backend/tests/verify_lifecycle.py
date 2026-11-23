import subprocess
import time
import urllib.request
import json
import os
import sys

print("[Test] Starting NEXUS backend server from root directory...")
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8765"],
    cwd=backend_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(2.0)

# Check if process is running
if proc.poll() is not None:
    stdout, stderr = proc.communicate()
    print("Failed to start server:")
    print("STDOUT:", stdout.decode())
    print("STDERR:", stderr.decode())
    sys.exit(1)

try:
    # Use urllib without system proxy
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)

    req = urllib.request.Request("http://127.0.0.1:8765/api/system/health")
    with opener.open(req) as resp:
        data = json.loads(resp.read().decode())
        print("[Test] Health response:", data)
        assert data["status"] == "healthy"
        print("[Test] Health check PASSED.")

    req = urllib.request.Request("http://127.0.0.1:8765/api/resources/metrics")
    with opener.open(req) as resp:
        data = json.loads(resp.read().decode())
        print(f"[Test] Telemetry: CPU={data['cpu_percent']}%, RAM={data['ram_used_gb']}/{data['ram_total_gb']}GB, Status={data['status']}")
        assert "cpu_percent" in data
        print("[Test] Telemetry check PASSED.")

    # Trigger graceful shutdown
    shutdown_req = urllib.request.Request("http://127.0.0.1:8765/api/system/shutdown", data=b"", method="POST")
    with opener.open(shutdown_req) as resp:
        shutdown_res = json.loads(resp.read().decode())
        print("[Test] Shutdown response:", shutdown_res)

    time.sleep(1.5)
    ret = proc.poll()
    print(f"[Test] Process exit status: {ret}")
    if ret is None:
        proc.kill()
        print("[Test] Process had to be terminated manually.")
    else:
        print("[Test] Clean exit verified! No orphaned process.")
except Exception as e:
    proc.kill()
    raise e
