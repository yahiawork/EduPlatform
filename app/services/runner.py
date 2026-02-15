import os, sys, tempfile, subprocess, time
from flask import current_app

def run_python(code_py: str, stdin_text: str = ""):
    start = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        sol = os.path.join(td, "solution.py")
        with open(sol, "w", encoding="utf-8") as f:
            f.write(code_py)

        try:
            p = subprocess.run(
                [sys.executable, sol],
                cwd=td,
                input=stdin_text,
                capture_output=True,
                text=True,
                timeout=current_app.config.get("RUN_TIMEOUT_SEC", 100),
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
            runtime_ms = int((time.perf_counter() - start) * 1000)
            out = (p.stdout or "")
            err = (p.stderr or "")
            return {
                "status": "OK" if p.returncode == 0 else "RUNTIME_ERROR",
                "runtime_ms": runtime_ms,
                "stdout": out,
                "stderr": err,
            }
        except subprocess.TimeoutExpired:
            runtime_ms = int((time.perf_counter() - start) * 1000)
            return {"status": "TIMEOUT", "runtime_ms": runtime_ms, "stdout": "", "stderr": "TIMEOUT"}
        except Exception as e:
            runtime_ms = int((time.perf_counter() - start) * 1000)
            return {"status": "ERROR", "runtime_ms": runtime_ms, "stdout": "", "stderr": str(e)}
