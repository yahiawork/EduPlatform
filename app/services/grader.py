import os, sys, tempfile, subprocess, time
from flask import current_app

def grade_python(code_py: str, tests_py: str):
    if current_app.config.get("USE_DOCKER_GRADER", False):
        return _grade_with_docker(code_py, tests_py)
    return _grade_local(code_py, tests_py)

def _grade_local(code_py: str, tests_py: str):
    # NOTE: Local grading is for dev only (less safe).
    start = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        sol = os.path.join(td, "solution.py")
        tst = os.path.join(td, "test_solution.py")
        with open(sol, "w", encoding="utf-8") as f:
            f.write(code_py)
        with open(tst, "w", encoding="utf-8") as f:
            f.write(tests_py)

        try:
            p = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=td,
                capture_output=True,
                text=True,
                timeout=current_app.config.get("GRADER_TIMEOUT_SEC", 6),
            )
            runtime_ms = int((time.perf_counter() - start) * 1000)
            out = (p.stdout or "") + "\n" + (p.stderr or "")
            return {
                "status": "PASSED" if p.returncode == 0 else "FAILED",
                "runtime_ms": runtime_ms,
                "output": out,
            }
        except subprocess.TimeoutExpired:
            runtime_ms = int((time.perf_counter() - start) * 1000)
            return {"status": "FAILED", "runtime_ms": runtime_ms, "output": "TIMEOUT"}
        except Exception as e:
            runtime_ms = int((time.perf_counter() - start) * 1000)
            return {"status": "ERROR", "runtime_ms": runtime_ms, "output": str(e)}

def _grade_with_docker(code_py: str, tests_py: str):
    start = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, "solution.py"), "w", encoding="utf-8") as f:
            f.write(code_py)
        with open(os.path.join(td, "test_solution.py"), "w", encoding="utf-8") as f:
            f.write(tests_py)

        image = current_app.config.get("DOCKER_IMAGE", "edu_runner:latest")
        timeout = current_app.config.get("GRADER_TIMEOUT_SEC", 6)

        cmd = [
            "docker", "run", "--rm",
            "--network=none",
            "--cpus=1", "--memory=256m",
            "-v", f"{td}:/work",
            "-w", "/work",
            image,
            "pytest", "-q"
        ]

        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            runtime_ms = int((time.perf_counter() - start) * 1000)
            out = (p.stdout or "") + "\n" + (p.stderr or "")
            return {
                "status": "PASSED" if p.returncode == 0 else "FAILED",
                "runtime_ms": runtime_ms,
                "output": out,
            }
        except subprocess.TimeoutExpired:
            runtime_ms = int((time.perf_counter() - start) * 1000)
            return {"status": "FAILED", "runtime_ms": runtime_ms, "output": "TIMEOUT"}
        except Exception as e:
            runtime_ms = int((time.perf_counter() - start) * 1000)
            return {"status": "ERROR", "runtime_ms": runtime_ms, "output": str(e)}
